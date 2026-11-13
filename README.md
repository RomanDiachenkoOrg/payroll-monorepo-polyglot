# Acme Payroll (polyglot monorepo)

Payroll and HR system for a small company, split into a few services that each use the
language that suits them best. Everything starts with one `docker compose` command.

- **api** - Python FastAPI service: authentication, employees, departments, timesheets,
  pay runs and the payroll calculation. Publishes events to Redis.
- **reports** - Go service that reads Postgres directly and serves report JSON and CSV exports.
- **notifier** - small Node.js worker that consumes events from Redis (pay run approved,
  timesheet rejected) and writes the resulting emails to the `mailbox` table.
- **web** - Vue 3 single page app served by nginx, which also proxies `/api` and `/reports`.
- **db** - Postgres 16 (schema managed by Alembic, demo data seeded on first start).

```
browser ──> nginx (web :8080) ──/api──────> FastAPI (:8000) ──> Postgres (:5432)
                              └─/reports──> Go reports (:8081) ──┘
                     FastAPI ──events──> Redis ──> Node notifier ──> mailbox table
```

## Tech stack

| Component | Stack |
| --- | --- |
| `services/api` | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, PyJWT, bcrypt, pytest |
| `services/reports` | Go 1.22, net/http, pgx v5, golang-jwt |
| `services/notifier` | Node.js 22, node-redis, node-postgres, `node:test` |
| `web` | Vue 3, Vite 5, Pinia, Vue Router 4, PrimeVue 4, Vitest |
| infrastructure | Docker Compose, Postgres 16, Redis 7, nginx |

## Prerequisites

- Docker Desktop / Docker Engine with Compose v2 (Docker 24+)

For running unit tests outside Docker (optional): Python 3.12, Go 1.22, Node.js 20+.

## Running

```bash
docker compose up --build
```

On Windows you can also use `./scripts/dev.ps1 up`; on Linux/macOS `make up`.

| URL | What |
| --- | --- |
| http://localhost:8080 | Web application |
| http://localhost:8000/api/docs | API (OpenAPI / Swagger UI) |
| http://localhost:8081/reports/health | Reports service |
| `localhost:5432` | Postgres (`payroll` / `payroll`) |

The API container applies migrations (`alembic upgrade head`) and loads demo data on first start.
Host ports can be changed with `WEB_PORT`, `API_PORT`, `REPORTS_PORT` and `DB_PORT`
(e.g. `WEB_PORT=9090 docker compose up --build`).

Stop with `docker compose down`; wipe the database with `docker compose down -v`.

## Demo accounts

Password for every account: `Passw0rd!`

| Email | Role |
| --- | --- |
| `admin@acme.test` | Admin - everything |
| `manager@acme.test` | Manager (Engineering) - approves/rejects Engineering timesheets, sees reports |
| `employee@acme.test` | Employee - own profile, payslips and timesheets |
| `grace.kim@acme.test` | Manager (Operations) |

## Screens

| Route | Screen | Roles |
| --- | --- | --- |
| `/login` | Sign in | all |
| `/dashboard` | Headcount, last payroll, pending timesheets, next pay date, cost by department | admin, manager |
| `/employees` | Search, department/status filters, sorting, pagination, create/edit/deactivate | admin (managers read-only) |
| `/employees/:id` | Profile, salary history with "Add raise", payslips | admin, manager |
| `/departments` | Department CRUD (departments with active employees cannot be deleted) | admin |
| `/timesheets` | All timesheets, status filter, approve / reject with reason | admin, manager |
| `/payruns`, `/payruns/:id` | Create pay run, calculate, review lines, approve, mark paid (locked) | admin (managers read-only) |
| `/payslips/:id` | Payslip breakdown, print view, CSV download | owner, admin, manager |
| `/reports` | Payroll cost by department for a period, CSV export (Go service) | admin, manager |
| `/settings` | Tax brackets and rates, users, audit log with filters | admin |
| `/my/payslips` | My payslips and notifications | everyone with an employee record |
| `/my/timesheets` | Weekly timesheets (7 days, 0-24 h), submit | everyone with an employee record |
| `/my/profile` | Phone, pension opt-in, salary history | everyone with an employee record |

## Payroll rules

- Salaried: monthly gross = annual salary / 12.
- Hourly: rate x regular hours + rate x 1.5 x overtime hours; overtime = hours above 40 in a week
  (approved timesheets whose week starts in the pay period).
- Income tax on monthly gross: 0-1000 at 0%, 1000-4000 at 15%, above 4000 at 25% (editable).
- Social contribution 5%, pension 3% when opted in, other fixed deductions (health insurance).
- Pay run lifecycle: Draft -> Calculated -> Approved -> Paid (paid runs are locked).

## Project structure

```
db/                 Postgres init scripts (extensions, read-only role)
services/api/       FastAPI app (app/), Alembic migrations, seed, pytest tests
services/reports/   Go reporting service (internal/auth, report, store, httpapi)
services/notifier/  Node worker consuming Redis events
web/                Vue 3 SPA + nginx config
scripts/dev.ps1     Windows helper (up, down, reset, logs, test)
Makefile            Same helpers for make
docker-compose.yml  Whole stack
```

## Tests

```bash
make test                      # or ./scripts/dev.ps1 test
cd services/api && pip install -r requirements-dev.txt && python -m pytest
cd services/reports && go test ./...
cd services/notifier && npm ci && npm test
cd web && npm ci && npm test
```

API tests run against an in-memory SQLite database, so no running services are needed.
CI (`.github/workflows/ci.yml`) runs one job per component, only when that component changed.
