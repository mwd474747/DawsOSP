# DawsOS Authentication Setup

**Date**: October 28, 2025  
**Purpose**: Complete authentication setup and usage guide  
**Status**: ✅ COMPLETE

---

## 🎯 OVERVIEW

DawsOS uses JWT-based authentication with role-based access control (RBAC). The system is configured with a super admin account that has full access to all APIs and features.

---

## 🔐 SUPER ADMIN ACCOUNT

### **Credentials**
- **Email**: `michael@dawsos.com`
- **Password**: `mozzuq-byfqyQ-5tefvu`
- **Role**: `ADMIN`
- **Permissions**: All permissions (`*`)

### **Account Details**
- **User ID**: `c70af1b9-3fa7-4fa2-8660-2871fedb201f`
- **Status**: Active
- **Created**: October 28, 2025
- **Last Login**: On first use

---

## 🚀 QUICK START

### **1. Start the System**
```bash
# Start backend API
./backend/run_api.sh

# Start frontend UI (in another terminal)
cd dawsos-ui && npm run dev
```

### **2. Access the System**
- **Frontend UI**: http://localhost:3002
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### **3. Login**
Use the super admin credentials above to log in to either the UI or API.

---

## 🔧 API AUTHENTICATION

### **Login Endpoint**
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "michael@dawsos.com",
  "password": "mozzuq-byfqyQ-5tefvu"
}
```

### **Response**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "c70af1b9-3fa7-4fa2-8660-2871fedb201f",
    "email": "michael@dawsos.com",
    "role": "ADMIN"
  }
}
```

### **Using the Token**
```bash
# Add to all API requests
Authorization: Bearer <access_token>
```

### **Example API Call**
```bash
curl -X POST "http://localhost:8000/v1/execute" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "portfolio_overview",
    "portfolio_id": "test-portfolio",
    "require_fresh": false
  }'
```

---

## 📋 AVAILABLE ENDPOINTS

### **Authentication Endpoints**
- `POST /auth/login` - Login and get token
- `GET /auth/me` - Get current user info
- `GET /auth/permissions` - Get user permissions
- `POST /auth/refresh` - Refresh token
- `POST /auth/logout` - Logout and invalidate token

### **Core API Endpoints**
- `POST /v1/execute` - Execute patterns
- `GET /health` - Health check (no auth required)
- `GET /health/pack` - Pricing pack status
- `GET /metrics` - System metrics

### **Admin Endpoints**
- `GET /auth/users` - List all users
- `POST /auth/users` - Create new user

---

## 🔒 SECURITY CONFIGURATION

### **JWT Configuration**
- **Algorithm**: HS256
- **Expiration**: 24 hours (86400 seconds)
- **Secret**: Uses environment variable `AUTH_JWT_SECRET` or default for development

### **Password Requirements**
- **Minimum Length**: 8 characters
- **Hashing**: bcrypt with salt rounds
- **Validation**: Server-side validation

### **Role-Based Access Control**
- **VIEWER**: Read-only access
- **USER**: Standard user access
- **MANAGER**: Management access
- **ADMIN**: Full administrative access

---

## 🛠️ TECHNICAL IMPLEMENTATION

### **Authentication Flow**
1. User submits credentials to `/auth/login`
2. Server validates credentials against database
3. Server generates JWT token with user claims
4. Client stores token and includes in subsequent requests
5. Server validates token on protected endpoints

### **Database Schema**
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR UNIQUE NOT NULL,
    role VARCHAR NOT NULL CHECK (role IN ('VIEWER', 'USER', 'MANAGER', 'ADMIN')),
    permissions TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    password_hash VARCHAR NOT NULL,
    last_login_at TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### **Middleware**
- **AuthMiddleware**: Validates JWT tokens on protected routes
- **DBMiddleware**: Initializes database connections
- **ErrorMiddleware**: Handles authentication errors

---

## 🔧 SETUP SCRIPT

### **Run Setup Script**
```bash
python scripts/setup_super_admin.py
```

This script will:
1. Create the super admin user account
2. Validate authentication works
3. Print usage instructions
4. Confirm setup completion

### **Manual Setup** (if needed)
```python
from backend.app.services.auth import AuthService
from backend.app.db.connection import init_db_pool

async def create_admin():
    pool = await init_db_pool()
    auth_service = AuthService()
    
    result = await auth_service.register_user(
        email='michael@dawsos.com',
        password='mozzuq-byfqyQ-5tefvu',
        role='ADMIN'
    )
    
    return result
```

---

## 🚨 TROUBLESHOOTING

### **Common Issues**

#### **1. "Invalid credentials" Error**
- Check email and password are correct
- Ensure password meets minimum length (8 characters)
- Verify user exists in database

#### **2. "Missing Authorization header" Error**
- Include `Authorization: Bearer <token>` header
- Ensure token is valid and not expired
- Check token format (no extra spaces)

#### **3. "Token expired" Error**
- Login again to get new token
- Tokens expire after 24 hours
- Use refresh endpoint if available

#### **4. Database Connection Issues**
- Ensure PostgreSQL is running
- Check DATABASE_URL environment variable
- Verify database schema is applied

### **Debug Commands**
```bash
# Check database connection
python -c "from backend.app.db.connection import init_db_pool; import asyncio; asyncio.run(init_db_pool())"

# Test authentication
python -c "from backend.app.services.auth import AuthService; import asyncio; asyncio.run(AuthService().authenticate_user('michael@dawsos.com', 'mozzuq-byfqyQ-5tefvu'))"

# Check API health
curl http://localhost:8000/health
```

---

## 📝 DEVELOPMENT NOTES

### **Environment Variables**
```bash
# Required for production
export AUTH_JWT_SECRET="your-secure-jwt-secret"
export DATABASE_URL="postgresql://user:pass@localhost:5432/dawsos"

# Optional
export AUTH_TOKEN_EXPIRY_HOURS="24"
export AUTH_PASSWORD_MIN_LENGTH="8"
```

### **Testing**
```bash
# Run authentication tests
pytest backend/tests/test_auth.py

# Run integration tests
pytest backend/tests/test_integration.py
```

### **Production Considerations**
1. Set secure JWT secret
2. Use HTTPS in production
3. Implement rate limiting
4. Add audit logging
5. Consider token refresh mechanism
6. Implement account lockout policies

---

## ✅ VERIFICATION CHECKLIST

- [x] Super admin user created
- [x] Authentication service working
- [x] JWT tokens generated correctly
- [x] API endpoints protected
- [x] Database schema applied
- [x] Frontend can authenticate
- [x] Backend API accessible
- [x] Documentation complete
- [x] Setup script functional
- [x] Error handling implemented

---

## 🎯 NEXT STEPS

1. **Start using the system** with the provided credentials
2. **Test all API endpoints** to ensure they work correctly
3. **Configure production environment** with secure secrets
4. **Add additional users** as needed using the admin endpoints
5. **Monitor authentication logs** for security

---

**The authentication system is fully functional and ready for use. The super admin account has been created and configured with full access to all APIs and features.**
