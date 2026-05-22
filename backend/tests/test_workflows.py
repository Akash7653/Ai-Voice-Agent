"""
Integration tests for appointment workflows
"""
import pytest
from unittest.mock import AsyncMock, patch
from models.models import Appointment, AppointmentStatus, DoctorSchedule
from db.database import get_db


@pytest.mark.asyncio
async def test_full_booking_workflow(test_db):
    """Test complete workflow: check doctors, verify slots, create appointment"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Setup: Create doctor schedules
    doc_schedules = [
        DoctorSchedule(
            doctor_id="doc_001",
            doctor_name="Dr. Smith",
            specialty="Cardiology",
            available_slots={
                "2025-12-20": ["10:00", "10:30", "11:00"],
                "2025-12-21": ["14:00", "14:30", "15:00"],
            },
        ),
        DoctorSchedule(
            doctor_id="doc_002",
            doctor_name="Dr. Johnson",
            specialty="Cardiology",
            available_slots={
                "2025-12-20": ["09:00", "09:30", "10:00"],
            },
        ),
    ]
    
    for doc in doc_schedules:
        test_db.add(doc)
    await test_db.commit()
    
    # Step 1: Get available doctors by specialty
    response = client.get("/api/doctors?specialty=Cardiology")
    assert response.status_code == 200
    doctors = response.json()["data"]
    assert len(doctors) >= 2
    
    # Step 2: Create appointment with first doctor
    payload = {
        "patient_id": "patient_123",
        "doctor_id": "doc_001",
        "doctor_name": "Dr. Smith",
        "specialty": "Cardiology",
        "appointment_date": "2025-12-20",
        "appointment_time": "10:30",
    }
    
    response = client.post("/api/appointments", json=payload)
    assert response.status_code == 200
    appt_data = response.json()
    assert appt_data["success"] is True
    appt_id = appt_data["data"]["id"]
    
    # Step 3: Get patient appointments
    response = client.get("/api/appointments/patient_123")
    assert response.status_code == 200
    appts = response.json()["data"]
    assert len(appts) == 1
    assert appts[0]["id"] == appt_id


@pytest.mark.asyncio
async def test_booking_then_reschedule_workflow(test_db):
    """Test booking, then rescheduling to a different slot"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Setup: Create doctor schedule
    doc_schedule = DoctorSchedule(
        doctor_id="doc_001",
        doctor_name="Dr. Smith",
        specialty="Cardiology",
        available_slots={
            "2025-12-20": ["10:00", "10:30", "11:00"],
            "2025-12-21": ["14:00", "14:30", "15:00"],
        },
    )
    test_db.add(doc_schedule)
    await test_db.commit()
    
    # Step 1: Create initial appointment
    payload = {
        "patient_id": "patient_123",
        "doctor_id": "doc_001",
        "doctor_name": "Dr. Smith",
        "specialty": "Cardiology",
        "appointment_date": "2025-12-20",
        "appointment_time": "10:30",
    }
    
    response = client.post("/api/appointments", json=payload)
    assert response.status_code == 200
    appt_id = response.json()["data"]["id"]
    
    # Step 2: Reschedule to different date/time
    reschedule_payload = {
        "appointment_date": "2025-12-21",
        "appointment_time": "14:30",
    }
    
    response = client.patch(f"/api/appointments/{appt_id}", json=reschedule_payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["status"] == "rescheduled"
    
    # Step 3: Verify updated appointment
    response = client.get("/api/appointments/patient_123")
    assert response.status_code == 200
    appts = response.json()["data"]
    assert appts[0]["appointment_date"] == "2025-12-21"
    assert appts[0]["appointment_time"] == "14:30"


@pytest.mark.asyncio
async def test_booking_conflict_resolution(test_db):
    """Test booking conflict detection and alternative suggestions"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Setup: Create doctor schedule
    doc_schedule = DoctorSchedule(
        doctor_id="doc_001",
        doctor_name="Dr. Smith",
        specialty="Cardiology",
        available_slots={
            "2025-12-20": ["10:00", "10:30", "11:00"],
        },
    )
    test_db.add(doc_schedule)
    
    # Create existing appointment (booked by another patient)
    existing_appt = Appointment(
        patient_id="patient_999",
        doctor_id="doc_001",
        doctor_name="Dr. Smith",
        specialty="Cardiology",
        appointment_date="2025-12-20",
        appointment_time="10:30",
        status=AppointmentStatus.SCHEDULED,
    )
    test_db.add(existing_appt)
    await test_db.commit()
    
    # Try to book same slot
    payload = {
        "patient_id": "patient_123",
        "doctor_id": "doc_001",
        "doctor_name": "Dr. Smith",
        "specialty": "Cardiology",
        "appointment_date": "2025-12-20",
        "appointment_time": "10:30",
    }
    
    response = client.post("/api/appointments", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False  # Should fail due to conflict
    
    # Try alternative slot
    payload["appointment_time"] = "11:00"
    response = client.post("/api/appointments", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_tts_with_booking_confirmation(test_db):
    """Test TTS used to provide booking confirmation"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Setup
    doc_schedule = DoctorSchedule(
        doctor_id="doc_001",
        doctor_name="Dr. Smith",
        specialty="Cardiology",
        available_slots={
            "2025-12-20": ["10:30"],
        },
    )
    test_db.add(doc_schedule)
    await test_db.commit()
    
    # Create appointment
    payload = {
        "patient_id": "patient_123",
        "doctor_id": "doc_001",
        "doctor_name": "Dr. Smith",
        "specialty": "Cardiology",
        "appointment_date": "2025-12-20",
        "appointment_time": "10:30",
    }
    
    response = client.post("/api/appointments", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Generate TTS confirmation message
    tts_payload = {
        "text": "Your appointment has been confirmed for December 20th at 10:30 AM with Dr. Smith.",
        "language": "en",
        "session_id": "session_123",
    }
    
    with patch('main.tts_service.generate_speech', new_callable=AsyncMock) as mock_tts:
        mock_tts.return_value = {
            "success": True,
            "audio": b"confirmation_audio",
        }
        
        response = client.post("/api/tts", json=tts_payload)
        assert response.status_code == 200
        assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_cancel_then_rebook_workflow(test_db):
    """Test cancelling an appointment and then rebooking"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Setup
    doc_schedule = DoctorSchedule(
        doctor_id="doc_001",
        doctor_name="Dr. Smith",
        specialty="Cardiology",
        available_slots={
            "2025-12-20": ["10:00", "10:30", "11:00"],
        },
    )
    test_db.add(doc_schedule)
    await test_db.commit()
    
    # Create appointment
    payload = {
        "patient_id": "patient_123",
        "doctor_id": "doc_001",
        "doctor_name": "Dr. Smith",
        "specialty": "Cardiology",
        "appointment_date": "2025-12-20",
        "appointment_time": "10:30",
    }
    
    response = client.post("/api/appointments", json=payload)
    appt_id = response.json()["data"]["id"]
    
    # Cancel the appointment
    response = client.delete(f"/api/appointments/{appt_id}")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "cancelled"
    
    # Rebook the same slot (should now be available)
    payload["appointment_time"] = "10:30"
    response = client.post("/api/appointments", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
