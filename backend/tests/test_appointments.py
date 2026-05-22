"""
Tests for appointment endpoints
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import Appointment, AppointmentStatus, DoctorSchedule
from db.database import get_db


@pytest.mark.asyncio
async def test_get_appointments_empty(test_db: AsyncSession):
    """Test getting appointments for patient with no appointments"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Override the get_db dependency
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    response = client.get("/api/appointments/patient_123")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []


@pytest.mark.asyncio
async def test_get_appointments_with_data(test_db: AsyncSession):
    """Test getting appointments for patient with existing appointments"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create a test appointment
    appt = Appointment(
        patient_id="patient_123",
        doctor_id="doc_001",
        doctor_name="Dr. Smith",
        specialty="Cardiology",
        appointment_date="2025-12-20",
        appointment_time="10:30",
        status=AppointmentStatus.SCHEDULED,
    )
    test_db.add(appt)
    await test_db.commit()
    
    response = client.get("/api/appointments/patient_123")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 1
    assert data["data"][0]["doctor_name"] == "Dr. Smith"
    assert data["data"][0]["appointment_time"] == "10:30"


@pytest.mark.asyncio
async def test_create_appointment_success(test_db: AsyncSession):
    """Test successful appointment creation"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create a doctor schedule first
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
    
    payload = {
        "patient_id": "patient_123",
        "doctor_id": "doc_001",
        "doctor_name": "Dr. Smith",
        "specialty": "Cardiology",
        "appointment_date": "2025-12-20",
        "appointment_time": "10:30",
        "duration_minutes": 30,
    }
    
    response = client.post("/api/appointments", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "id" in data["data"]


@pytest.mark.asyncio
async def test_create_appointment_missing_fields(test_db: AsyncSession):
    """Test appointment creation with missing fields"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    payload = {
        "patient_id": "patient_123",
        # Missing required fields
    }
    
    response = client.post("/api/appointments", json=payload)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_appointment_conflict(test_db: AsyncSession):
    """Test appointment creation with conflicting slot"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create doctor schedule
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
    
    # Create existing appointment
    existing = Appointment(
        patient_id="patient_999",
        doctor_id="doc_001",
        doctor_name="Dr. Smith",
        specialty="Cardiology",
        appointment_date="2025-12-20",
        appointment_time="10:30",
        status=AppointmentStatus.SCHEDULED,
    )
    test_db.add(existing)
    await test_db.commit()
    
    # Try to book the same slot
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
    assert data["success"] is False
    assert "conflict" in data or "already booked" in data.get("error", "")


@pytest.mark.asyncio
async def test_reschedule_appointment_success(test_db: AsyncSession):
    """Test successful appointment rescheduling"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create doctor schedule
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
    
    # Create appointment
    appt = Appointment(
        patient_id="patient_123",
        doctor_id="doc_001",
        doctor_name="Dr. Smith",
        specialty="Cardiology",
        appointment_date="2025-12-20",
        appointment_time="10:30",
        status=AppointmentStatus.SCHEDULED,
    )
    test_db.add(appt)
    await test_db.commit()
    await test_db.refresh(appt)
    
    # Reschedule to new slot
    payload = {
        "appointment_date": "2025-12-21",
        "appointment_time": "14:30",
    }
    
    response = client.patch(f"/api/appointments/{str(appt.id)}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "rescheduled"


@pytest.mark.asyncio
async def test_cancel_appointment_success(test_db: AsyncSession):
    """Test successful appointment cancellation"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create appointment
    appt = Appointment(
        patient_id="patient_123",
        doctor_id="doc_001",
        doctor_name="Dr. Smith",
        specialty="Cardiology",
        appointment_date="2025-12-20",
        appointment_time="10:30",
        status=AppointmentStatus.SCHEDULED,
    )
    test_db.add(appt)
    await test_db.commit()
    await test_db.refresh(appt)
    
    response = client.delete(f"/api/appointments/{str(appt.id)}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_nonexistent_appointment(test_db: AsyncSession):
    """Test cancelling non-existent appointment"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    response = client.delete("/api/appointments/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
