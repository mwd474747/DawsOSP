# DawsOS Authentication Quick Start Guide

**Last Updated**: 2025-10-27

This guide shows how to set up and use JWT authentication in DawsOS.

---

## 1. Installation (5 minutes)

### Step 1: Install Dependencies

```bash
cd backend
pip install PyJWT>=2.8.0 bcrypt>=4.1.0 python-multipart>=0.0.6
```

### Step 2: Set JWT Secret

```bash
# Generate a secure secret
export AUTH_JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Or set in .env file
echo "AUTH_JWT_SECRET=your_secure_secret_here" >> .env
```

### Step 3: Run Database Migration

```bash
# Connect to PostgreSQL
psql -U dawsos_app -d dawsos -f backend/db/migrations/010_add_users_and_audit_log.sql
```

Expected output:
```
CREATE TABLE
CREATE INDEX
...
✅ Users table created
✅ Audit log table created
```

### Step 4: Verify Installation

```bash
# Check users table
psql -U dawsos_app -d dawsos -c "SELECT email, role FROM users;"

# Expected output:
#        email        | role
# --------------------+-------
#  admin@dawsos.com   | ADMIN
#  user@dawsos.com    | USER
```

---

## 2. Testing Authentication (2 minutes)

### Test JWT Flow (No Database Required)

```bash
cd backend
python3 tests/demo_jwt_flow.py
```

Expected output:
```
================================================================================
DawsOS JWT AUTHENTICATION FLOW DEMONSTRATION
================================================================================

📝 STEP 1: Generate JWT Token
--------------------------------------------------------------------------------
User ID:  11111111-1111-1111-1111-111111111111
Email:    manager@dawsos.com
Role:     MANAGER

Generated JWT Token:
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

✅ STEP 2: Verify JWT Token
...
✅ ALL TESTS PASSED
```

---

## 3. Using the API (3 minutes)

### Step 1: Start Backend

```bash
cd backend
./run_api.sh
```

Server starts on `http://localhost:8000`

### Step 2: Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@dawsos.com",
    "password": "user123"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "11111111-1111-1111-1111-111111111111",
    "email": "user@dawsos.com",
    "role": "USER"
  }
}
```

**Save the `access_token` - you'll need it for all API calls!**

### Step 3: Execute Pattern (With JWT)

```bash
# Replace <TOKEN> with your access_token from login
curl -X POST http://localhost:8000/v1/execute \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "portfolio_overview",
    "inputs": {
      "portfolio_id": "11111111-1111-1111-1111-111111111111",
      "lookback_days": 252
    }
  }'
```

### Step 4: View Audit Logs

```bash
# Check your activity
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <TOKEN>"
```

---

## 4. Default Users

After running the migration, these users are created:

| Email | Password | Role | Permissions |
|-------|----------|------|-------------|
| `admin@dawsos.com` | `admin123` | ADMIN | All permissions |
| `user@dawsos.com` | `user123` | USER | Read + Execute patterns |

⚠️ **CHANGE PASSWORDS IN PRODUCTION!**

```bash
# Change password (as ADMIN)
curl -X POST http://localhost:8000/auth/users/11111111-1111-1111-1111-111111111111/password \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"new_password": "new_secure_password"}'
```

---

## 5. Role Hierarchy

| Role | Level | Permissions |
|------|-------|-------------|
| **VIEWER** | 1 | Read portfolios, Read metrics |
| **USER** | 2 | + Execute patterns |
| **MANAGER** | 3 | + Export reports, Write trades |
| **ADMIN** | 4 | All permissions (including user management) |

**Permission Inheritance**: Higher roles inherit all permissions from lower roles.

---

## 6. Common Tasks

### Create New User (ADMIN only)

```bash
curl -X POST http://localhost:8000/auth/users \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "secure_password_123",
    "role": "USER"
  }'
```

### Refresh Token

```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Authorization: Bearer <OLD_TOKEN>"
```

Returns new token with extended expiration.

### Check Permissions

```bash
curl -X GET http://localhost:8000/auth/permissions \
  -H "Authorization: Bearer <TOKEN>"
```

Returns list of your permissions:
```json
["read_portfolio", "read_metrics", "execute_patterns"]
```

---

## 7. Troubleshooting

### Error: "Missing Authorization header"

**Problem**: Forgot to include JWT token

**Solution**: Add `-H "Authorization: Bearer <TOKEN>"` to your curl command

### Error: "Token has expired"

**Problem**: JWT tokens expire after 24 hours

**Solution**: Login again or use refresh endpoint

### Error: "Access denied to portfolio"

**Problem**: Trying to access a portfolio you don't own

**Solution**:
- Users can only access their own portfolios
- ADMINs can access all portfolios
- Check `user_id` in portfolios table matches your JWT `user_id`

### Error: "Missing required permission: write_trades"

**Problem**: Your role doesn't have the required permission

**Solution**:
- Check your role: `GET /auth/me`
- Check required permission for endpoint
- Ask ADMIN to upgrade your role if needed

---

## 8. Security Best Practices

✅ **Always use HTTPS in production**
- JWT tokens should never be sent over HTTP
- Use TLS/SSL certificates

✅ **Set strong JWT secret**
- At least 32 random bytes
- Never commit to version control
- Store in environment variable

✅ **Change default passwords**
- Default passwords are for development only
- Use strong passwords (12+ chars, mixed case, numbers, symbols)

✅ **Rotate tokens regularly**
- Tokens expire after 24 hours
- Use refresh endpoint before expiry

✅ **Monitor audit logs**
- Check for suspicious activity
- Export logs to external system (Splunk, ELK)

✅ **Use least-privilege principle**
- Give users minimum required role
- VIEWER for read-only access
- USER for standard operations
- MANAGER only when needed
- ADMIN very sparingly

---

## 9. API Endpoints Reference

### Authentication Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/login` | None | Login with email/password |
| POST | `/auth/refresh` | JWT | Refresh token |
| GET | `/auth/me` | JWT | Get current user info |
| GET | `/auth/permissions` | JWT | Get user permissions |
| GET | `/auth/users` | JWT (ADMIN) | List all users |
| POST | `/auth/users` | JWT (ADMIN) | Create new user |

### Protected Endpoints

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| POST | `/v1/execute` | `execute_patterns` | Execute pattern |
| POST | `/v1/trades` | `write_trades` | Execute trade |
| POST | `/v1/reports/export` | `export_reports` | Export PDF report |

---

## 10. Environment Variables

Required environment variables:

```bash
# JWT Authentication
AUTH_JWT_SECRET=your_secure_secret_here_32_bytes_minimum

# Database (existing)
DATABASE_URL=postgresql://dawsos_app:dawsos_app_pass@localhost:5432/dawsos

# API Configuration (existing)
PRICING_POLICY=WM4PM_CAD
EXECUTOR_API_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:8501,http://localhost:3000
```

---

## 11. Next Steps

After basic authentication is working:

1. **Enable Rate Limiting**: Limit login attempts and API calls
2. **Add Email Verification**: Verify email addresses on signup
3. **Implement Password Reset**: Allow users to reset forgotten passwords
4. **Add MFA**: Multi-factor authentication for enhanced security
5. **Set up Monitoring**: Track failed auth attempts and permission denials
6. **Export Audit Logs**: Send to external system for compliance

---

## 12. Quick Reference

### Login Flow

```
1. POST /auth/login → Get JWT token
2. Save token (valid 24 hours)
3. Use token in Authorization header: "Bearer <token>"
4. Before expiry, POST /auth/refresh → Get new token
```

### Permission Check Flow

```
1. Request arrives with JWT token
2. Middleware verifies token signature
3. Extract user_id and role from claims
4. Check if user owns portfolio (if applicable)
5. Check if role has required permission
6. If all pass, execute endpoint logic
7. Log action to audit_log table
```

### Audit Trail

Every API call is logged:
- User ID
- Action (e.g., "execute_pattern")
- Resource type (e.g., "pattern")
- Resource ID (e.g., "portfolio_overview")
- Details (inputs, timing, metadata)
- Timestamp

Query audit logs:
```bash
curl -X GET "http://localhost:8000/auth/users/me/activity?limit=100" \
  -H "Authorization: Bearer <TOKEN>"
```

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review `/backend/tests/demo_jwt_flow.py` for examples
3. Check audit logs for permission denials
4. Review `AUTHENTICATION_IMPLEMENTATION_REPORT.md` for detailed docs

---

**Last Updated**: 2025-10-27
**Version**: 1.0.0
