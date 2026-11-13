from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..models import Employee, PayRun, Payslip, Timesheet
from .calc import calculate
from .settings_store import load_config


def calculate_pay_run(db: Session, run: PayRun) -> dict:
    config = load_config(db)
    employees = db.scalars(
        select(Employee).where(Employee.status == "ACTIVE", Employee.hire_date <= run.period_end)
    ).all()

    db.execute(delete(Payslip).where(Payslip.pay_run_id == run.id))
    total_gross = total_net = Decimal("0")
    count = 0
    for e in employees:
        weeks: list[list[float]] = []
        if e.pay_type == "HOURLY":
            sheets = db.scalars(
                select(Timesheet).where(
                    Timesheet.employee_id == e.id,
                    Timesheet.status == "APPROVED",
                    Timesheet.week_start >= run.period_start,
                    Timesheet.week_start <= run.period_end,
                )
            ).all()
            weeks = [t.hours for t in sheets]
            if not weeks:
                continue
        b = calculate(
            pay_type=e.pay_type,
            annual_salary=e.annual_salary,
            hourly_rate=e.hourly_rate,
            weeks=weeks,
            pension_opt_in=e.pension_opt_in,
            other_deductions=e.other_deductions,
            config=config,
        )
        db.add(
            Payslip(
                pay_run_id=run.id,
                employee_id=e.id,
                pay_type=e.pay_type,
                regular_hours=b.regular_hours,
                overtime_hours=b.overtime_hours,
                gross=b.gross,
                tax=b.tax,
                social=b.social,
                pension=b.pension,
                other=b.other,
                net=b.net,
            )
        )
        total_gross += b.gross
        total_net += b.net
        count += 1

    run.status = "CALCULATED"
    run.total_gross = total_gross
    run.total_net = total_net
    run.calculated_at = datetime.now(UTC)
    return {"employees": count, "gross": str(total_gross), "net": str(total_net)}
