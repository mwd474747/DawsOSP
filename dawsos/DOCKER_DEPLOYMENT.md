# DawsOS Docker Deployment Guide

## Quick Start

### 1. Prerequisites
- Docker installed (version 20.10+)
- Docker Compose installed (version 2.0+)
- At least 2GB free disk space
- API keys for: Anthropic (Claude), FMP, FRED, NewsAPI

### 2. Setup

```bash
# Clone the repository
git clone https://github.com/mwd474747/DawsOSB.git
cd DawsOSB/dawsos

# Copy environment template
cp .env.docker .env

# Edit .env and add your API keys
nano .env
```

### 3. Build & Run

#### Option A: Simple Docker (Recommended for start)
```bash
# Make scripts executable
chmod +x docker-build.sh docker-run.sh

# Build the image
./docker-build.sh

# Run the container
./docker-run.sh
```

#### Option B: Docker Compose (Full stack with Redis + PostgreSQL)
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f dawsos
```

### 4. Access DawsOS
Open browser to: http://localhost:8501

---

## Architecture

### Container Structure
```
dawsos (main app)
├── Python 3.11 base
├── Streamlit web UI
├── All agents & capabilities
└── Persistent storage volume

redis (optional cache)
├── In-memory caching
└── Session storage

postgres (optional database)
├── Production data storage
└── Historical analytics
```

### Port Mappings
- `8501` - Streamlit UI
- `6379` - Redis (if using docker-compose)
- `5432` - PostgreSQL (if using docker-compose)

---

## Configuration

### Environment Variables

#### Required API Keys
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
FMP_API_KEY=your_fmp_key
FRED_API_KEY=your_fred_key
NEWSAPI_KEY=your_news_key
```

#### Optional Settings
```bash
# Database
POSTGRES_PASSWORD=dawsos123
POSTGRES_HOST=postgres

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Streamlit
STREAMLIT_THEME_BASE=dark
STREAMLIT_SERVER_PORT=8501
```

### Volume Mounts

#### Persistent Data
```yaml
volumes:
  - ./storage:/app/storage     # Knowledge graph, workflows
  - ./logs:/app/logs           # Application logs
  - ./.env:/app/.env:ro        # Environment variables
```

---

## Docker Commands

### Basic Operations

```bash
# Build image
docker build -t dawsos:latest .

# Run container
docker run -d \
  --name dawsos \
  -p 8501:8501 \
  --env-file .env \
  -v ./storage:/app/storage \
  dawsos:latest

# View logs
docker logs -f dawsos

# Stop container
docker stop dawsos

# Remove container
docker rm dawsos

# Shell access
docker exec -it dawsos /bin/bash
```

### Docker Compose Operations

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose build --no-cache

# View service logs
docker-compose logs -f dawsos

# Scale services
docker-compose up -d --scale dawsos=2

# Clean up everything
docker-compose down -v --remove-orphans
```

---

## Production Deployment

### 1. Security Hardening

```dockerfile
# Add to Dockerfile
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Run as non-root
USER 1000:1000

# Add security headers
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
```

### 2. Performance Optimization

```yaml
# docker-compose.yml
services:
  dawsos:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### 3. Health Monitoring

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 4. Backup Strategy

```bash
#!/bin/bash
# backup.sh

# Backup storage volume
docker run --rm \
  -v dawsos_storage:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/dawsos-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .

# Backup PostgreSQL
docker-compose exec postgres pg_dump -U dawsos dawsos > backup-$(date +%Y%m%d).sql
```

---

## Kubernetes Deployment

### Basic Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dawsos
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dawsos
  template:
    metadata:
      labels:
        app: dawsos
    spec:
      containers:
      - name: dawsos
        image: dawsos:latest
        ports:
        - containerPort: 8501
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: dawsos-secrets
              key: anthropic-key
        volumeMounts:
        - name: storage
          mountPath: /app/storage
      volumes:
      - name: storage
        persistentVolumeClaim:
          claimName: dawsos-storage
---
apiVersion: v1
kind: Service
metadata:
  name: dawsos-service
spec:
  selector:
    app: dawsos
  ports:
  - port: 8501
    targetPort: 8501
  type: LoadBalancer
```

---

## Troubleshooting

### Common Issues

#### Container won't start
```bash
# Check logs
docker logs dawsos

# Common fixes:
# 1. Ensure .env file exists
# 2. Check port 8501 is free
# 3. Verify API keys are set
```

#### Permission errors
```bash
# Fix storage permissions
chmod -R 777 storage/

# Or run container as current user
docker run --user $(id -u):$(id -g) ...
```

#### Memory issues
```bash
# Increase Docker memory limit
docker run -m 4g dawsos:latest

# Or in docker-compose:
mem_limit: 4g
```

#### Network issues
```bash
# Check container network
docker network inspect bridge

# Test from inside container
docker exec dawsos curl http://localhost:8501
```

### Debug Mode

```bash
# Run interactively for debugging
docker run -it \
  --rm \
  --env-file .env \
  -v ./storage:/app/storage \
  dawsos:latest \
  /bin/bash

# Then manually start
streamlit run main.py
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Docker Build and Push

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Build Docker image
      run: docker build -t dawsos:${{ github.sha }} .

    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push dawsos:${{ github.sha }}
```

---

## Multi-Architecture Build

```bash
# Build for multiple platforms
docker buildx create --name multiarch --use
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag dawsos:latest \
  --push .
```

---

## Monitoring

### Prometheus Metrics
Add to `main.py`:
```python
from prometheus_client import Counter, Histogram, generate_latest

# Add metrics endpoint
@app.route('/metrics')
def metrics():
    return generate_latest()
```

### Logging
```bash
# Aggregate logs
docker-compose logs -f --tail=100

# Save logs
docker logs dawsos > dawsos.log 2>&1
```

---

## Summary

Docker deployment provides:
- ✅ **Consistent environment** across all platforms
- ✅ **Easy scaling** with docker-compose
- ✅ **Data persistence** through volumes
- ✅ **Health monitoring** with built-in checks
- ✅ **Production ready** with security & optimization

Total deployment time: ~5 minutes