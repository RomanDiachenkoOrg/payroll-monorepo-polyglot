# Database

Postgres 16, started by `docker compose`.

- `init/` - scripts run by the Postgres image the first time the data volume is created
  (extensions, timezone, a read-only reporting role).
- The schema itself is versioned with Alembic in `services/api/alembic/versions` and is applied
  by the API container on start (`alembic upgrade head`), followed by `python -m app.seed`,
  which loads demo data when the database is empty.

Connect locally: `psql postgres://payroll:payroll@localhost:5432/payroll`

Reset everything: `docker compose down -v && docker compose up --build`
