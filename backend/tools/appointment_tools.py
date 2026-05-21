"""
Appointment Management Tools
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import select
import json
from dataclasses import dataclass

@dataclass
class ToolResult:
    """Result from tool execution"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AppointmentTools:
    """Tools for appointment management"""
    
    def __init__(self, db_session):
        self.db_session = db_session
    
    async def check_availability(
        self,
        doctor_name: Optional[str] = None,
        specialty: Optional[str] = None,
        date: Optional[str] = None,
        language: str = "en"
    ) -> ToolResult:
        """
        Check doctor availability
        Returns available slots
        """
        frommodels.models import DoctorSchedule
        
        try:
            # Query for available doctors
            query = select(DoctorSchedule)
            
            if doctor_name:
                query = query.where(DoctorSchedule.doctor_name.ilike(f"%{doctor_name}%"))
            
            if specialty:
                query = query.where(DoctorSchedule.specialty.ilike(f"%{specialty}%"))
            
            result = await self.db_session.execute(query)
            doctors = result.scalars().all()
            
            if not doctors:
                message = self._get_localized_message("no_doctors_found", language)
                return ToolResult(success=False, message=message)
            
            # Format availability
            availability = []
            for doctor in doctors:
                availability.append({
                    "doctor_name": doctor.doctor_name,
                    "doctor_id": doctor.doctor_id,
                    "specialty": doctor.specialty,
                    "available_slots": doctor.available_slots,
                    "working_hours": f"{doctor.working_hours_start}-{doctor.working_hours_end}"
                })
            
            message = self._get_localized_message("availability_found", language, count=len(doctors))
            return ToolResult(
                success=True,
                message=message,
                data={"doctors": availability}
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                message="Error checking availability",
                error=str(e)
            )
    
    async def book_appointment(
        self,
        patient_id: str,
        doctor_name: str,
        doctor_id: Optional[str] = None,
        specialty: str = "",
        appointment_date: str = "",
        appointment_time: str = "",
        language: str = "en"
    ) -> ToolResult:
        """
        Book an appointment
        """
        frommodels.models import Appointment, DoctorSchedule, AppointmentStatus
        
        try:
            # Validate appointment details
            if not all([doctor_name, appointment_date, appointment_time]):
                message = self._get_localized_message("missing_details", language)
                return ToolResult(success=False, message=message)
            
            # Check for conflicts
            result = await self.db_session.execute(
                select(Appointment).where(
                    (Appointment.patient_id == patient_id) &
                    (Appointment.appointment_date == appointment_date) &
                    (Appointment.appointment_time == appointment_time) &
                    (Appointment.status == AppointmentStatus.SCHEDULED)
                )
            )
            
            existing = result.scalar_one_or_none()
            if existing:
                message = self._get_localized_message("conflict_found", language)
                return ToolResult(success=False, message=message)
            
            # Create appointment
            appointment = Appointment(
                patient_id=patient_id,
                doctor_name=doctor_name,
                doctor_id=doctor_id,
                specialty=specialty,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status=AppointmentStatus.SCHEDULED,
                confirmed_at=datetime.utcnow()
            )
            
            self.db_session.add(appointment)
            await self.db_session.commit()
            
            message = self._get_localized_message(
                "appointment_booked",
                language,
                doctor=doctor_name,
                date=appointment_date,
                time=appointment_time
            )
            
            return ToolResult(
                success=True,
                message=message,
                data={
                    "appointment_id": str(appointment.id),
                    "doctor_name": doctor_name,
                    "date": appointment_date,
                    "time": appointment_time
                }
            )
        
        except Exception as e:
            await self.db_session.rollback()
            return ToolResult(
                success=False,
                message="Error booking appointment",
                error=str(e)
            )
    
    async def reschedule_appointment(
        self,
        appointment_id: str,
        new_date: str,
        new_time: str,
        language: str = "en"
    ) -> ToolResult:
        """
        Reschedule an existing appointment
        """
        frommodels.models import Appointment, AppointmentStatus
        import uuid
        
        try:
            result = await self.db_session.execute(
                select(Appointment).where(Appointment.id == uuid.UUID(appointment_id))
            )
            appointment = result.scalar_one_or_none()
            
            if not appointment:
                message = self._get_localized_message("appointment_not_found", language)
                return ToolResult(success=False, message=message)
            
            # Check for conflicts with new time
            result = await self.db_session.execute(
                select(Appointment).where(
                    (Appointment.patient_id == appointment.patient_id) &
                    (Appointment.appointment_date == new_date) &
                    (Appointment.appointment_time == new_time) &
                    (Appointment.status == AppointmentStatus.SCHEDULED) &
                    (Appointment.id != uuid.UUID(appointment_id))
                )
            )
            
            if result.scalar_one_or_none():
                message = self._get_localized_message("new_slot_conflict", language)
                return ToolResult(success=False, message=message)
            
            # Update appointment
            old_date = appointment.appointment_date
            old_time = appointment.appointment_time
            
            appointment.appointment_date = new_date
            appointment.appointment_time = new_time
            appointment.status = AppointmentStatus.RESCHEDULED
            
            await self.db_session.commit()
            
            message = self._get_localized_message(
                "appointment_rescheduled",
                language,
                old_date=old_date,
                old_time=old_time,
                new_date=new_date,
                new_time=new_time
            )
            
            return ToolResult(
                success=True,
                message=message,
                data={
                    "appointment_id": appointment_id,
                    "new_date": new_date,
                    "new_time": new_time
                }
            )
        
        except Exception as e:
            await self.db_session.rollback()
            return ToolResult(
                success=False,
                message="Error rescheduling appointment",
                error=str(e)
            )
    
    async def cancel_appointment(
        self,
        appointment_id: str,
        language: str = "en"
    ) -> ToolResult:
        """
        Cancel an appointment
        """
        frommodels.models import Appointment, AppointmentStatus
        import uuid
        
        try:
            result = await self.db_session.execute(
                select(Appointment).where(Appointment.id == uuid.UUID(appointment_id))
            )
            appointment = result.scalar_one_or_none()
            
            if not appointment:
                message = self._get_localized_message("appointment_not_found", language)
                return ToolResult(success=False, message=message)
            
            appointment.status = AppointmentStatus.CANCELLED
            await self.db_session.commit()
            
            message = self._get_localized_message(
                "appointment_cancelled",
                language,
                doctor=appointment.doctor_name,
                date=appointment.appointment_date
            )
            
            return ToolResult(
                success=True,
                message=message,
                data={"appointment_id": appointment_id}
            )
        
        except Exception as e:
            await self.db_session.rollback()
            return ToolResult(
                success=False,
                message="Error cancelling appointment",
                error=str(e)
            )
    
    def _get_localized_message(
        self,
        key: str,
        language: str = "en",
        **kwargs
    ) -> str:
        """Get localized message"""
        messages = {
            "en": {
                "no_doctors_found": "No doctors found matching your criteria.",
                "availability_found": f"Found {{count}} doctor(s) with availability.",
                "missing_details": "Please provide doctor name, date, and time for booking.",
                "conflict_found": "You already have an appointment at this time.",
                "appointment_not_found": "Appointment not found.",
                "appointment_booked": "Great! Your appointment with {{doctor}} is booked for {{date}} at {{time}}.",
                "appointment_rescheduled": "Your appointment has been rescheduled from {{old_date}} {{old_time}} to {{new_date}} {{new_time}}.",
                "appointment_cancelled": "Your appointment with {{doctor}} on {{date}} has been cancelled.",
                "new_slot_conflict": "The new slot is not available. Please choose another time.",
            },
            "hi": {
                "no_doctors_found": "आपके मानदंड के अनुसार कोई डॉक्टर नहीं मिला।",
                "availability_found": "{{count}} डॉक्टर(्स) मिल गए।",
                "missing_details": "कृपया बुकिंग के लिए डॉक्टर का नाम, तारीख और समय प्रदान करें।",
                "conflict_found": "आपके पास इसी समय पर एक नियुक्ति है।",
                "appointment_not_found": "नियुक्ति नहीं मिली।",
                "appointment_booked": "बढ़िया! {{date}} को {{time}} पर {{doctor}} के साथ आपकी नियुक्ति बुक हो गई है।",
                "appointment_rescheduled": "आपकी नियुक्ति {{old_date}} {{old_time}} से {{new_date}} {{new_time}} पर स्थानांतरित कर दी गई है।",
                "appointment_cancelled": "{{date}} को {{doctor}} के साथ आपकी नियुक्ति रद्द कर दी गई है।",
                "new_slot_conflict": "नई स्लॉट उपलब्ध नहीं है। कृपया दूसरा समय चुनें।",
            },
            "ta": {
                "no_doctors_found": "உங்கள் அளவுகோல்களுக்கு பொருந்தும் மருத்துவர்கள் கிடைக்கவில்லை.",
                "availability_found": "{{count}} மருத்துவர்(கள்) கிடைத்தனர்.",
                "missing_details": "முன்பதிவுக்கு மருத்துவரின் பெயர், தேதி மற்றும் நேரம் வழங்கவும்.",
                "conflict_found": "உங்களுக்கு இந்த நேரத்தில் ஒரு சந்திப்பு ஏற்கனவே உள்ளது.",
                "appointment_not_found": "சந்திப்பு கிடைக்கவில்லை.",
                "appointment_booked": "சிறப்பு! {{date}} இல் {{time}} க்கு {{doctor}} உடன் உங்கள் சந்திப்பு பதிவுசெய்யப்பட்டது.",
                "appointment_rescheduled": "உங்கள் சந்திப்பு {{old_date}} {{old_time}} இலிருந்து {{new_date}} {{new_time}} க்கு மாற்றப்பட்டது.",
                "appointment_cancelled": "{{date}} இல் {{doctor}} உடன் உங்கள் சந்திப்பு ரத்து செய்யப்பட்டது.",
                "new_slot_conflict": "புதிய முயற்சி கிடைக்கவில்லை. மற்றொரு நேரம் தேர்ந்தெடுக்கவும்.",
            }
        }
        
        # Telugu localization
        te_messages = {
            "no_doctors_found": "మీ నిబంధనలకు అనుగుణంగా డాక్టర్లు కనబడలేదు.",
            "availability_found": "{count} డాక్టర్(లు) కనబడినారు.",
            "missing_details": "దయచేసి బుకింగ్ కోసం డాక్టర్ పేరు, తేదీ మరియు సమయాన్ని ఇవ్వండి.",
            "conflict_found": "ఈ సమయంలో మీకు ఇప్పటికే ఒక అపాయింట్‌మెంట్ ఉంది.",
            "appointment_not_found": "అపాయింట్‌మెంట్ కనబడలేదు.",
            "appointment_booked": "బాగా ఉంది! {date} తేదీకి {time} గంటలకు {doctor} తో మీ అపాయింట్‌మెంట్ బుక్ అయింది.",
            "appointment_rescheduled": "మీ అపాయింట్‌మెంట్ {old_date} {old_time} నుండి {new_date} {new_time} కి పునర్నిర్దేశించబడింది.",
            "appointment_cancelled": "{date} న {doctor}తో మీ అపాయింట్‌మెంట్ రద్దు చేయబడింది.",
            "new_slot_conflict": "కొత్త స్లాట్ అందుబాటులో లేదు. దయచేసి వేరే సమయాన్ని ఎంచుకోండి.",
        }

        # Merge Telugu messages into main messages dict if not present
        if "te" not in messages:
            messages["te"] = te_messages
        }
        
        lang_messages = messages.get(language, messages["en"])
        message = lang_messages.get(key, key)
        
        # Format message with kwargs
        for key, value in kwargs.items():
            message = message.replace(f"{{{{{key}}}}}", str(value))
        
        return message
