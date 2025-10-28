# DawsOS Troubleshooting Guide

## Common Issues

### Authentication Issues
**Problem**: "Invalid credentials" error
**Solution**: 
- Verify email and password
- Check password length (8+ characters)
- Ensure user exists in database

**Problem**: "Missing Authorization header" error
**Solution**:
- Include `Authorization: Bearer <token>` header
- Verify token is valid and not expired
- Check token format

### Database Issues
**Problem**: "Database connection failed"
**Solution**:
- Check DATABASE_URL environment variable
- Verify PostgreSQL is running
- Check database credentials
- Ensure database exists

**Problem**: "Table does not exist"
**Solution**:
- Run database migrations
- Check schema files
- Verify database initialization

### API Issues
**Problem**: "Internal server error"
**Solution**:
- Check application logs
- Verify all services are running
- Check database connectivity
- Review error details

### Frontend Issues
**Problem**: "Failed to fetch" error
**Solution**:
- Check backend API is running
- Verify API URL configuration
- Check network connectivity
- Review browser console

## Debug Commands

```bash
# Check database connection
python -c "from backend.app.db.connection import init_db_pool; import asyncio; asyncio.run(init_db_pool())"

# Test authentication
python scripts/setup_super_admin.py

# Check API health
curl http://localhost:8000/health

# View logs
tail -f backend/logs/app.log
```

## Getting Help

1. Check this troubleshooting guide
2. Review application logs
3. Check GitHub issues
4. Contact development team
