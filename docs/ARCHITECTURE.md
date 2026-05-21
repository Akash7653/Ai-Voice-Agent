# Architecture Deep Dive

## System Design Principles

This system is built on several core architectural principles:

1. **Modularity**: Each component (STT, LLM, Tools, Memory) is independently replaceable
2. **Async-First**: All I/O operations use async/await for optimal resource utilization
3. **Real Tool Calling**: Actual LLM tool execution, not hardcoded responses
4. **Latency-Optimized**: Sub-450ms target with component-level tracking
5. **Scalable**: Horizontal scaling support via stateless design

## Component Deep Dive

### 1. WebSocket Gateway

**File**: `backend/websocket/voice_handler.py`

Responsibilities:
- Accept WebSocket connections per patient
- Buffer audio chunks
- Coordinate the processing pipeline
- Stream responses back
- Track session state

```
Flow:
1. Patient connects → Create session in Redis
2. Audio chunks received → Buffer in memory
3. End signal → Trigger full pipeline
4. Response → Stream audio back
5. Disconnect → Clean up session
```

**Key Features**:
- Per-patient sessions
- Non-blocking async processing
- Graceful error handling
- Comprehensive logging

### 2. Speech-to-Text Service

**File**: `backend/services/stt_service.py`

Uses OpenAI Whisper API:
- Latency: ~100-150ms
- Handles multiple languages
- Audio buffering and streaming
- Error handling and fallback

```python
# Transcription flow
1. Receive audio bytes
2. Create BytesIO wrapper
3. Call Whisper API
4. Return transcript + timing
```

**Optimization**:
- Batch processing for multiple requests
- Compression of audio data
- Connection reuse

### 3. Language Detection

**File**: `backend/services/language_detection.py`

Strategy:
- Character-set based detection
- Devanagari (Hindi): Unicode 0x0900-0x097F
- Tamil: Unicode 0x0B80-0x0C00
- English: Default for Latin characters
- Confidence scoring

```python
# Detection
if (hindi_chars / total_chars) > 0.3:
    return "hi", confidence
```

Persists language preference in patient memory for future sessions.

### 4. LLM Orchestrator

**File**: `backend/agent/orchestrator/llm_orchestrator.py`

**Core Responsibilities**:
1. Prompt engineering (multilingual)
2. Intent detection
3. Entity extraction
4. Tool selection
5. Response generation

**Reasoning Flow**:
```
User Input
    ↓
System Prompt (language-specific)
    ↓
GPT-4o-mini (JSON output)
    ↓
Parse Response
    ↓
Extract Intent & Entities
    ↓
Select Tool
    ↓
Return Structured Result
```

**JSON Response Format**:
```json
{
  "intent": "book_appointment",
  "confidence": 0.95,
  "entities": {
    "patient_id": "patient_001",
    "doctor_name": "Dr. Kumar",
    "appointment_date": "2024-12-21",
    "appointment_time": "10:00"
  },
  "reasoning": "User clearly stated intent to book appointment",
  "response": "Great! Your appointment with Dr. Kumar is booked..."
}
```

**Fallback Logic**: If LLM is unavailable, uses keyword-based intent detection with lower confidence.

### 5. Tool Calling Layer

**File**: `backend/tools/appointment_tools.py`

Implements real tools that interact with database:

```python
class AppointmentTools:
    async def check_availability()     # Query doctor_schedule
    async def book_appointment()       # Insert into appointments
    async def reschedule_appointment() # Update appointments
    async def cancel_appointment()     # Mark as cancelled
```

Each tool:
- Validates inputs
- Checks for conflicts
- Updates database
- Returns structured result
- Provides localized messages

**Example**: Booking
```python
# Validates:
1. All required fields present
2. No double booking
3. Date is future
4. Doctor exists and has availability

# Actions:
1. Create appointment record
2. Update doctor availability
3. Log to conversation
4. Return confirmation message
```

### 6. Memory System

**Session Memory (Redis)**
```python
Key: session:{session_id}
TTL: 3600 seconds
Value: {
    "session_id": "uuid",
    "patient_id": "patient_001",
    "language": "hi",
    "context": {
        "intent": "booking",
        "doctor": "cardiologist",
        "date": "tomorrow"
    },
    "state": "listening",
    "last_response": "..."
}
```

Benefits:
- Fast access (< 1ms)
- Automatic expiry
- Sessioncontext persistence

**Persistent Memory (PostgreSQL)**
```python
PatientMemory {
    patient_id: unique
    preferred_language: string
    preferred_doctor: string
    interaction_count: int
    last_interaction: timestamp
    conversation_summary: text
}
```

Benefits:
- Persists across sessions
- Enables personalization
- Analytics & insights

**Memory Update Flow**:
```
Incoming Request
    ↓
Fetch Session (Redis) - O(1)
    ↓
Fetch Patient Memory (PostgreSQL) - O(1) indexed
    ↓
Merge: Session + Patient context
    ↓
Pass to LLM Agent
    ↓
Agent Reasoning (considers context)
    ↓
Update Session (Redis)
    ↓
Update Patient Memory (PostgreSQL)
```

### 7. Latency Tracking

**File**: `backend/services/latency_tracker.py`

Tracks per-component timings:
```python
start()  # Begin timing
end()    # Stop and record

Components:
- stt: Speech-to-text
- llm: Language model reasoning
- tools: Tool execution
- tts: Text-to-speech
- total: End-to-end
```

Report:
```json
{
  "total_latency_ms": 350,
  "breakdown": {
    "stt": 120,
    "llm": 150,
    "tools": 45,
    "tts": 35
  }
}
```

Saved to database for analytics and SLA monitoring.

### 8. Text-to-Speech

**File**: `backend/services/stt_service.py` (TTSService class)

Providers:
- **OpenAI TTS**: Primary
- **ElevenLabs**: Alternative (fallback)

Latency: ~100-150ms

Features:
- Multiple voice options
- Multilingual support
- Streaming audio response

### 9. Campaign Scheduler

**File**: `backend/scheduler/campaign_scheduler.py`

Async scheduler for outbound tasks:

```python
# Reminders
- Trigger 24 hours before appointment
- Voice call with confirmation option
- Log interaction

# Follow-ups
- Trigger 3 days after completion
- Gather feedback/suggestions
- Update patient record
```

**Execution**:
```
APScheduler (background jobs)
    ↓
Check scheduled tasks
    ↓
For each due task:
    - Create WebSocket connection
    - Initiate voice call
    - Run agent in reminder mode
    - Log results
    - Mark complete/retry
```

## Data Flow Diagrams

### Booking Appointment Flow

```
Patient: "Book appointment with Dr. Kumar for tomorrow at 10 AM"
    ↓
STT → "book appointment with Dr. Kumar for tomorrow at 10 AM"
    ↓
Language Detection → "en"
    ↓
Session Memory Fetch → {} (empty)
    ↓
Patient Memory Fetch → {preferred_language: "en", interaction_count: 5}
    ↓
Merged Context: {language: "en", history: 5 interactions}
    ↓
LLM Prompt (with context)
    ↓
GPT-4o-mini Output:
{
  "intent": "book_appointment",
  "confidence": 0.98,
  "entities": {
    "doctor_name": "Kumar",
    "appointment_date": "2024-12-21",
    "appointment_time": "10:00"
  }
}
    ↓
Tool Selection: book_appointment()
    ↓
Tool Execution:
- Validate: doctor exists? availability? no conflicts?
- Create appointment record
- Update doctor schedule
- Return success
    ↓
Response Generation:
"Great! Your appointment with Dr. Kumar is booked for December 21 at 10:00 AM."
    ↓
TTS → Audio response
    ↓
Send audio to patient
    ↓
Update Session & Patient Memory
    ↓
Log conversation & metrics
```

### Error Handling Flow

```
Tool Execution Error
    ↓
Catch Exception
    ↓
Log Error with context
    ↓
Generate Error Message (localized)
    ↓
Offer Alternative:
- Try again
- Check availability
- Reschedule different time
    ↓
Send Response to patient
    ↓
Continue conversation
```

## Scalability Considerations

### Stateless Design
- All state in Redis/PostgreSQL
- Multiple backend instances possible
- Load balancer routes to any instance

### Database Optimization
- Connection pooling (AsyncPG: 20 min, 40 max)
- Indexed queries (patient_id, session_id, scheduled_time)
- Query optimization with EXPLAIN ANALYZE

### Caching Strategy
```
Request
    ↓
Check Redis (doctor list cache)
    ↓
Hit: Return cached
    ↓
Miss: Query PostgreSQL
    ↓
Cache result (TTL: 3600s)
    ↓
Return to client
```

### Concurrent Connection Limits
- PostgreSQL: max_connections = 100
- Redis: maxclients = 10000
- Backend instances: scale horizontally

## Security Considerations

### API Security
- CORS enabled for frontend origin
- Rate limiting (planned)
- Input validation (Pydantic models)
- SQL injection protection (parameterized queries)

### Data Privacy
- Encrypted database connections
- Session data TTL (auto-expiry)
- Patient data encrypted at rest (production)
- HIPAA compliance roadmap

### Authentication
- Session-based for now
- JWT tokens (future)
- Multi-factor authentication (future)

## Monitoring & Observability

### Metrics Collected
1. **Latency**: Per component, percentiles (P50, P95, P99)
2. **Availability**: Uptime, error rates
3. **Volume**: Requests/min, active sessions
4. **Quality**: Intent confidence, tool success rates

### Logging
- Structured JSON logging
- Level-based filtering
- Centralized logging (ELK/CloudWatch ready)

### Alerting
- Latency SLA breaches (> 500ms)
- Error rate spikes
- Database connection pool exhaustion
- Redis memory usage

## Future Enhancements

1. **Advanced Memory**
   - Long-term patient history
   - Pattern recognition
   - Recommendation engine

2. **Multi-Provider**
   - Multiple clinic support
   - Provider-specific workflows
   - Revenue sharing

3. **Advanced Analytics**
   - Appointment no-show prediction
   - Optimal slot recommendation
   - Patient satisfaction scoring

4. **Integration**
   - EHR systems (Epic, Cerner)
   - Calendar systems (Google, Outlook)
   - Payment processors

5. **Performance**
   - Edge deployment (CDN)
   - Model optimization (quantization)
   - Caching strategy refinement

---

**Document Version**: 1.0  
**Last Updated**: December 2024
