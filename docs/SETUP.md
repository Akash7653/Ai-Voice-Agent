# Installation & Setup Guide

## Prerequisites Checklist

- [ ] Docker & Docker Compose installed
- [ ] OpenAI API key obtained
- [ ] Git installed
- [ ] Python 3.11+ (for local development)
- [ ] Node.js 20+ (for frontend development)
- [ ] PostgreSQL 16+ (for local development)
- [ ] Redis 7+ (for local development)

## Quick Start (Docker)

### 1. Clone Repository
```bash
cd Voice-Agent
```

### 2. Configure Environment
```bash
# Copy example env file
cp .env.example .env

# Edit with your values
nano .env
# Required:
# OPENAI_API_KEY=sk-...
```

### 3. Start Services
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 4. Verify Installation
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
open http://localhost:3000

# Check API docs
open http://localhost:8000/docs
```

### 5. Initialize Database
```bash
# Database auto-initializes via init.sql in docker-compose
# Verify tables created:
docker-compose exec postgres psql -U voice_user -d voice_agent_db -c "\dt"
```

## Local Development Setup

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://voice_user:voice_password@localhost:5432/voice_agent_db
export REDIS_URL=redis://localhost:6379
export OPENAI_API_KEY=sk-...

# Start PostgreSQL (if not using Docker)
# Make sure PostgreSQL is running and database exists

# Start Redis (if not using Docker)
# redis-server

# Initialize database
python -c "fromdb.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Run server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install
# or
yarn install

# Create .env.local
cp .env.example .env.local

# Configure API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" >> .env.local

# Start development server
npm run dev
# or
yarn dev

# Open browser
open http://localhost:3000
```

## Database Setup

### Using Docker (Recommended)

```bash
# PostgreSQL starts automatically with docker-compose
# Schema created via docker-entrypoint-initdb.d/init.sql

# Connect to database
docker-compose exec postgres psql -U voice_user -d voice_agent_db

# View tables
\dt

# Exit
\q
```

### Manual PostgreSQL Setup

```bash
# Create database
createdb -U postgres voice_agent_db

# Create user
psql -U postgres -c "CREATE USER voice_user WITH PASSWORD 'voice_password';"

# Grant privileges
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE voice_agent_db TO voice_user;"

# Run schema
psql -U voice_user -d voice_agent_db -f backend/db/init.sql

# Verify
psql -U voice_user -d voice_agent_db -c "\dt"
```

## Redis Setup

### Using Docker

```bash
# Redis starts automatically with docker-compose

# Connect to Redis
docker-compose exec redis redis-cli

# Test connection
PING
# Response: PONG

# Check memory
INFO memory
```

### Manual Redis Setup

```bash
# Install Redis
# macOS: brew install redis
# Ubuntu: sudo apt-get install redis-server

# Start Redis
redis-server

# Test in another terminal
redis-cli PING
# Response: PONG
```

## Configuration

### Environment Variables

**Backend (.env)**
```env
# Required
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://voice_user:password@localhost:5432/voice_agent_db
REDIS_URL=redis://localhost:6379

# Optional (defaults provided)
ENV=development
DEBUG=True
LOG_LEVEL=INFO
SESSION_TTL=3600
CORS_ORIGINS=http://localhost:3000
```

**Frontend (.env.local)**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Database Configuration

Edit `backend/db/database.py`:
```python
# Customize connection pool
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=20,           # Min connections
    max_overflow=40,        # Max overflow
    pool_pre_ping=True,     # Test before use
)
```

### Redis Configuration

Edit `backend/memory/session_memory.py`:
```python
def __init__(self, redis_url: str = None):
    self.ttl = int(os.getenv("SESSION_TTL", 3600))  # Customize TTL
```

## Verification

### Backend Health Check

```bash
# Health endpoint
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "service": "Voice AI Healthcare Agent",
  "version": "1.0.0"
}
```

### Database Connection

```bash
# Test from backend container
docker-compose exec backend python -c "
fromdb.database import AsyncSessionLocal
print('Database connection: OK')
"
```

### Redis Connection

```bash
# Test from backend container
docker-compose exec backend python -c "
import redis
r = redis.from_url('redis://redis:6379')
print('Ping:', r.ping())
"
```

### API Endpoints

```bash
# Get doctors
curl http://localhost:8000/api/doctors | python -m json.tool

# Get patient appointments
curl http://localhost:8000/api/appointments/patient_001 | python -m json.tool

# Get patient info
curl http://localhost:8000/api/patient/patient_001 | python -m json.tool
```

### WebSocket Connection

```bash
# Using websocat or wscat
wscat -c ws://localhost:8000/ws/voice/patient_001

# Send message
{"type": "audio_chunk", "audio": "base64_encoded_audio"}
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill process
kill -9 <PID>

# Or use different ports
docker-compose down
# Edit docker-compose.yml ports
docker-compose up -d
```

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Verify credentials in .env
grep DATABASE_URL .env

# Test connection
docker-compose exec postgres psql -U voice_user -d voice_agent_db -c "SELECT 1"
```

### Redis Connection Error

```bash
# Check if Redis is running
docker-compose ps redis

# Check logs
docker-compose logs redis

# Test connection
docker-compose exec redis redis-cli PING
```

### WebSocket Connection Issues

```bash
# Check backend logs for WebSocket errors
docker-compose logs backend | grep -i websocket

# Verify CORS settings
grep CORS_ORIGINS .env

# Test endpoint
curl -i http://localhost:8000/health

# Check firewall
# Ensure port 8000 is not blocked
```

### Audio Processing Issues

```bash
# Check microphone access in browser
# Navigate to http://localhost:3000
# Browser should prompt for microphone access

# In browser console (F12)
navigator.mediaDevices.getUserMedia({audio: true})
  .then(stream => console.log("Microphone access: OK"))
  .catch(e => console.error("Microphone error:", e))
```

### OpenAI API Errors

```bash
# Verify API key
echo $OPENAI_API_KEY

# Test API directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check quota/limits in OpenAI dashboard
```

## Development Workflows

### Adding a New Tool

1. **Create tool in `backend/tools/appointment_tools.py`**
```python
async def my_new_tool(self, param1: str) -> ToolResult:
    # Implementation
    return ToolResult(success=True, message="...", data={})
```

2. **Update LLM prompt to recognize the new tool**
```python
# In backend/agent/orchestrator/llm_orchestrator.py
# Add to system prompt
```

3. **Add tool execution logic**
```python
# In voice_handler.py
elif tool_name == "my_new_tool":
    result = await tools.my_new_tool(**tool_arguments)
```

4. **Test via API/WebSocket**

### Adding a New Language

1. **Add language code to constants**
```python
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "es": "Spanish"  # New
}
```

2. **Update language detection**
```python
# Add character ranges for new language
ES_CHARS = set(chr(i) for i in range(...))
```

3. **Add system prompt**
```python
prompts = {
    "es": "Spanish system prompt..."
}
```

4. **Add message translations**
```python
messages = {
    "es": {
        "appointment_booked": "Tu cita con {{doctor}} ..."
    }
}
```

### Testing Locally

```bash
# Unit tests
cd backend
pytest tests/ -v

# Integration tests
pytest tests/integration/ -v

# Load testing
locust -f locustfile.py --host=http://localhost:8000

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] All environment variables set
- [ ] Database migrations run
- [ ] API keys secured in vault/secrets manager
- [ ] SSL/TLS certificates obtained
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Logging configured
- [ ] Monitoring/alerting set up
- [ ] Backup strategy in place
- [ ] Documentation updated

### Deployment Steps

#### Option 1: Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml voice-agent

# Monitor
docker service logs voice-agent_backend
```

#### Option 2: Kubernetes
```bash
# Create namespace
kubectl create namespace voice-agent

# Create secrets
kubectl create secret generic db-secret \
  --from-literal=password=... \
  -n voice-agent

# Deploy
kubectl apply -f k8s/

# Monitor
kubectl logs -n voice-agent -l app=backend
```

#### Option 3: Railway/Render + Vercel
```bash
# Connect git repository
# Set environment variables in dashboard
# Deploy (auto-deploy on push)
```

### Post-Deployment

```bash
# Verify services
curl https://api.yourdomain.com/health

# Check logs
# Monitor dashboards

# Test critical paths
# Book appointment
# Check availability
# Reschedule/cancel
```

## Maintenance

### Database Backups

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U voice_user voice_agent_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U voice_user voice_agent_db < backup.sql
```

### Log Rotation

```bash
# Configure in /etc/logrotate.d/voice-agent
/var/log/voice-agent/*.log {
    daily
    rotate 7
    compress
    delaycompress
}
```

### Update Dependencies

```bash
# Backend
pip list --outdated
pip install --upgrade -r requirements.txt

# Frontend
npm outdated
npm update
```

---

**Last Updated**: December 2024  
**Version**: 1.0
