-- Runs once when the Postgres volume is created. Tables are managed by Alembic
-- migrations in services/api; this script only prepares the database itself.
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

ALTER DATABASE payroll SET timezone TO 'UTC';
