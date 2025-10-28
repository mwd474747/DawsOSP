# DawsOS Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git (for cloning the repository)
- 8GB+ RAM recommended
- 20GB+ disk space

### One-Command Deployment
```bash
# Clone the repository
git clone <repository-url>
cd DawsOSP

# Start the complete system
./deploy.sh dev
```

## 📋 System Architecture

### Services Overview
- **dawsos-ui**: Next.js frontend (Port 3000)
- **backend**: FastAPI backend (Port 8000)
- **postgres**: PostgreSQL database (Port 5432)
- **redis**: Redis cache (Port 6379)
- **worker**: Background job processor
- **observability**: Optional monitoring stack

### Docker Compose Structure
```
DawsOS Stack
├── dawsos-ui (Next.js Frontend)
├── backend (FastAPI API)
├── postgres (Database)
├── redis (Cache)
├── worker (Background Jobs)
└── observability (Monitoring)
```

## 🛠️ Deployment Options

### Development Mode
```bash
# Quick start for development
./start.sh

# Or full Docker deployment
./deploy.sh dev
```

### Production Mode
```bash
# Production deployment
./deploy.sh prod

# With clean build
./deploy.sh prod true
```

### Individual Services
```bash
# Start only backend services
docker compose up -d postgres redis backend

# Start only frontend
docker compose up -d dawsos-ui

# Start with monitoring
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
# Database
POSTGRES_DB=dawsos
POSTGRES_USER=dawsos
POSTGRES_PASSWORD=your_password

# Redis
REDIS_PASSWORD=your_redis_password

# API
API_SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Port Configuration
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Database**: localhost:5432
- **Redis**: localhost:6379
- **Monitoring**: http://localhost:3001 (if enabled)

## 📊 Monitoring & Health Checks

### Health Endpoints
- Frontend: http://localhost:3000/api/health
- Backend: http://localhost:8000/health
- Database: Checked via backend health endpoint

### Logs
```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f dawsos-ui
docker compose logs -f backend
```

### Container Status
```bash
# Check running containers
docker compose ps

# Check resource usage
docker stats
```

## 🔄 Maintenance

### Updates
```bash
# Pull latest changes
git pull

# Rebuild and restart
./deploy.sh dev true
```

### Database Management
```bash
# Access database
docker compose exec postgres psql -U dawsos -d dawsos

# Backup database
docker compose exec postgres pg_dump -U dawsos dawsos > backup.sql

# Restore database
docker compose exec -T postgres psql -U dawsos -d dawsos < backup.sql
```

### Cleanup
```bash
# Stop all services
docker compose down

# Remove all data (WARNING: This deletes all data)
docker compose down -v

# Remove unused images
docker system prune -a
```

## 🐛 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using the port
lsof -i :3000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

#### Docker Build Fails
```bash
# Clean Docker cache
docker system prune -a

# Rebuild with no cache
./deploy.sh dev true
```

#### Database Connection Issues
```bash
# Check database logs
docker compose logs postgres

# Restart database
docker compose restart postgres
```

#### Frontend Build Issues
```bash
# Check Next.js logs
docker compose logs dawsos-ui

# Rebuild frontend
docker compose build dawsos-ui --no-cache
```

### Debug Mode
```bash
# Run with debug logging
DEBUG=1 ./deploy.sh dev

# Access container shell
docker compose exec dawsos-ui sh
docker compose exec backend bash
```

## 📈 Performance Tuning

### Resource Limits
Edit `docker-compose.yml` to set resource limits:

```yaml
services:
  dawsos-ui:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

### Database Optimization
```bash
# Increase shared_buffers
docker compose exec postgres psql -U dawsos -d dawsos -c "ALTER SYSTEM SET shared_buffers = '256MB';"
```

## 🔒 Security

### Production Security Checklist
- [ ] Change default passwords
- [ ] Use HTTPS in production
- [ ] Set up firewall rules
- [ ] Enable database encryption
- [ ] Use secrets management
- [ ] Regular security updates

### SSL/TLS Setup
```bash
# Add SSL certificates to docker-compose.yml
# See docker-compose.prod.yml for example
```

## 📚 Additional Resources

### Documentation
- [API Documentation](http://localhost:8000/docs)
- [Frontend Components](./dawsos-ui/README.md)
- [Backend Services](./backend/README.md)

### Support
- Check logs: `docker compose logs -f`
- Health checks: Visit health endpoints
- Database issues: Check postgres logs
- Frontend issues: Check dawsos-ui logs

## 🎯 Next Steps

1. **Configure Environment**: Set up your `.env` file
2. **Deploy System**: Run `./deploy.sh dev`
3. **Access UI**: Visit http://localhost:3000
4. **Test API**: Visit http://localhost:8000/docs
5. **Monitor**: Check logs and health endpoints

---

**Need Help?** Check the troubleshooting section or review the logs for specific error messages.
