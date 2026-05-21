# Developer Quick Reference

## Common Commands

### Docker Management
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild containers
docker-compose build

# Access service
docker-compose exec backend bash
docker-compose exec postgres psql -U voice_user -d voice_agent_db
docker-compose exec redis redis-cli
```

### Backend Development
```bash
# Virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Run server
python -m uvicorn main:app --reload

# Database migrations
alembic upgrade head

# Run tests
pytest tests/ -v

# Code quality
black backend/
flake8 backend/
mypy backend/
```

### Frontend Development
```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build production
npm run build

# Run production build
npm start

# Linting
npm run lint

# Type checking
npm run type-check

# Tests
npm test
```

### Database Operations
```bash
# PostgreSQL
docker-compose exec postgres psql -U voice_user -d voice_agent_db

# View tables
\dt

# Run SQL query
\c voice_agent_db
SELECT * FROM appointments;

# Backup database
docker-compose exec postgres pg_dump -U voice_user voice_agent_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U voice_user voice_agent_db < backup.sql
```

## File Locations

### Key Files by Purpose

**Voice Pipeline**
- `backend/websocket/voice_handler.py` - Real-time audio handling
- `backend/services/stt_service.py` - Speech-to-text
- `backend/agent/orchestrator/llm_orchestrator.py` - AI reasoning
- `backend/tools/appointment_tools.py` - Tool execution

**Memory**
- `backend/memory/session_memory.py` - Redis + PostgreSQL
- `backend/models/models.py` - Database models
- `backend/db/database.py` - Database connection

**Frontend**
- `frontend/app/page.tsx` - Main application page
- `frontend/hooks/useVoice.ts` - Voice logic hooks
- `frontend/services/api.ts` - API client
- `frontend/components/index.tsx` - React components

**Configuration**
- `.env` - Environment variables
- `docker-compose.yml` - Service orchestration
- `backend/requirements.txt` - Python dependencies
- `frontend/package.json` - npm dependencies

**Documentation**
- `README.md` - Project overview
- `docs/ARCHITECTURE.md` - System design
- `docs/SETUP.md` - Installation guide
- `docs/API.md` - API reference

## Code Patterns

### Adding a New Tool
```python
# 1. Add method to AppointmentTools class
async def my_tool(self, param: str) -> ToolResult:
    try:
        # Implement tool logic
        return ToolResult(success=True, message="...", data={})
    except Exception as e:
        return ToolResult(success=False, error=str(e))

# 2. Map in llm_orchestrator.py
intent_to_tool = {
    "my_intent": "my_tool"
}

# 3. Execute in voice_handler.py
tool_result = await self.orchestrator.execute_tool(
    tool_name,
    tool_arguments,
    language
)
```

### Adding Language Support
```python
# 1. Update language constants
SUPPORTED_LANGUAGES = {
    "es": "Spanish"  # Add new
}

# 2. Add character detection
ES_CHARS = set(chr(i) for i in range(0x0100, 0x0200))

# 3. Add system prompt
prompts = {
    "es": "Spanish system prompt..."
}

# 4. Add message translations
messages = {
    "es": {
        "appointment_booked": "Tu cita..."
    }
}
```

### WebSocket Message Handling
```python
# Listen for message type
if data["type"] == "audio_chunk":
    # Handle audio
elif data["type"] == "end_audio":
    # Process request
elif data["type"] == "disconnect":
    # Clean up

# Send response
await websocket.send_json({
    "type": "response",
    "text": "...",
    "data": {...}
})
```

## Debugging Tips

### Check Service Status
```bash
# Backend health
curl http://localhost:8000/health

# Database connection
docker-compose exec backend python -c "
from backend.db.database import AsyncSessionLocal
print('Database: OK')
"

# Redis connection
docker-compose exec backend python -c "
import redis
r = redis.from_url('redis://redis:6379')
print('Redis:', r.ping())
"
```

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend

# Follow logs (tail)
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Database Debugging
```sql
-- Check active connections
SELECT * FROM pg_stat_activity;

-- View table structure
\d appointments

-- Count records
SELECT COUNT(*) FROM appointments;

-- Recent conversations
SELECT * FROM conversation_log ORDER BY created_at DESC LIMIT 10;

-- Latency stats
SELECT component, AVG(duration_ms), MIN(duration_ms), MAX(duration_ms)
FROM latency_metric
GROUP BY component;
```

### WebSocket Testing
```bash
# Using websocat
websocat ws://localhost:8000/ws/voice/patient_001

# Using wscat (npm)
npm install -g wscat
wscat -c ws://localhost:8000/ws/voice/patient_001

# Send test message
{"type": "audio_chunk", "audio": "base64data"}
{"type": "end_audio"}
```

## Performance Profiling

### Latency Measurement
```python
from backend.services.latency_tracker import LatencyTracker

tracker = LatencyTracker(session_id)
tracker.start("component_name")
# ... do work ...
latency_ms = tracker.end("component_name")

print(tracker.get_report())
```

### Database Query Profiling
```sql
-- Enable query logging
SET log_statement = 'all';

-- Analyze query
EXPLAIN ANALYZE
SELECT * FROM appointments WHERE patient_id = 'patient_001';

-- Slow query log
SET log_min_duration_statement = 100;  -- Log queries > 100ms
```

### Memory Usage
```bash
# Python memory
docker-compose exec backend python -c "
import tracemalloc
tracemalloc.start()
# ... run code ...
current, peak = tracemalloc.get_traced_memory()
print(f'Memory: {peak / 10**6:.1f} MB')
"

# Redis memory
docker-compose exec redis redis-cli INFO memory

# PostgreSQL memory
docker-compose exec postgres ps aux | grep postgres
```

## Environment Variables Quick Reference

```bash
# Essential
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://voice_user:pass@localhost/voice_agent_db
REDIS_URL=redis://localhost:6379

# Tuning
SESSION_TTL=3600                    # Session timeout (seconds)
LOG_LEVEL=INFO                      # DEBUG, INFO, WARNING, ERROR
OPENAI_MODEL=gpt-4o-mini           # LLM model choice
CORS_ORIGINS=http://localhost:3000  # Frontend origin

# Feature flags
ENABLE_LATENCY_TRACKING=True
ENABLE_CAMPAIGN_SCHEDULER=True
```

## Testing Checklist

Before deploying to production:

- [ ] All Docker services start successfully
- [ ] Backend health check passes
- [ ] Frontend loads without errors
- [ ] WebSocket connection establishes
- [ ] Audio capture works (check browser microphone)
- [ ] STT transcription accurate
- [ ] LLM reasoning correct
- [ ] Tools execute successfully
- [ ] TTS audio plays
- [ ] Database saves conversation logs
- [ ] Redis caching works
- [ ] Latency metrics recorded
- [ ] Error handling works
- [ ] Language detection accurate
- [ ] Appointment CRUD operations
- [ ] Campaign scheduler runs

## Useful Resources

- **OpenAI API Docs**: https://platform.openai.com/docs/guides/gpt
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Next.js Docs**: https://nextjs.org/docs
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Redis Docs**: https://redis.io/docs/

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| WebSocket connection refused | Backend not running | `docker-compose up -d` |
| Database connection error | PostgreSQL not initialized | Wait 30s for init, check logs |
| Audio not working | Microphone permission | Browser popup - allow access |
| High latency | Slow LLM/STT | Check API rate limits, network |
| Missing appointments | Database not persisting | Check PostgreSQL connection |
| Language not detected | Insufficient text | Minimum 10 characters |
| Memory leak | Unclosed connections | Restart service |

---

**Last Updated**: December 2024
