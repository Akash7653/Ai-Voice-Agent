# API Reference

## Overview

The Voice AI Healthcare Agent exposes both WebSocket and REST APIs for voice interactions and appointment management.

## WebSocket API

### Endpoint
```
wss://localhost:8000/ws/voice/{patient_id}
```

### Connection Flow

1. **Connect**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/voice/patient_001');

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  // Handle message
};
```

2. **Session Start Message** (server → client)
```json
{
  "type": "session_start",
  "session_id": "uuid-1234",
  "message": "Voice agent ready. Please speak."
}
```

### Message Types

#### Audio Chunk (client → server)
```json
{
  "type": "audio_chunk",
  "audio": "base64_encoded_audio_data"
}
```

**Description**: Send audio chunks while recording
**Frequency**: Every 100ms during recording
**Audio Format**: Mono, 16000 Hz sample rate

#### End Audio (client → server)
```json
{
  "type": "end_audio"
}
```

**Description**: Signal end of audio input, triggers processing
**Response**: Agent will respond with transcript, reasoning, and response

#### Transcript (server → client)
```json
{
  "type": "transcript",
  "text": "I want to book an appointment",
  "language": "en",
  "confidence": 0.95
}
```

**Description**: User's transcribed speech

#### Reasoning Trace (server → client)
```json
{
  "type": "reasoning_trace",
  "intent": "book_appointment",
  "confidence": 0.95,
  "entities": {
    "doctor_name": "Dr. Kumar",
    "appointment_date": "2024-12-21",
    "appointment_time": "10:00"
  },
  "reasoning": "User explicitly requested booking with specific doctor and time"
}
```

**Description**: AI reasoning and extracted information

#### Response (server → client)
```json
{
  "type": "response",
  "text": "Great! Your appointment with Dr. Kumar is booked for December 21 at 10:00 AM.",
  "language": "en",
  "audio": "base64_encoded_audio_response"
}
```

**Description**: Agent's text response and audio (base64 encoded)

#### Latency Metrics (server → client)
```json
{
  "type": "latency_metrics",
  "total_latency_ms": 350,
  "breakdown": {
    "stt": 120,
    "llm": 150,
    "tools": 45,
    "tts": 35
  }
}
```

**Description**: Performance metrics for the completed request

#### Error (server → client)
```json
{
  "type": "error",
  "message": "Error processing audio"
}
```

**Description**: Error message if something goes wrong

#### Disconnect (client → server)
```json
{
  "type": "disconnect"
}
```

**Description**: Gracefully close connection

## REST API Endpoints

### Health Check

```
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "Voice AI Healthcare Agent",
  "version": "1.0.0"
}
```

### Appointments

#### Get Patient Appointments
```
GET /api/appointments/{patient_id}?status=scheduled
```

**Parameters**:
- `patient_id` (path): Patient identifier
- `status` (query, optional): Filter by status (scheduled, completed, cancelled)

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-1234",
      "doctor_name": "Dr. Kumar",
      "specialty": "Cardiologist",
      "appointment_date": "2024-12-21",
      "appointment_time": "10:00",
      "status": "scheduled",
      "created_at": "2024-12-20T10:00:00Z"
    }
  ]
}
```

**Status Codes**:
- 200: Success
- 404: Patient not found
- 500: Server error

### Doctors

#### Get Doctor List
```
GET /api/doctors?specialty=Cardiologist
```

**Parameters**:
- `specialty` (query, optional): Filter by specialty

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "doc_001",
      "name": "Dr. Rajesh Kumar",
      "specialty": "Cardiologist",
      "working_hours": "09:00-17:00",
      "available_slots": {
        "2024-12-21": ["09:00", "10:00", "14:00"],
        "2024-12-22": ["11:00", "15:00"]
      }
    }
  ]
}
```

### Patient Information

#### Get Patient Info
```
GET /api/patient/{patient_id}
```

**Parameters**:
- `patient_id` (path): Patient identifier

**Response**:
```json
{
  "success": true,
  "data": {
    "patient_id": "patient_001",
    "preferred_language": "hi",
    "preferred_doctor": "Dr. Kumar",
    "interaction_count": 5,
    "last_interaction": "2024-12-20T10:00:00Z",
    "conversation_summary": "Patient frequently books cardiology appointments..."
  }
}
```

#### Update Patient Preferences
```
POST /api/patient/{patient_id}/preferences
Content-Type: application/json

{
  "preferred_language": "hi",
  "preferred_doctor": "Dr. Kumar"
}
```

**Request Body**:
```json
{
  "preferred_language": "en|hi|ta",
  "preferred_doctor": "doctor_name"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Preferences updated"
}
```

### Sessions

#### Get Session Info
```
GET /api/session/{session_id}
```

**Parameters**:
- `session_id` (path): Session identifier

**Response**:
```json
{
  "success": true,
  "data": {
    "session_id": "uuid-1234",
    "patient_id": "patient_001",
    "language": "en",
    "context": {
      "intent": "booking",
      "doctor": "cardiologist"
    },
    "state": "listening",
    "created_at": 1702962000.123
  }
}
```

### Analytics

#### Get Latency Statistics
```
GET /api/latency-stats/{patient_id}?limit=100
```

**Parameters**:
- `patient_id` (path): Patient identifier
- `limit` (query, optional): Number of metrics to retrieve (default: 100)

**Response**:
```json
{
  "success": true,
  "data": {
    "avg_total_latency": 350.5,
    "min_latency": 250,
    "max_latency": 450,
    "metrics_count": 50
  }
}
```

## Error Responses

### WebSocket Errors

```json
{
  "type": "error",
  "message": "Error message"
}
```

Common errors:
- "Could not transcribe audio"
- "Session not found"
- "Error processing request"

### REST API Errors

**400 Bad Request**:
```json
{
  "detail": "Invalid parameters"
}
```

**404 Not Found**:
```json
{
  "detail": "Patient not found"
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Internal server error"
}
```

## Authentication

Currently, authentication is session-based. Identify patients via `patient_id` in WebSocket URI.

### Future Authentication
- JWT tokens
- OAuth 2.0
- API keys
- Multi-factor authentication

## Rate Limiting

Currently not enforced. Planned for production:
- 100 requests/minute per patient
- 1000 concurrent WebSocket connections
- Burst allowance: 50 requests

## CORS

Allowed origins (configurable via `CORS_ORIGINS` env):
- http://localhost:3000 (development)
- https://yourdomain.com (production)

## Pagination

Not currently implemented. Will be added for large result sets.

## Webhooks

Optional outbound webhooks (planned):
- Appointment confirmed
- Appointment reminder
- Campaign completed
- Error occurred

## Code Examples

### JavaScript/TypeScript

```typescript
// Connect to voice agent
const ws = new WebSocket('ws://localhost:8000/ws/voice/patient_001');

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  switch(msg.type) {
    case 'session_start':
      console.log('Connected:', msg.session_id);
      break;
    case 'transcript':
      console.log('You said:', msg.text);
      break;
    case 'reasoning_trace':
      console.log('Intent:', msg.intent);
      break;
    case 'response':
      console.log('Agent:', msg.text);
      playAudio(msg.audio);
      break;
    case 'latency_metrics':
      console.log('Latency:', msg.total_latency_ms, 'ms');
      break;
  }
};

// Send audio
async function sendAudio(audioData) {
  ws.send(JSON.stringify({
    type: 'audio_chunk',
    audio: base64Encode(audioData)
  }));
}

// End input
function endInput() {
  ws.send(JSON.stringify({ type: 'end_audio' }));
}
```

### Python

```python
import asyncio
import json
import websockets

async def voice_interaction():
    async with websockets.connect('ws://localhost:8000/ws/voice/patient_001') as ws:
        # Receive session start
        msg = json.loads(await ws.recv())
        print(f"Session: {msg['session_id']}")
        
        # Send audio
        with open('audio.wav', 'rb') as f:
            audio = f.read()
        
        await ws.send(json.dumps({
            'type': 'audio_chunk',
            'audio': base64.b64encode(audio).decode()
        }))
        
        # End audio
        await ws.send(json.dumps({'type': 'end_audio'}))
        
        # Receive responses
        while True:
            msg = json.loads(await ws.recv())
            if msg['type'] == 'response':
                print(f"Agent: {msg['text']}")
                break

asyncio.run(voice_interaction())
```

### cURL

```bash
# Get doctors
curl -X GET http://localhost:8000/api/doctors \
  -H "Content-Type: application/json"

# Get appointments
curl -X GET http://localhost:8000/api/appointments/patient_001 \
  -H "Content-Type: application/json"

# Update preferences
curl -X POST http://localhost:8000/api/patient/patient_001/preferences \
  -H "Content-Type: application/json" \
  -d '{
    "preferred_language": "hi",
    "preferred_doctor": "Dr. Kumar"
  }'

# WebSocket (using websocat)
websocat ws://localhost:8000/ws/voice/patient_001
```

## Versioning

Current API Version: 1.0.0

Future versions will maintain backward compatibility where possible.

## SLA & Performance

**Target Metrics**:
- Response Latency: < 450ms (P95)
- Availability: 99.9%
- Error Rate: < 0.1%

**Monitoring**: Available via `/api/latency-stats` endpoint

---

**API Version**: 1.0.0  
**Last Updated**: December 2024
