-- Read-only role for ad-hoc reporting and BI tools.
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'payroll_readonly') THEN
    CREATE ROLE payroll_readonly LOGIN PASSWORD 'readonly';
  END IF;
END
$$;

GRANT CONNECT ON DATABASE payroll TO payroll_readonly;
GRANT USAGE ON SCHEMA public TO payroll_readonly;
ALTER DEFAULT PRIVILEGES FOR ROLE payroll IN SCHEMA public GRANT SELECT ON TABLES TO payroll_readonly;
