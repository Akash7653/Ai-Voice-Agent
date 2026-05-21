# 🚀 Quick Start & Deployment Guide

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15 (or use Docker)
- Redis 7 (or use Docker)
- OpenAI API Key

## Local Development Setup

### 1. Clone & Install Frontend

```bash
cd frontend
npm install
```

### 2. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000

# backend/.env
OPENAI_API_KEY=sk-xxx
DATABASE_URL=postgresql://postgres:password@localhost:5432/voice_agent
REDIS_URL=redis://localhost:6379
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
LOG_LEVEL=DEBUG
```

### 4. Start Docker Services (PostgreSQL + Redis)

```bash
docker-compose up -d postgres redis
```

### 5. Apply Database Migrations

```bash
cd backend
python -m alembic upgrade head  # or create tables manually
```

### 6. Start Backend

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 7. Start Frontend (in new terminal)

```bash
cd frontend
npm run dev
```

Output:
```
  ▲ Next.js 15.0.0
  - ready started server on 0.0.0.0:3000
```

### 8. Open Browser

```
http://localhost:3001
```

(Frontend runs on 3001, backend on 8000)

---

## 🎯 Testing the Voice Pipeline

### 1. Verify Connection

**Browser Console (F12):**
```javascript
// Should see: [App] Voice service connected
// Status: ready
```

### 2. Test Microphone Access

**Click "🎤 Listen" Button:**
- Check browser permission prompt
- Allow microphone access
- Waveform should animate
- Status changes to "listening"

### 3. Verify Audio Capture

**Speak clearly:**
```
"Hello, I would like to book an appointment"
```

**Check Backend Logs:**
```
[STT] Audio received: 12534 bytes
[STT] Calling Whisper API (language=auto)...
[STT] Transcription: 'Hello, I would like to book an appointment' (1250.5ms)
[WebSocket] Audio buffer size: 12534 bytes
```

### 4. Inspect Debug Audio

```bash
# Check debug audio file
ls -la /tmp/debug_audio.webm
file /tmp/debug_audio.webm
# WebM, Opus codec, 48 kHz

# Play back audio
ffplay /tmp/debug_audio.webm

# Check audio properties
ffprobe /tmp/debug_audio.webm -v quiet
```

### 5. Monitor Real-time Metrics

**Live Panels Show:**
- ✅ Transcript: User speech + AI response
- ✅ Latency: STT/LLM/TTS/WebSocket times
- ✅ Status: Listening → Thinking → Speaking → Listening

---

## 📦 Production Deployment

### Option A: Docker Compose (Recommended for Testing)

```bash
# 1. Build all images
docker-compose build

# 2. Start all services
docker-compose up -d

# 3. Check logs
docker-compose logs -f backend

# 4. Access application
open http://localhost:3001

# 5. Stop services
docker-compose down
```

### Option B: Manual Docker Build

```bash
# Backend
cd backend
docker build -t voice-agent-backend:latest .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-xxx \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  voice-agent-backend:latest

# Frontend
cd frontend
docker build -t voice-agent-frontend:latest .
docker run -p 3001:3000 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 \
  voice-agent-frontend:latest
```

### Option C: Kubernetes Deployment

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voice-agent-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: voice-agent-backend
  template:
    metadata:
      labels:
        app: voice-agent-backend
    spec:
      containers:
      - name: backend
        image: voice-agent-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valuefrom :
            secretKeyRef:
              name: openai-secret
              key: api-key
        - name: DATABASE_URL
          valuefrom :
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valuefrom :
            configMapKeyRef:
              name: redis-config
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

---

## 🔧 Configuration Reference

### Frontend Environment Variables

```bash
NEXT_PUBLIC_API_URL          # Backend WebSocket/API endpoint
NEXT_PUBLIC_LOG_LEVEL        # Browser console log level (DEBUG/INFO/WARN)
```

### Backend Environment Variables

```bash
OPENAI_API_KEY               # OpenAI API key for STT/TTS
DATABASE_URL                 # PostgreSQL connection string
REDIS_URL                    # Redis connection string
CORS_ORIGINS                 # Comma-separated CORS origins
LOG_LEVEL                    # Logging level (DEBUG/INFO/WARNING/ERROR)
SESSION_TTL_HOURS            # Session expiry time (default: 24)
MAX_AUDIO_SIZE_MB            # Max audio file size (default: 10)
WHISPER_MODEL                # Whisper model (default: whisper-1)
AUDIO_DEBUG_SAVE             # Save debug_audio.webm (default: true in dev, false in prod)
```

---

## 📊 Monitoring & Debugging

### 1. Frontend Logs

**Browser DevTools (F12):**
```javascript
// Audio capture logs
[Audio] MIME type: audio/webm;codecs=opus
[Audio] Start: 500ms interval, MIME=audio/webm;codecs=opus
[Audio] Chunk: 12534 bytes

// WebSocket logs
[WebSocket] Connected
[WebSocket] Sent 12534 bytes
[WebSocket] Reconnecting in 1000ms (attempt 1/5)

// Application logs
[App] Voice service connected
[App] Transcript: Hello, I would like to book an appointment
```

### 2. Backend Logs

```bash
# Watch realtime logs
tail -f backend/logs/voice_agent.log

# Filter by component
grep "\[STT\]" backend/logs/voice_agent.log
grep "\[WebSocket\]" backend/logs/voice_agent.log
grep "\[LLM\]" backend/logs/voice_agent.log
```

### 3. Database Debugging

```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d voice_agent

# Check sessions table
SELECT session_id, patient_id, state, created_at from  sessions 
ORDER BY created_at DESC LIMIT 5;

# Check transcriptions table
SELECT user_input, ai_response, latency_ms from  transcriptions 
WHERE patient_id = 'patient_001' 
ORDER BY created_at DESC LIMIT 10;
```

### 4. Redis Debugging

```bash
# Connect to Redis CLI
redis-cli

# Check session data
KEYS "session:*"
GET "session:abc123"

# Monitor real-time commands
MONITOR

# Check Redis memory
INFO memory
```

### 5. Performance Profiling

```bash
# Backend latency analysis
# Check logs for timing breakdown:
# [STT] Transcription complete: ... (latency: 1250.5ms)
# [LLM] Orchestration complete: ... (latency: 127.9ms)
# [TTS] Synthesis complete: ... (latency: 95.2ms)

# Frontend performance
# Open DevTools → Performance tab
# Click Record → Use app → Click Stop
# Review FPS, memory usage, component render times
```

---

## 🐛 Common Issues & Solutions

### Issue: "ERR_INVALID_PROTOCOL" or WebSocket fails

**Cause**: Frontend trying to connect to wrong backend URL

**Solution**:
```bash
# Check .env.local
cat frontend/.env.local
# Should show: NEXT_PUBLIC_API_URL=http://localhost:8000

# Verify backend is running
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Issue: "OpenAI API Error: 401 Unauthorized"

**Cause**: Invalid or missing API key

**Solution**:
```bash
# Verify API key in .env
echo $OPENAI_API_KEY

# Test API key
python -c "from  openai import OpenAI; OpenAI(api_key='$OPENAI_API_KEY').models.list()"

# If error: Update .env and restart backend
```

### Issue: "Database connection failed"

**Cause**: PostgreSQL not running or wrong connection string

**Solution**:
```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"

# If error: Create database first
createdb voice_agent
```

### Issue: "Audio too small (48 bytes)"

**Cause**: Recording captured only silence/noise

**Solution**:
1. Check microphone is unmuted
2. Speak clearly and loudly
3. Check microphone permissions in browser
4. Increase chunk size from  500ms to 1000ms if still issues

### Issue: "Latency > 500ms"

**Cause**: Slow network or OpenAI API overload

**Solution**:
1. Check internet connection speed: `speedtest-cli`
2. Monitor OpenAI status: https://status.openai.com
3. Increase timeouts in config
4. Check database query performance

---

## 🔄 Continuous Integration / Continuous Deployment

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Test Backend
        run: |
          cd backend
          pip install -r requirements.txt
          pytest
      
      - name: Test Frontend
        run: |
          cd frontend
          npm install
          npm run build
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Docker Hub
        run: |
          docker login -u ${{ secrets.DOCKER_USER }} -p ${{ secrets.DOCKER_PASS }}
          docker build -t myrepo/voice-agent-backend:latest ./backend
          docker push myrepo/voice-agent-backend:latest
```

---

## 📈 Scaling Considerations

### Horizontal Scaling (Multiple Instances)

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend-1:
    build: ./backend
    environment:
      WORKER_ID: 1
  
  backend-2:
    build: ./backend
    environment:
      WORKER_ID: 2
  
  backend-3:
    build: ./backend
    environment:
      WORKER_ID: 3
  
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - backend-1
      - backend-2
      - backend-3
```

### Load Balancing with Nginx

```nginx
upstream backend {
    server backend-1:8000;
    server backend-2:8000;
    server backend-3:8000;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 🔐 Security Hardening

### 1. Enable HTTPS

```bash
# Generate self-signed cert (dev)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Or use Let's Encrypt (prod)
certbot certonly --standalone -d yourdomain.com
```

### 2. Configure CORS Properly

```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # NOT "*"
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True,
)
```

### 3. Add Rate Limiting

```python
from  slowapi import Limiter
from  slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.websocket("/ws/voice/{patient_id}")
@limiter.limit("10/minute")
async def websocket_voice_endpoint(websocket: WebSocket, patient_id: str):
    ...
```

### 4. Enable Security Headers

```python
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "www.yourdomain.com"]
)

# Add headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

---

## 📝 Maintenance & Upgrades

### Regular Maintenance Tasks

```bash
# Daily
docker-compose logs backend | tail -100  # Check for errors

# Weekly
psql $DATABASE_URL -c "VACUUM ANALYZE"   # Optimize database

# Monthly
docker system prune -a                    # Clean up old images
docker volume prune                       # Clean up unused volumes

# Quarterly
# Update dependencies
cd frontend && npm update
cd backend && pip install --upgrade -r requirements.txt

# Annually
# Security audit
npm audit
pip-audit
```

### Backup Strategy

```bash
# PostgreSQL backup
pg_dump $DATABASE_URL > backup.sql

# Redis backup
redis-cli --rdb /backup/dump.rdb

# Docker volumes backup
docker run --rm -v voice_agent_pgdata:/data \
  -v /backup:/backup \
  alpine tar czf /backup/pgdata.tar.gz /data

# Schedule with cron
0 2 * * * /path/to/backup.sh  # Daily at 2 AM
```

---

## ✅ Pre-Launch Checklist

- [ ] All environment variables configured
- [ ] Database migrations applied
- [ ] Redis connection verified
- [ ] OPENAI_API_KEY works
- [ ] Frontend builds without errors
- [ ] Backend starts without errors
- [ ] WebSocket connection successful
- [ ] Audio capture works
- [ ] STT transcription accurate
- [ ] Latency <450ms (measured)
- [ ] Error handling tested
- [ ] CORS origins whitelisted
- [ ] SSL/TLS configured
- [ ] Rate limiting enabled
- [ ] Security headers added
- [ ] Logging configured
- [ ] Monitoring enabled
- [ ] Backup strategy tested
- [ ] Documentation complete
- [ ] Team trained on system

---

## 📞 Support Contacts

- **Bug Reports**: Create issue in GitHub
- **OpenAI Support**: https://support.openai.com
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Next.js Docs**: https://nextjs.org/docs

---

**Last Updated**: May 21, 2026  
**Version**: 1.0.0 - Production Ready

