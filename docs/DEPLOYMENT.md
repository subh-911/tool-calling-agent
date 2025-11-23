# Deployment Guide

Complete guide for deploying the Tool-Calling Agent to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Security Considerations](#security-considerations)
- [Monitoring and Logging](#monitoring-and-logging)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required

- Python 3.9 or higher
- Docker and Docker Compose (for containerized deployment)
- OpenAI API key and/or Anthropic API key
- 1GB+ RAM (2GB+ recommended)
- SSL certificate (for HTTPS in production)

### Recommended

- Reverse proxy (Nginx, Traefik)
- Process manager (systemd, supervisord)
- Monitoring tools (Prometheus, Grafana)
- Log aggregation (ELK stack, Loki)

## Environment Configuration

### 1. Create Production Environment File

```bash
cp .env.example .env
```

### 2. Configure Production Settings

Edit `.env` with production values:

```bash
# Application Settings
APP_NAME=tool-calling-agent
ENVIRONMENT=production
LOG_LEVEL=INFO

# LLM Provider
DEFAULT_LLM_PROVIDER=openai

# API Keys (REQUIRED)
OPENAI_API_KEY=sk-your-actual-openai-key
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key

# Models
OPENAI_MODEL=gpt-4-turbo-preview
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Agent Configuration
MAX_TOOL_CALLS_PER_TURN=5
TOOL_CALL_TIMEOUT_SECONDS=30
ENABLE_TOOL_VALIDATION=true

# API Configuration
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["https://yourdomain.com"]
```

### 3. Security Best Practices

**Never commit `.env` files to version control!**

```bash
# Verify .env is in .gitignore
grep .env .gitignore

# Set restrictive permissions
chmod 600 .env
```

## Docker Deployment

### Method 1: Docker Compose (Recommended)

1. **Navigate to docker directory:**

```bash
cd docker
```

2. **Build and start services:**

```bash
docker-compose up -d
```

3. **View logs:**

```bash
docker-compose logs -f agent-api
```

4. **Check health:**

```bash
curl http://localhost:8000/api/v1/health
```

5. **Stop services:**

```bash
docker-compose down
```

### Method 2: Docker Build and Run

1. **Build image:**

```bash
docker build -f docker/Dockerfile -t tool-calling-agent:latest .
```

2. **Run container:**

```bash
docker run -d \
  --name tool-calling-agent \
  -p 8000:8000 \
  --env-file .env \
  tool-calling-agent:latest
```

3. **View logs:**

```bash
docker logs -f tool-calling-agent
```

### Docker Production Optimizations

**Multi-stage build** (already implemented):
- Smaller final image size
- Faster deployment
- Reduced attack surface

**Health checks** (already implemented):
- Automatic container restart on failure
- Load balancer integration

**Non-root user** (already implemented):
- Enhanced security
- Follows best practices

## Cloud Deployment

### AWS (Elastic Container Service)

1. **Push image to ECR:**

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -f docker/Dockerfile -t tool-calling-agent .
docker tag tool-calling-agent:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/tool-calling-agent:latest

# Push
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/tool-calling-agent:latest
```

2. **Create ECS task definition:**

```json
{
  "family": "tool-calling-agent",
  "containerDefinitions": [
    {
      "name": "agent-api",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/tool-calling-agent:latest",
      "memory": 1024,
      "cpu": 512,
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:openai-key"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/api/v1/health || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3
      }
    }
  ]
}
```

3. **Create ECS service with load balancer**

### Google Cloud Platform (Cloud Run)

1. **Build and push to Artifact Registry:**

```bash
# Configure Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build and push
gcloud builds submit --tag us-central1-docker.pkg.dev/PROJECT_ID/tool-calling-agent/app
```

2. **Deploy to Cloud Run:**

```bash
gcloud run deploy tool-calling-agent \
  --image us-central1-docker.pkg.dev/PROJECT_ID/tool-calling-agent/app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production \
  --set-secrets OPENAI_API_KEY=openai-key:latest \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 10
```

### Azure (Container Instances)

```bash
az container create \
  --resource-group myResourceGroup \
  --name tool-calling-agent \
  --image tool-calling-agent:latest \
  --dns-name-label tool-calling-agent \
  --ports 8000 \
  --environment-variables \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO \
  --secure-environment-variables \
    OPENAI_API_KEY=$OPENAI_API_KEY \
  --cpu 1 \
  --memory 1
```

### DigitalOcean (App Platform)

1. **Create app.yaml:**

```yaml
name: tool-calling-agent
services:
  - name: api
    dockerfile_path: docker/Dockerfile
    github:
      repo: your-username/tool-calling-agent
      branch: main
      deploy_on_push: true
    health_check:
      http_path: /api/v1/health
    http_port: 8000
    instance_count: 2
    instance_size_slug: basic-xs
    routes:
      - path: /
    envs:
      - key: ENVIRONMENT
        value: production
      - key: OPENAI_API_KEY
        type: SECRET
        value: ${OPENAI_API_KEY}
```

2. **Deploy:**

```bash
doctl apps create --spec app.yaml
```

## Traditional Server Deployment

### Using systemd (Linux)

1. **Create systemd service file:**

```bash
sudo nano /etc/systemd/system/tool-calling-agent.service
```

```ini
[Unit]
Description=Tool-Calling Agent API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/tool-calling-agent
Environment="PATH=/opt/tool-calling-agent/venv/bin"
EnvironmentFile=/opt/tool-calling-agent/.env
ExecStart=/opt/tool-calling-agent/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. **Enable and start service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable tool-calling-agent
sudo systemctl start tool-calling-agent
sudo systemctl status tool-calling-agent
```

### Using Nginx Reverse Proxy

1. **Install Nginx:**

```bash
sudo apt update
sudo apt install nginx
```

2. **Create Nginx configuration:**

```bash
sudo nano /etc/nginx/sites-available/tool-calling-agent
```

```nginx
upstream agent_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Logging
    access_log /var/log/nginx/agent-access.log;
    error_log /var/log/nginx/agent-error.log;

    # Proxy settings
    location / {
        proxy_pass http://agent_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Health check endpoint
    location /api/v1/health {
        proxy_pass http://agent_backend;
        access_log off;
    }
}
```

3. **Enable site and restart Nginx:**

```bash
sudo ln -s /etc/nginx/sites-available/tool-calling-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Security Considerations

### 1. API Key Management

**Use environment variables or secret managers:**

```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id openai-api-key

# Azure Key Vault
az keyvault secret show --vault-name myVault --name openai-api-key

# Google Secret Manager
gcloud secrets versions access latest --secret="openai-api-key"
```

### 2. HTTPS/TLS

**Always use HTTPS in production:**

```bash
# Let's Encrypt with Certbot
sudo certbot --nginx -d yourdomain.com
```

### 3. Rate Limiting

**Implement rate limiting (example with Nginx):**

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;

location /api/ {
    limit_req zone=api_limit burst=10 nodelay;
    proxy_pass http://agent_backend;
}
```

### 4. Firewall Rules

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

### 5. Authentication (Optional)

Add API key authentication to protect endpoints:

```python
# In app/api/routes.py
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

# Add to endpoints
@router.post("/query", dependencies=[Depends(verify_api_key)])
```

## Monitoring and Logging

### Application Logs

**View logs:**

```bash
# Docker
docker-compose logs -f

# Systemd
sudo journalctl -u tool-calling-agent -f

# Log files
tail -f /var/log/tool-calling-agent/app.log
```

### Health Monitoring

**Set up health check monitoring:**

```bash
# Simple cron job
*/5 * * * * curl -f http://localhost:8000/api/v1/health || echo "Service down!" | mail -s "Alert" admin@example.com
```

### Prometheus Metrics (Optional)

1. **Install prometheus-fastapi-instrumentator:**

```bash
pip install prometheus-fastapi-instrumentator
```

2. **Add to app/main.py:**

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(...)
Instrumentator().instrument(app).expose(app)
```

3. **Access metrics:**

```
http://localhost:8000/metrics
```

## Scaling

### Horizontal Scaling

**Run multiple instances behind a load balancer:**

```bash
# Docker Compose scaling
docker-compose up -d --scale agent-api=3

# Kubernetes deployment
kubectl scale deployment tool-calling-agent --replicas=5
```

### Vertical Scaling

**Adjust resources based on load:**

```yaml
# docker-compose.yml
services:
  agent-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Performance Tuning

**Uvicorn workers:**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Calculate optimal workers:**
```
workers = (2 × CPU cores) + 1
```

## Backup and Disaster Recovery

### Configuration Backup

```bash
# Backup environment and configs
tar -czf backup-$(date +%Y%m%d).tar.gz .env docker/ app/config.py

# Store in S3
aws s3 cp backup-$(date +%Y%m%d).tar.gz s3://my-backups/
```

### Database Backup (if applicable)

If you add database storage:

```bash
# PostgreSQL
pg_dump dbname > backup.sql

# MongoDB
mongodump --db=agent_db --out=/backup
```

## Troubleshooting

### Service Won't Start

1. Check logs for errors
2. Verify environment variables are set
3. Ensure API keys are valid
4. Check port availability

```bash
# Check if port 8000 is in use
sudo lsof -i :8000

# Test configuration
python -c "from app.config import settings; print(settings)"
```

### High Memory Usage

```bash
# Monitor resource usage
docker stats

# Reduce workers
uvicorn app.main:app --workers 2

# Check for memory leaks
python -m memory_profiler app/main.py
```

### Slow Response Times

1. Enable query logging
2. Monitor LLM API latency
3. Consider caching tool results
4. Check network connectivity

### SSL Certificate Issues

```bash
# Renew Let's Encrypt certificate
sudo certbot renew

# Test certificate
openssl s_client -connect yourdomain.com:443
```

## Checklist

Before going to production:

- [ ] API keys are stored securely (not in code)
- [ ] HTTPS is enabled with valid certificate
- [ ] Logging is configured and working
- [ ] Health checks are responding
- [ ] Monitoring is set up
- [ ] Backups are configured
- [ ] Rate limiting is implemented
- [ ] CORS is properly configured
- [ ] Error handling is tested
- [ ] Load testing is performed
- [ ] Documentation is updated
- [ ] Disaster recovery plan is in place

---

For more information, see:
- [API Documentation](API.md)
- [Tool Creation Guide](TOOLS.md)
