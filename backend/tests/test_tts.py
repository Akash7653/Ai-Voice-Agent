"""
Tests for TTS endpoint
"""
import pytest
from unittest.mock import AsyncMock, patch
from db.database import get_db


@pytest.mark.asyncio
async def test_tts_endpoint_success(test_db):
    """Test successful TTS synthesis"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    payload = {
        "text": "Appointment booked for tomorrow at 10 AM",
        "language": "en",
        "session_id": "session_123",
    }
    
    # Mock TTS service to return dummy audio
    with patch('main.tts_service.generate_speech', new_callable=AsyncMock) as mock_tts:
        mock_tts.return_value = {
            "success": True,
            "audio": b"dummy_mp3_audio_data",
        }
        
        response = client.post("/api/tts", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "audio" in data
        assert isinstance(data["audio"], str)  # base64 encoded
        assert "duration_ms" in data


@pytest.mark.asyncio
async def test_tts_endpoint_missing_text(test_db):
    """Test TTS endpoint with missing text"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    payload = {
        "language": "en",
    }
    
    response = client.post("/api/tts", json=payload)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_tts_endpoint_different_languages(test_db):
    """Test TTS endpoint with different language codes"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    languages = ["en", "hi", "ta"]
    
    for lang in languages:
        payload = {
            "text": f"Test message in {lang}",
            "language": lang,
        }
        
        with patch('main.tts_service.generate_speech', new_callable=AsyncMock) as mock_tts:
            mock_tts.return_value = {
                "success": True,
                "audio": b"dummy_audio",
            }
            
            response = client.post("/api/tts", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            # Verify TTS service was called with correct language
            mock_tts.assert_called_once()
            call_kwargs = mock_tts.call_args[1]
            assert call_kwargs["language"] == lang


@pytest.mark.asyncio
async def test_tts_endpoint_tts_failure(test_db):
    """Test TTS endpoint when TTS service fails"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    payload = {
        "text": "This will fail",
        "language": "en",
    }
    
    with patch('main.tts_service.generate_speech', new_callable=AsyncMock) as mock_tts:
        mock_tts.return_value = {
            "success": False,
            "error": "TTS service unavailable",
        }
        
        response = client.post("/api/tts", json=payload)
        
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_tts_endpoint_persists_latency(test_db):
    """Test that TTS endpoint persists latency metrics"""
    from main import app
    from fastapi.testclient import TestClient
    from models.models import LatencyMetric
    from sqlalchemy import select
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    payload = {
        "text": "Test message",
        "language": "en",
        "session_id": "session_123",
    }
    
    with patch('main.tts_service.generate_speech', new_callable=AsyncMock) as mock_tts:
        mock_tts.return_value = {
            "success": True,
            "audio": b"dummy_audio",
        }
        
        response = client.post("/api/tts", json=payload)
        
        assert response.status_code == 200
        
        # Check if latency metric was persisted
        result = await test_db.execute(
            select(LatencyMetric).where(LatencyMetric.session_id == "session_123")
        )
        metrics = result.scalars().all()
        
        assert len(metrics) == 1
        assert metrics[0].component == "tts"
        assert metrics[0].duration_ms > 0


@pytest.mark.asyncio
async def test_tts_endpoint_default_language(test_db):
    """Test TTS endpoint uses default language when not specified"""
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    payload = {
        "text": "Test without language",
    }
    
    with patch('main.tts_service.generate_speech', new_callable=AsyncMock) as mock_tts:
        mock_tts.return_value = {
            "success": True,
            "audio": b"dummy_audio",
        }
        
        response = client.post("/api/tts", json=payload)
        
        assert response.status_code == 200
        
        # Verify default language was used
        call_kwargs = mock_tts.call_args[1]
        assert call_kwargs["language"] == "en"
