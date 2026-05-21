# Real-Time Multilingual Voice AI Agent - Architecture Diagram

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER (Browser)                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   ┌──────────────────────────────────────────────────────────────────────┐       │
│   │                    Next.js 15 Frontend (React)                       │       │
│   │                                                                       │       │
│   │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │       │
│   │  │   Voice     │  │   WebSocket  │  │  UI Components:          │   │       │
│   │  │   Capture   │  │   Client     │  │  - Waveform Visualizer  │   │       │
│   │  │  (Web Audio │  │              │  │  - Reasoning Panel       │   │       │
│   │  │   API)      │  │              │  │  - Latency Dashboard     │   │       │
│   │  └──────┬──────┘  └──────┬───────┘  │  - Appointment Cards     │   │       │
│   │         │                │          │  - Doctor Directory      │   │       │
│   │         └────────┬───────┘          └──────────────────────────┘   │       │
│   │                  │                                                  │       │
│   └──────────────────┼──────────────────────────────────────────────────┘       │
│                      │ WebSocket (Audio Frames)                                  │
└──────────────────────┼──────────────────────────────────────────────────────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
┌────────────────────────────┐   ┌──────────────────────────┐
│   WebSocket Server         │   │   REST API Endpoints     │
│   (FastAPI)                │   │   (FastAPI)              │
│                            │   │                          │
│   /ws/voice/{patient_id}   │   │  GET  /api/appointments  │
│                            │   │  GET  /api/doctors       │
│   Audio Streaming Handler  │   │  POST /api/appointments  │
│                            │   │  PUT  /api/appointments  │
│                            │   │  DELETE /api/appts       │
└────────┬───────────────────┘   └──────────┬───────────────┘
         │                                  │
         └──────────────┬────────────────────┘
                        │
┌───────────────────────┴────────────────────────────────────────────────────────┐
│                      VOICE PROCESSING PIPELINE                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  USER SPEECH INPUT                                                              │
│          │                                                                       │
│          ▼                                                                       │
│  ┌──────────────────┐      ┌─────────────────────┐      ┌─────────────────┐   │
│  │  Speech-to-Text  │ ────→│  Language Detection │ ────→│   LLM Agent     │   │
│  │  (OpenAI         │  Transcript     │ (Devanagari/Tamil) │ (GPT-4o-mini) │   │
│  │   Whisper)       │      │ Detection           │      │  Reasoning      │   │
│  │                  │      │ Confidence: 0-1     │      │  JSON Output    │   │
│  │ <150ms latency   │      └─────────────────────┘      └────────┬────────┘   │
│  └──────────────────┘                                            │              │
│                                                                   │              │
│                                           ┌───────────────────────┘              │
│                                           │                                     │
│                                           ▼                                     │
│                          ┌────────────────────────────────┐                     │
│                          │   Tool Orchestrator            │                     │
│                          │   (Intent Detection)           │                     │
│                          │                                │                     │
│                          │  Parsed JSON:                  │                     │
│                          │  {                             │                     │
│                          │    "intent": "book|cancel",    │                     │
│                          │    "doctor": "cardiologist",   │                     │
│                          │    "date": "tomorrow",         │                     │
│                          │    "confidence": 0.95          │                     │
│                          │  }                             │                     │
│                          └────────┬───────────────────────┘                     │
│                                   │                                             │
│                    ┌──────────────┼──────────────┐                              │
│                    ▼              ▼              ▼                              │
│           ┌──────────────┐ ┌────────────┐ ┌──────────────┐                     │
│           │   Book       │ │  Cancel    │ │  Reschedule  │                     │
│           │  Appointment │ │ Appointment│ │ Appointment  │                     │
│           │              │ │            │ │              │                     │
│           │  Validates:  │ │ Marks as   │ │ Updates slot │                     │
│           │  - Conflict  │ │ cancelled  │ │ - Validates  │                     │
│           │  - Time      │ │ - Logs     │ │ - Detects    │                     │
│           │  - Doctor    │ │   reason   │ │   conflicts  │                     │
│           └──────┬───────┘ └──────┬─────┘ └──────┬───────┘                     │
│                  │                 │              │                             │
│                  └────────┬────────┴──────────────┘                             │
│                           │                                                     │
│                  <50-100ms latency>                                             │
│                           │                                                     │
│                           ▼                                                     │
│                  ┌────────────────────┐                                         │
│                  │  Text Response     │                                         │
│                  │  Generation        │                                         │
│                  │                    │                                         │
│                  │  Multilingual:     │                                         │
│                  │  - en / hi / ta    │                                         │
│                  └────────┬───────────┘                                         │
│                           │                                                     │
│                           ▼                                                     │
│                  ┌────────────────────┐                                         │
│                  │ Text-to-Speech     │                                         │
│                  │ (OpenAI TTS)       │                                         │
│                  │                    │                                         │
│                  │ <150ms latency     │                                         │
│                  └────────┬───────────┘                                         │
│                           │                                                     │
│                           ▼                                                     │
│                  Audio Response                                                 │
│                  (WebSocket → Browser)                                          │
│                                                                                   │
│  ═══════════════════════════════════════════════════════════════════════        │
│  TOTAL PIPELINE LATENCY: < 450ms                                                │
│  - STT: 100-150ms                                                               │
│  - Language Detection: 10-20ms                                                  │
│  - LLM Reasoning: 150-250ms                                                     │
│  - Tool Execution: 50-100ms                                                     │
│  - TTS: 100-150ms                                                               │
│  ═══════════════════════════════════════════════════════════════════════        │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                     │
                    ┌────────────────┴──────────────┐
                    │                               │
┌───────────────────┴──────────────┐   ┌───────────┴──────────────────────────┐
│   DATA & MEMORY LAYER             │   │  BACKGROUND SERVICES                │
├───────────────────────────────────┤   ├──────────────────────────────────────┤
│                                   │   │                                      │
│  ┌─────────────────────────────┐  │   │  ┌─────────────────────────────┐   │
│  │  Session Memory (Redis)      │  │   │  │  Campaign Scheduler         │   │
│  │                              │  │   │  │  (APScheduler)              │   │
│  │  Key: session:{session_id}   │  │   │  │                             │   │
│  │  TTL: 1 hour (configurable)  │  │   │  │  - Send reminders 24h       │   │
│  │                              │  │   │  │    before appointment       │   │
│  │  Stores:                     │  │   │  │  - Send follow-ups 3 days   │   │
│  │  - Current intent            │  │   │  │    after completion         │   │
│  │  - Pending confirmations     │  │   │  │  - Retry logic with         │   │
│  │  - Conversation state        │  │   │  │    exponential backoff      │   │
│  │  - Audio buffer              │  │   │  └─────────────────────────────┘   │
│  │                              │  │   │                                      │
│  └─────────────────────────────┘  │   │  ┌─────────────────────────────┐   │
│                                   │   │  │  Latency Tracking           │   │
│  ┌─────────────────────────────┐  │   │  │  (LatencyMonitor)           │   │
│  │  Persistent Memory (PostgreSQL) │   │  │                             │   │
│  │                              │  │   │  │  Tracks per-component:     │   │
│  │  Tables:                     │  │   │  │  - STT latency              │   │
│  │  - appointments              │  │   │  │  - LLM latency              │   │
│  │  - doctor_schedule           │  │   │  │  - Tool latency             │   │
│  │  - patient_memory            │  │   │  │  - TTS latency              │   │
│  │  - conversation_log          │  │   │  │  - Total latency            │   │
│  │  - campaign_task             │  │   │  │                             │   │
│  │  - latency_metric            │  │   │  │  Exports metrics for        │   │
│  │                              │  │   │  │  /api/latency-stats         │   │
│  │  Stores:                     │  │   │  │                             │   │
│  │  - Patient history           │  │   │  └─────────────────────────────┘   │
│  │  - Language preference       │  │   │                                      │
│  │  - Interaction count         │  │   │                                      │
│  │  - Appointments              │  │   │                                      │
│  │  - Conversation logs         │  │   │                                      │
│  │  - Doctor schedule           │  │   │                                      │
│  │  - Campaign tasks            │  │   │                                      │
│  │                              │  │   │                                      │
│  └─────────────────────────────┘  │   │                                      │
│                                   │   │                                      │
└───────────────────────────────────┘   └──────────────────────────────────────┘
          │                     │
          │                     │
    Redis 7.0              PostgreSQL 16
    (In-memory cache)      (Persistent store)
    Port: 6379             Port: 5432
    Data Expiry: TTL       Replication: Ready
    

┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DEPLOYMENT LAYER (Docker)                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   FastAPI    │  │     Next.js  │  │  PostgreSQL  │  │    Redis     │        │
│  │   Backend    │  │   Frontend   │  │   Database   │  │     Cache    │        │
│  │              │  │              │  │              │  │              │        │
│  │  Port 8000   │  │  Port 3000   │  │ Port 5432    │  │ Port 6379    │        │
│  │              │  │              │  │              │  │              │        │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                                   │
│                      ↓ docker-compose up -d ↓                                   │
│                      All services orchestrated                                   │
│                      Health checks enabled                                       │
│                      Volumes for persistence                                     │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘


                            MULTILINGUAL PIPELINE

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                   │
│  USER LANGUAGE DETECTION                                                        │
│                                                                                   │
│  Hindi Text          Tamil Text          English Text                            │
│  (Devanagari:        (Tamil:             (ASCII:                                 │
│   0x0900-0x097F)     0x0B80-0x0C00)      0x0000-0x007F)                         │
│         │                   │                   │                                │
│         └───────────────────┼───────────────────┘                               │
│                             │                                                    │
│                             ▼                                                    │
│                  Confidence Score: 0-1                                           │
│                  Language Code: en/hi/ta                                         │
│                             │                                                    │
│         ┌───────────────────┼───────────────────┐                               │
│         │                   │                   │                                │
│         ▼                   ▼                   ▼                                │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐                            │
│  │  LLM Prompt │  │  LLM Prompt  │  │  LLM Prompt  │                            │
│  │  (English)  │  │  (Hindi)     │  │  (Tamil)     │                            │
│  │             │  │              │  │              │                            │
│  │ System:     │  │ System:      │  │ System:      │                            │
│  │ "You are a  │  │ "आप एक      │  │ "நீ ஒரு     │                            │
│  │  healthcare │  │  स्वास्थ्य  │  │  சுகाதார   │                            │
│  │  assistant" │  │  सहायक हो"   │  │  உதவி"     │                            │
│  └──────┬──────┘  └────────┬─────┘  └────────┬─────┘                            │
│         │                  │                  │                                  │
│         └──────────────────┼──────────────────┘                                 │
│                            │                                                    │
│                            ▼                                                    │
│              Agent Response (Language-matched)                                   │
│              + Localized Messages                                                │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        REAL-TIME MESSAGE FLOW                                │
└──────────────────────────────────────────────────────────────────────────────┘

INBOUND (User Voice → Response)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Client sends audio chunk via WebSocket
   Message Type: AUDIO_CHUNK
   Payload: {base64_encoded_audio}
   
2. Server receives audio → STT (Whisper)
   Transcripts: "Book appointment tomorrow"
   Latency: 100-150ms
   
3. Language detection module
   Detects: Hindi (Devanagari chars)
   Confidence: 0.92
   
4. LLM Orchestrator processes request
   - Receives transcript + language + history
   - Generates structured JSON:
     {"intent": "book", "doctor": "cardiologist", ...}
   - Confidence: 0.95
   Latency: 150-250ms
   
5. Tool execution (appointment tools)
   - Checks availability
   - Creates booking
   - Returns confirmation
   Latency: 50-100ms
   
6. Response generation + TTS
   Text: "Your appointment is confirmed..."
   Audio: Base64-encoded speech
   Latency: 100-150ms
   
7. Server sends response via WebSocket
   Message Type: AUDIO_RESPONSE + METADATA
   
8. Client plays audio + displays UI
   
   TOTAL: <450ms ✓


OUTBOUND (Campaign Mode)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Campaign scheduler triggers at scheduled time
   - Task: "appointment_reminder"
   - Patient: patient_001
   - Appointment: APT_123
   
2. Backend initiates conversation
   - Generates opening message
   - Converts to speech
   - Establishes WebSocket connection
   
3. Agent speaks: "Hello, this is a reminder about your appointment..."
   
4. User responds via voice
   
5. Agent processes response
   - Intent: reschedule / confirm / reject
   
6. Tool execution based on intent
   - Reschedule: New slot offered
   - Confirm: Logged in database
   - Reject: Marked as declined
   
7. Campaign task updated
   - Status: completed
   - Result: rescheduled / confirmed / declined
   
8. Retry mechanism if needed
   - Max retries: 3
   - Exponential backoff


MEMORY ARCHITECTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Session Memory (Redis) - Fast, temporary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Key: session:SESSION_ID
TTL: 3600s (1 hour)

{
  "session_id": "sess_abc123",
  "patient_id": "pat_001",
  "language": "hi",
  "current_intent": "booking",
  "pending_confirmation": "10:00 AM tomorrow",
  "conversation_state": "awaiting_confirmation",
  "message_history": [...],
  "audio_buffer": [...]
}

Persistent Memory (PostgreSQL) - Permanent, searchable
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
patient_memory table:
{
  "patient_id": "pat_001",
  "language": "hi",
  "preferred_doctor": "Dr. Sharma",
  "total_interactions": 42,
  "last_appointment": "2024-05-15",
  "conversation_summary": "Prefers morning slots, diabetic patient..."
}

appointments table:
{
  "id": "apt_789",
  "patient_id": "pat_001",
  "doctor_id": "doc_456",
  "date": "2024-05-20",
  "time": "10:00",
  "status": "confirmed",
  "created_at": "2024-05-19 14:30:00"
}

conversation_log table:
{
  "session_id": "sess_abc123",
  "transcript": "Book appointment with cardiologist",
  "intent": "booking",
  "tools_used": ["check_availability", "book_appointment"],
  "latency_ms": 342,
  "created_at": "2024-05-19 14:30:05"
}

```

## Scalability Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    HORIZONTAL SCALING SETUP                               │
└────────────────────────────────────────────────────────────────────────────┘

Load Balancer (Nginx)
     │
     ├─── Backend Instance 1 (FastAPI)
     ├─── Backend Instance 2 (FastAPI)
     ├─── Backend Instance 3 (FastAPI)
     └─── Backend Instance N (FastAPI)

Shared Services:
     ├─ PostgreSQL (Master)
     │  └─ Replica 1
     │  └─ Replica 2
     │
     └─ Redis Cluster
        ├─ Node 1 (Master)
        ├─ Node 2 (Slave)
        └─ Node 3 (Slave)

Benefits:
- Stateless backend (all state in Redis/PostgreSQL)
- Horizontal scaling via adding instances
- Session affinity not required
- Database read replicas for scaling queries
- Redis Cluster for HA memory layer

Configuration:
- Pool Size: 20 connections per instance
- Max Overflow: 40 connections
- Connection Timeout: 30s
- Redis TTL: 1 hour (auto-cleanup)

```

## Error Handling & Fallback Flow

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    ERROR RECOVERY MECHANISMS                              │
└────────────────────────────────────────────────────────────────────────────┘

1. LLM Unavailable
   → Fallback to keyword-based intent detection
   → Pattern matching on common phrases
   → Reduced confidence score
   → Log event for monitoring

2. Database Connection Failed
   → Retry with exponential backoff (3 attempts)
   → Use Redis cached data if available
   → Return cached doctor schedule
   → Notify user of degraded service

3. Speech Recognition Failed (Whisper)
   → Request user to repeat
   → Increase audio quality threshold
   → Fallback to phonetic matching
   → Log audio for quality audit

4. Tool Execution Failed
   → Check for scheduling conflicts
   → Offer alternative slots
   → Suggest rescheduling
   → Log for manual review

5. TTS Service Failed (OpenAI)
   → Use text fallback response
   → Log event for monitoring
   → Cache successful responses
   → Retry with backup provider

All errors are logged with:
- Session ID
- Component name
- Error type
- Recovery action taken
- Timestamp
```

## Performance Optimization Strategies

```
┌────────────────────────────────────────────────────────────────────────────┐
│              LATENCY OPTIMIZATION & MONITORING                            │
└────────────────────────────────────────────────────────────────────────────┘

1. Connection Pooling
   - PostgreSQL: 20 pool size, 40 max overflow
   - Redis: Single persistent connection
   - Reuse connections to reduce handshake overhead

2. Caching Strategy
   - Doctor schedule cached in Redis (24h TTL)
   - Patient preferences cached in session
   - LLM system prompts pre-compiled
   - Doctor list cached (updated hourly)

3. Async Operations
   - All I/O operations async (non-blocking)
   - Audio processing in background
   - Campaign scheduling async with APScheduler
   - Database queries async via AsyncPG

4. Component Optimization
   - STT: Pre-configured Whisper client
   - LLM: Optimized token count, shorter prompts
   - TTS: Voice cache, batch processing
   - Database: Indexes on patient_id, appointment_date

5. Network Optimization
   - WebSocket persistent connection (no HTTP overhead)
   - Message compression for large payloads
   - Audio chunk buffering to optimize throughput
   - Batch API calls where possible

6. Monitoring & Metrics
   - Real-time latency tracking per component
   - P50, P95, P99 percentile analysis
   - Dashboard at /api/latency-stats/{patient_id}
   - Logs all component timings for analysis

Target SLA:
- P50 Latency: <250ms
- P95 Latency: <450ms
- P99 Latency: <600ms
- Availability: 99.9%
```

---

This architecture supports:
✅ Real-time voice conversations (<450ms)
✅ Multilingual support (English, Hindi, Tamil)
✅ Persistent & session memory
✅ Tool orchestration with real database operations
✅ Horizontal scalability
✅ Error recovery & fallbacks
✅ Campaign scheduling
✅ Latency tracking & monitoring
✅ Production-grade Docker deployment
