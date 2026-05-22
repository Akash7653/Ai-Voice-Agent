"""
Database initialization script
Run this on production to set up schema and seed data
"""
import asyncio
import os
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models.models import (
    Base,
    DoctorSchedule,
    PatientMemory,
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5432/voice_agent",
)


async def init_db():
    """Create all tables"""
    print("[DB] Creating tables...")
    engine = create_async_engine(DATABASE_URL, echo=False, connect_args={"statement_cache_size": 0})

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ [DB] Tables created successfully")
    await engine.dispose()


async def seed_doctors():
    """Seed sample doctor data"""
    print("[DB] Seeding doctors...")

    engine = create_async_engine(DATABASE_URL, echo=False, connect_args={"statement_cache_size": 0})
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    sample_doctors = [
        {
            "doctor_id": "doc_cardio_001",
            "doctor_name": "Dr. Rajesh Kumar",
            "specialty": "Cardiology",
            "available_slots": {
                "2025-12-20": ["09:00", "09:30", "10:00", "10:30", "11:00"],
                "2025-12-21": ["14:00", "14:30", "15:00", "15:30"],
                "2025-12-22": ["09:00", "09:30", "10:00"],
            },
        },
        {
            "doctor_id": "doc_ortho_001",
            "doctor_name": "Dr. Priya Singh",
            "specialty": "Orthopedics",
            "available_slots": {
                "2025-12-20": ["10:00", "11:00", "14:00", "15:00"],
                "2025-12-21": ["09:00", "10:00", "10:30"],
                "2025-12-22": ["14:00", "14:30", "15:00", "15:30", "16:00"],
            },
        },
        {
            "doctor_id": "doc_neuro_001",
            "doctor_name": "Dr. Amit Patel",
            "specialty": "Neurology",
            "available_slots": {
                "2025-12-20": ["09:30", "10:30", "11:00", "11:30"],
                "2025-12-21": ["14:30", "15:00", "15:30", "16:00"],
                "2025-12-22": ["10:00", "10:30", "11:00"],
            },
        },
        {
            "doctor_id": "doc_derm_001",
            "doctor_name": "Dr. Neha Sharma",
            "specialty": "Dermatology",
            "available_slots": {
                "2025-12-20": ["11:00", "11:30", "14:00", "14:30"],
                "2025-12-21": ["10:00", "10:30", "11:00", "15:00"],
                "2025-12-22": ["14:00", "14:30", "15:00"],
            },
        },
        {
            "doctor_id": "doc_pedi_001",
            "doctor_name": "Dr. Vikram Desai",
            "specialty": "Pediatrics",
            "available_slots": {
                "2025-12-20": ["09:00", "09:30", "10:00", "10:30"],
                "2025-12-21": ["09:00", "09:30", "14:00", "14:30"],
                "2025-12-22": ["09:00", "10:00", "15:00", "15:30"],
            },
        },
    ]

    async with async_session() as session:
        for doc_data in sample_doctors:
            # Check if exists
            from sqlalchemy import select

            existing = await session.execute(
                select(DoctorSchedule).where(
                    DoctorSchedule.doctor_id == doc_data["doctor_id"]
                )
            )
            if not existing.scalar_one_or_none():
                doc = DoctorSchedule(**doc_data)
                session.add(doc)

        await session.commit()
        print(f"✅ [DB] Seeded {len(sample_doctors)} doctors")

    await engine.dispose()


async def seed_patients():
    """Seed sample patient data"""
    print("[DB] Seeding patients...")

    engine = create_async_engine(DATABASE_URL, echo=False, connect_args={"statement_cache_size": 0})
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    sample_patients = [
        {
            "patient_id": "patient_001",
            "preferred_language": "en",
            "preferred_doctor": None,
            "patient_metadata": {"age": 45, "email": "john@example.com", "phone": "+1234567890"},
        },
        {
            "patient_id": "patient_002",
            "preferred_language": "hi",
            "preferred_doctor": None,
            "patient_metadata": {"age": 38, "email": "priya@example.com", "phone": "+9876543210"},
        },
        {
            "patient_id": "patient_003",
            "preferred_language": "ta",
            "preferred_doctor": None,
            "patient_metadata": {"age": 52, "email": "rajesh@example.com", "phone": "+9123456789"},
        },
    ]

    async with async_session() as session:
        for pat_data in sample_patients:
            from sqlalchemy import select

            existing = await session.execute(
                select(PatientMemory).where(
                    PatientMemory.patient_id == pat_data["patient_id"]
                )
            )
            if not existing.scalar_one_or_none():
                pat = PatientMemory(**pat_data)
                session.add(pat)

        await session.commit()
        print(f"✅ [DB] Seeded {len(sample_patients)} patients")

    await engine.dispose()


async def main():
    """Run all initialization"""
    print(f"\n{'='*60}")
    print("🗄️  DATABASE INITIALIZATION")
    print(f"{'='*60}\n")

    try:
        await init_db()
        await seed_doctors()
        await seed_patients()

        print(f"\n{'='*60}")
        print("✅ DATABASE READY FOR PRODUCTION")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
