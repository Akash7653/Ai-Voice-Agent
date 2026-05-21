"""
Campaign scheduler for outbound reminder calls
"""
import asyncio
from  datetime import datetime, timedelta
import logging
from  apscheduler.schedulers.asyncio import AsyncIOScheduler
from  sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from  sqlalchemy import select

logger = logging.getLogger(__name__)

class CampaignScheduler:
    """Background scheduler for outbound campaigns"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.scheduler = AsyncIOScheduler()
        self.engine = None
        self.SessionLocal = None
    
    async def initialize(self):
        """Initialize scheduler and database connection"""
        from db.database import AsyncSessionLocal
        self.SessionLocal = AsyncSessionLocal
        self.scheduler.start()
        logger.info("Campaign scheduler initialized")
    
    async def start(self):
        """Start campaign scheduler"""
        # Schedule appointment reminders (24 hours before)
        self.scheduler.add_job(
            self.send_appointment_reminders,
            "interval",
            minutes=int(__import__("os").getenv("CAMPAIGN_CHECK_INTERVAL", 300)) // 60,
            id="appointment_reminders"
        )
        
        # Schedule follow-up campaigns
        self.scheduler.add_job(
            self.send_follow_ups,
            "interval",
            hours=24,
            id="follow_ups"
        )
        
        logger.info("Campaign scheduler started")
    
    async def send_appointment_reminders(self):
        """Send appointment reminders"""
        try:
            async with self.SessionLocal() as session:
                from models.models import Appointment, AppointmentStatus, CampaignTask, CampaignStatus
                
                # Find appointments in 24 hours
                tomorrow = datetime.utcnow() + timedelta(hours=24)
                tomorrow_date = tomorrow.strftime("%Y-%m-%d")
                
                result = await session.execute(
                    select(Appointment).where(
                        (Appointment.appointment_date == tomorrow_date) &
                        (Appointment.status == AppointmentStatus.SCHEDULED)
                    )
                )
                
                appointments = result.scalars().all()
                
                for appointment in appointments:
                    # Check if reminder already sent
                    existing = await session.execute(
                        select(CampaignTask).where(
                            (CampaignTask.appointment_id == appointment.id) &
                            (CampaignTask.campaign_type == "reminder") &
                            (CampaignTask.status == CampaignStatus.COMPLETED)
                        )
                    )
                    
                    if not existing.scalar_one_or_none():
                        # Create reminder task
                        task = CampaignTask(
                            patient_id=appointment.patient_id,
                            campaign_type="reminder",
                            appointment_id=appointment.id,
                            scheduled_time=datetime.utcnow(),
                            status=CampaignStatus.SCHEDULED
                        )
                        session.add(task)
                
                await session.commit()
                logger.info(f"Scheduled {len(appointments)} appointment reminders")
        
        except Exception as e:
            logger.error(f"Error sending appointment reminders: {e}")
    
    async def send_follow_ups(self):
        """Send follow-up campaigns"""
        try:
            async with self.SessionLocal() as session:
                from models.models import Appointment, AppointmentStatus, CampaignTask, CampaignStatus
                
                # Find completed appointments from  3 days ago
                three_days_ago = datetime.utcnow() - timedelta(days=3)
                
                result = await session.execute(
                    select(Appointment).where(
                        (Appointment.appointment_date <= three_days_ago.strftime("%Y-%m-%d")) &
                        (Appointment.status == AppointmentStatus.COMPLETED)
                    )
                )
                
                appointments = result.scalars().all()
                
                for appointment in appointments:
                    # Check if follow-up already sent
                    existing = await session.execute(
                        select(CampaignTask).where(
                            (CampaignTask.appointment_id == appointment.id) &
                            (CampaignTask.campaign_type == "follow_up")
                        )
                    )
                    
                    if not existing.scalar_one_or_none():
                        # Create follow-up task
                        task = CampaignTask(
                            patient_id=appointment.patient_id,
                            campaign_type="follow_up",
                            appointment_id=appointment.id,
                            scheduled_time=datetime.utcnow(),
                            status=CampaignStatus.SCHEDULED
                        )
                        session.add(task)
                
                await session.commit()
                logger.info(f"Scheduled {len(appointments)} follow-up campaigns")
        
        except Exception as e:
            logger.error(f"Error sending follow-ups: {e}")
    
    async def shutdown(self):
        """Shutdown scheduler"""
        self.scheduler.shutdown()
        logger.info("Campaign scheduler shut down")
