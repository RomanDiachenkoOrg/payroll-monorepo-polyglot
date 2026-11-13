import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .errors import install_error_handlers
from .routers import auth, dashboard, departments, employees, me, payruns, payslips, settings as settings_router, timesheets

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Payroll API", version="1.4.0", docs_url="/api/docs", openapi_url="/api/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
install_error_handlers(app)


@app.get("/api/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}


for router in (
    auth.router,
    me.router,
    dashboard.router,
    departments.router,
    employees.router,
    timesheets.router,
    payruns.router,
    payslips.router,
    settings_router.router,
):
    app.include_router(router, prefix="/api")
