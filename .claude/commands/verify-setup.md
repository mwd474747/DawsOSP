---
description: Verify DawsOS development environment setup
---

Run comprehensive setup verification:

1. Check pattern count: `ls -1 backend/patterns/*.json | wc -l` (should be 13)
2. Check agent count: `grep -c "register_agent" combined_server.py` (should be 4)
3. Check database connection: `psql $DATABASE_URL -c "\dt" | wc -l` (should show tables)
4. Check environment variables:
   - `echo $DATABASE_URL` (should be set)
   - `echo $AUTH_JWT_SECRET` (should be 32+ chars)
5. Check server health: `curl -s http://localhost:8000/health | jq .`
6. Check endpoints: `curl -s http://localhost:8000/docs` (should return OpenAPI spec)

Report any failures clearly.
