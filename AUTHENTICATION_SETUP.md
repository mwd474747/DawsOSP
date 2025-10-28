# DawsOS Authentication Setup

## Super Admin Account

- **Email**: michael@dawsos.com
- **Password**: mozzuq-byfqyQ-5tefvu
- **Role**: ADMIN (full access)

## Quick Start

1. **Start the system**
   ```bash
   # Backend
   ./backend/run_api.sh
   
   # Frontend
   cd dawsos-ui && npm run dev
   ```

2. **Access the system**
   - Frontend: http://localhost:3002
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

3. **Login with super admin credentials**

## API Authentication

### Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "michael@dawsos.com", "password": "mozzuq-byfqyQ-5tefvu"}'
```

### Use Token
```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer <your-token>"
```

## Security Features

- JWT tokens with 24-hour expiration
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Input validation and sanitization
- SQL injection protection

## User Roles

- **ADMIN**: Full system access
- **MANAGER**: Portfolio management access
- **USER**: Standard user access
- **VIEWER**: Read-only access
