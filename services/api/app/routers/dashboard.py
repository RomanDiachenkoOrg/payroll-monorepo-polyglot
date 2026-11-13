from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import CurrentUser, require_role
from ..mappers import pay_run_out
from ..models import Department, Employee, PayRun, Payslip, Timesheet
from ..schemas import DashboardOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def dashboard(user: CurrentUser = Depends(require_role("ADMIN", "MANAGER")), db: Session = Depends(get_db)):
    headcount = db.scalar(select(func.count(Employee.id))) or 0
    active = db.scalar(select(func.count(Employee.id)).where(Employee.status == "ACTIVE")) or 0
    pending_q = select(func.count(Timesheet.id)).where(Timesheet.status == "SUBMITTED")
    if user.role == "MANAGER":
        pending_q = pending_q.join(Employee).where(Employee.department_id == user.department_id)
    pending = db.scalar(pending_q) or 0

    last_paid = db.scalar(select(PayRun).where(PayRun.status == "PAID").order_by(PayRun.period_end.desc()).limit(1))
    upcoming = db.scalar(
        select(PayRun).where(PayRun.status != "PAID", PayRun.pay_date >= date.today()).order_by(PayRun.pay_date).limit(1)
    )
    cost: list[dict] = []
    if last_paid:
        rows = db.execute(
            select(Department.name, func.sum(Payslip.gross))
            .join(Employee, Employee.department_id == Department.id)
            .join(Payslip, Payslip.employee_id == Employee.id)
            .where(Payslip.pay_run_id == last_paid.id)
            .group_by(Department.name)
            .order_by(func.sum(Payslip.gross).desc())
        ).all()
        cost = [{"department": name, "gross": float(total)} for name, total in rows]

    recent = db.scalars(select(PayRun).order_by(PayRun.period_start.desc()).limit(5)).all()
    counts = dict(
        db.execute(select(Payslip.pay_run_id, func.count(Payslip.id)).group_by(Payslip.pay_run_id)).all()
    )
    return DashboardOut(
        headcount=headcount,
        active_headcount=active,
        last_payroll_gross=last_paid.total_gross if last_paid else None,
        last_payroll_period=f"{last_paid.period_start} to {last_paid.period_end}" if last_paid else None,
        pending_timesheets=pending,
        next_pay_date=upcoming.pay_date if upcoming else None,
        cost_by_department=cost,
        recent_pay_runs=[pay_run_out(r, counts.get(r.id, 0)) for r in recent],
    )
