# Production Deployment Checklist

## Pre-Deployment Phase

### Code Quality
- [ ] All linting passes (`npm run lint`, `flake8`)
- [ ] Type checking passes (`npm run type-check`, `mypy`)
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] No console errors in browser
- [ ] No server errors in logs
- [ ] Code review completed

### Security
- [ ] OPENAI_API_KEY not in version control
- [ ] Database credentials in secrets manager
- [ ] CORS origins properly configured
- [ ] Input validation enabled (Pydantic)
- [ ] SQL injection prevention verified
- [ ] Rate limiting configured
- [ ] Error messages non-verbose
- [ ] SSL/TLS certificates obtained

### Performance
- [ ] Latency targets met (< 450ms)
- [ ] Database indexes optimized
- [ ] Connection pooling configured
- [ ] Caching strategy implemented
- [ ] Load testing passed
- [ ] Memory profiling acceptable
- [ ] No N+1 queries

### Infrastructure
- [ ] Docker images built and tested
- [ ] Docker registry configured
- [ ] Kubernetes manifests prepared (if using K8s)
- [ ] Database backups configured
- [ ] Log aggregation setup
- [ ] Monitoring/alerting configured
- [ ] Disaster recovery plan documented

## Deployment Phase

### Environment Setup
- [ ] Production environment variables configured
- [ ] Secrets manager populated
- [ ] Database provisioned
- [ ] Redis cluster configured
- [ ] Load balancer configured
- [ ] DNS records updated
- [ ] SSL/TLS configured

### Application Deployment
- [ ] Docker images pushed to registry
- [ ] Kubernetes/Swarm manifests applied
- [ ] Health checks passing
- [ ] Metrics collection working
- [ ] Logs being aggregated
- [ ] Alerting functional

### Data Migration
- [ ] Database schema migrated
- [ ] Existing data migrated (if applicable)
- [ ] Backups verified
- [ ] Rollback plan documented

## Post-Deployment Phase

### Verification
- [ ] Frontend accessible at domain
- [ ] Backend API responding
- [ ] WebSocket connections stable
- [ ] Database operations working
- [ ] Redis caching functional
- [ ] SSL/TLS certificates valid
- [ ] CORS working correctly

### Monitoring
- [ ] Latency metrics normal
- [ ] Error rate < 0.1%
- [ ] Uptime > 99.9%
- [ ] No memory leaks
- [ ] No database connection pool exhaustion
- [ ] No Redis memory issues

### User Testing
- [ ] Voice recording works
- [ ] Transcription accurate
- [ ] Appointments book successfully
- [ ] Cancellation works
- [ ] Rescheduling works
- [ ] Multilingual support functional
- [ ] Latency dashboard accurate

### Documentation
- [ ] Runbooks created
- [ ] Incident response plan documented
- [ ] Scaling procedures documented
- [ ] Backup/restore procedures tested
- [ ] Change log updated

## Ongoing Operations

### Daily
- [ ] Monitor error rates
- [ ] Check latency metrics
- [ ] Verify service health
- [ ] Review alerts

### Weekly
- [ ] Review performance metrics
- [ ] Check database size growth
- [ ] Verify backup success
- [ ] Review security logs

### Monthly
- [ ] Capacity planning review
- [ ] Security audit
- [ ] Performance optimization review
- [ ] Cost analysis

### Quarterly
- [ ] Disaster recovery drill
- [ ] Security audit (comprehensive)
- [ ] Dependency updates
- [ ] Architecture review

## Troubleshooting Guide

### Service Won't Start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Port in use - change docker-compose.yml
# 2. Database not ready - wait 30s, increase health check timeout
# 3. Memory issues - increase Docker memory limit
# 4. Dependency issues - rebuild images
```

### High Latency

```bash
# Check component latencies
curl http://api.example.com/api/latency-stats/patient_001

# If STT slow:
# - Check OpenAI API status
# - Check network connectivity
# - Review audio quality

# If LLM slow:
# - Check OpenAI API status
# - Consider model selection
# - Add caching

# If database slow:
# - Check query performance (EXPLAIN ANALYZE)
# - Add indexes
# - Review connection pool size

# If TTS slow:
# - Check OpenAI API status
# - Consider alternative provider
```

### Database Issues

```bash
# Connection pool exhausted
# Solution: Increase pool_size in database.py

# Slow queries
# Solution: Add indexes, optimize queries
SELECT * from  pg_stat_statements ORDER BY mean_time DESC;

# Storage issues
# Solution: Archive old logs, increase disk
du -sh /var/lib/postgresql/data

# Replication lag
# Solution: Increase replication resources
```

### Memory Leaks

```bash
# Python memory
docker-compose exec backend python -m tracemalloc

# Container memory
docker stats

# Redis memory
docker-compose exec redis redis-cli INFO memory

# Solutions:
# - Implement connection pooling
# - Close resources properly
# - Restart services periodically
```

## Rollback Procedure

```bash
# If critical issue found:

# 1. Identify good version
git log --oneline

# 2. Revert code
git revert <commit_hash>

# 3. Rebuild and deploy
docker-compose down
docker-compose build
docker-compose up -d

# 4. Verify health
curl http://localhost:8000/health

# 5. Alert team
# Notify stakeholders of incident
```

## Scaling Guide

### Vertical Scaling (More Resources)
```bash
# Increase Docker memory
docker update --memory 4g voice_agent_backend

# Increase database connections
# Edit postgresql.conf: max_connections = 200

# Increase Redis memory
# Edit redis.conf: maxmemory 2gb
```

### Horizontal Scaling (More Instances)
```bash
# Multiple backend instances
docker-compose up -d --scale backend=3

# Configure load balancer
# Point LB to multiple backend IPs
# Enable health check on /health endpoint

# Database replication
# Set up PostgreSQL replication
# Configure backup standby
```

### Database Optimization
```sql
-- Add missing indexes
CREATE INDEX idx_patient_appointments 
ON appointments(patient_id, appointment_date);

-- Analyze query plans
EXPLAIN ANALYZE
SELECT * from  appointments WHERE patient_id = $1;

-- Archive old data
DELETE from  conversation_log 
WHERE created_at < NOW() - INTERVAL '90 days';
```

## Cost Optimization

1. **API Calls**
   - Cache LLM responses (24h TTL)
   - Batch STT requests
   - Use cheaper model variant

2. **Storage**
   - Archive old logs (S3 Glacier)
   - Delete old conversation logs
   - Compress database backups

3. **Infrastructure**
   - Right-size instances
   - Use spot instances for non-critical
   - Schedule resources (scale down nights)

4. **Database**
   - Connection pooling
   - Query optimization
   - Index cleanup

## Compliance Checklist

### HIPAA (if applicable)
- [ ] PHI encryption at rest
- [ ] PHI encryption in transit
- [ ] Access controls
- [ ] Audit logging
- [ ] Business associate agreements
- [ ] Breach notification plan

### GDPR (EU users)
- [ ] Right to be forgotten implemented
- [ ] Data export capability
- [ ] Privacy policy updated
- [ ] Consent management
- [ ] Data processing agreements

### SOC 2
- [ ] Security controls documented
- [ ] Logging and monitoring
- [ ] Access controls
- [ ] Change management
- [ ] Incident response plan

## Success Metrics

Track these metrics to ensure healthy system:

```
Availability:    >= 99.9%
Error Rate:      < 0.1%
Latency P50:     < 250ms
Latency P95:     < 450ms
Latency P99:     < 600ms
Success Rate:    >= 99.5%
Daily Active:    Track growth
Retention:       > 80%
NPS Score:       Track satisfaction
```

---

**Document Version**: 1.0  
**Last Updated**: December 2024
