-- Role initialization
-- Purpose: create application roles with least-privilege defaults
-- Idempotent: safe to run multiple times

DO
$$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'dawsos_app') THEN
        CREATE ROLE dawsos_app LOGIN PASSWORD 'dawsos_app_pass';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE dawsos TO dawsos_app;
GRANT USAGE ON SCHEMA public TO dawsos_app;

-- Ensure application role can read/write portfolio-scoped tables by default
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO dawsos_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO dawsos_app;
