"""Loads demo data into an empty database.

Run with ``python -m app.seed``. Does nothing when users already exist.
"""
from __future__ import annotations

import calendar
import json
import logging
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import (
    AuditLog,
    DeductionType,
    Department,
    Employee,
    EmployeeDeduction,
    PayRun,
    Payslip,
    SalaryHistory,
    Setting,
    TaxBracket,
    Timesheet,
    TimesheetEntry,
    User,
)
from .security import hash_password
from .services.calc import DEFAULT_BRACKETS, calculate

log = logging.getLogger("seed")

DEMO_PASSWORD = "Passw0rd!"

DEPARTMENTS = [
    ("Engineering", "ENG", "Michael Brooks"),
    ("Finance", "FIN", "Laura Chen"),
    ("Sales", "SAL", "Daniel Ortiz"),
    ("Operations", "OPS", "Grace Kim"),
    ("HR", "HR", "Alice Morgan"),
]

# first, last, email, title, department, pay type, amount, hired, pension, health, status
EMPLOYEES = [
    ("Michael", "Brooks", "manager@acme.test", "Engineering Manager", "Engineering", "SALARIED", 118000, "2019-03-11", True, 140, "ACTIVE"),
    ("Priya", "Natarajan", None, "Senior Software Engineer", "Engineering", "SALARIED", 104000, "2020-06-01", True, 140, "ACTIVE"),
    ("Tom", "Fischer", None, "Software Engineer", "Engineering", "SALARIED", 86000, "2022-09-19", False, 90, "ACTIVE"),
    ("Emily", "Carter", "employee@acme.test", "Support Engineer", "Engineering", "HOURLY", 32, "2023-02-06", True, 90, "ACTIVE"),
    ("Jonas", "Weber", None, "DevOps Engineer", "Engineering", "SALARIED", 97000, "2021-11-15", False, 140, "ACTIVE"),
    ("Sara", "Lindqvist", None, "Frontend Developer", "Engineering", "SALARIED", 78000, "2024-04-02", False, 0, "ACTIVE"),
    ("Kevin", "O'Neill", None, "Junior Developer", "Engineering", "HOURLY", 26.5, "2025-08-04", False, 0, "ACTIVE"),
    ("Laura", "Chen", None, "Finance Director", "Finance", "SALARIED", 125000, "2018-01-08", True, 140, "ACTIVE"),
    ("Robert", "Hughes", None, "Accountant", "Finance", "SALARIED", 60150, "2021-05-17", True, 90, "ACTIVE"),
    ("Nina", "Petrova", None, "Payroll Specialist", "Finance", "SALARIED", 58000, "2022-02-14", False, 90, "ACTIVE"),
    ("George", "Adams", None, "Accounts Clerk", "Finance", "HOURLY", 21, "2020-10-05", False, 0, "INACTIVE"),
    ("Daniel", "Ortiz", None, "Head of Sales", "Sales", "SALARIED", 110000, "2019-07-22", True, 140, "ACTIVE"),
    ("Hannah", "Schmidt", None, "Account Executive", "Sales", "SALARIED", 72000, "2021-03-01", False, 90, "ACTIVE"),
    ("Marcus", "Johnson", None, "Account Executive", "Sales", "SALARIED", 70000, "2022-06-13", True, 0, "ACTIVE"),
    ("Olivia", "Rossi", None, "Sales Development Rep", "Sales", "HOURLY", 24, "2024-01-15", False, 60, "ACTIVE"),
    ("Ethan", "Walker", None, "Sales Development Rep", "Sales", "HOURLY", 23, "2023-09-11", False, 0, "ACTIVE"),
    ("Chloe", "Dubois", None, "Sales Coordinator", "Sales", "SALARIED", 52000, "2020-02-03", False, 0, "INACTIVE"),
    ("Grace", "Kim", None, "Operations Manager", "Operations", "SALARIED", 92000, "2019-09-30", True, 140, "ACTIVE"),
    ("Luis", "Fernandez", None, "Warehouse Lead", "Operations", "HOURLY", 27, "2020-04-20", True, 90, "ACTIVE"),
    ("Aisha", "Bello", None, "Logistics Coordinator", "Operations", "HOURLY", 22.75, "2022-11-07", False, 60, "ACTIVE"),
    ("Peter", "Novak", None, "Facilities Technician", "Operations", "HOURLY", 25, "2021-08-16", False, 0, "ACTIVE"),
    ("Yuki", "Tanaka", None, "Procurement Analyst", "Operations", "SALARIED", 61000, "2023-05-22", False, 90, "ACTIVE"),
    ("Alice", "Morgan", "admin@acme.test", "HR Director", "HR", "SALARIED", 99000, "2018-05-14", True, 140, "ACTIVE"),
    ("Ben", "Clarke", None, "HR Generalist", "HR", "SALARIED", 56000, "2022-01-10", False, 90, "ACTIVE"),
    ("Fatima", "Haddad", None, "Recruiter", "HR", "SALARIED", 60000, "2021-10-04", False, 0, "INACTIVE"),
]

NORMAL_WEEK = [8, 8, 8, 8, 8, 0, 0]
BUSY_WEEK = [9, 9, 9, 9, 8, 3, 0]
SHORT_WEEK = [8, 8, 6, 8, 4, 0, 0]


def month_bounds(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    idx = year * 12 + (month - 1) + delta
    return idx // 12, idx % 12 + 1


def mondays(start: date, end: date) -> list[date]:
    d = start + timedelta(days=(7 - start.weekday()) % 7)
    out = []
    while d <= end:
        out.append(d)
        d += timedelta(days=7)
    return out


def email_for(first: str, last: str, explicit: str | None) -> str:
    if explicit:
        return explicit
    clean = "".join(ch for ch in f"{first}.{last}".lower() if ch.isalpha() or ch == ".")
    return f"{clean}@acme.test"


def seed(db: Session, today: date | None = None) -> bool:
    if db.scalar(select(func.count(User.id))):
        return False
    today = today or date.today()

    for i, b in enumerate(DEFAULT_BRACKETS):
        db.add(TaxBracket(sort_order=i, lower=b.lower, upper=b.upper, rate=b.rate))
    db.add_all([Setting(key="social_rate", value="0.05"), Setting(key="pension_rate", value="0.03"), Setting(key="currency", value="USD")])
    health = DeductionType(code="HEALTH", name="Health insurance", default_amount=Decimal("90"))
    db.add_all([health, DeductionType(code="UNION", name="Union dues", default_amount=Decimal("15"), is_active=False)])

    depts = {}
    for name, code, mgr in DEPARTMENTS:
        d = Department(name=name, code=code, manager_name=mgr)
        db.add(d)
        depts[name] = d
    db.flush()

    employees: list[Employee] = []
    for first, last, email, title, dept, pay_type, amount, hired, pension, health_amt, status in EMPLOYEES:
        amount = Decimal(str(amount))
        salaried = pay_type == "SALARIED"
        e = Employee(
            first_name=first,
            last_name=last,
            email=email_for(first, last, email),
            phone=f"+1 555 02{len(employees):02d}",
            title=title,
            department_id=depts[dept].id,
            pay_type=pay_type,
            annual_salary=amount if salaried else None,
            hourly_rate=None if salaried else amount,
            pension_opt_in=pension,
            hire_date=date.fromisoformat(hired),
            status=status,
        )
        start_amount = (amount * Decimal("0.94")).quantize(Decimal("1") if salaried else Decimal("0.01"))
        e.salary_history.append(
            SalaryHistory(
                effective_date=e.hire_date,
                annual_salary=start_amount if salaried else None,
                hourly_rate=None if salaried else start_amount,
                reason="Starting salary",
            )
        )
        e.salary_history.append(
            SalaryHistory(
                effective_date=date(today.year, 1, 1),
                annual_salary=amount if salaried else None,
                hourly_rate=None if salaried else amount,
                reason="Annual review",
            )
        )
        db.add(e)
        db.flush()
        if health_amt:
            db.add(EmployeeDeduction(employee_id=e.id, deduction_type_id=health.id, amount=Decimal(health_amt)))
        employees.append(e)
    db.flush()

    by_email = {e.email: e for e in employees}
    pw = hash_password(DEMO_PASSWORD)
    admin = User(email="admin@acme.test", password_hash=pw, full_name="Alice Morgan", role="ADMIN", employee_id=by_email["admin@acme.test"].id, department_id=depts["HR"].id)
    manager = User(email="manager@acme.test", password_hash=pw, full_name="Michael Brooks", role="MANAGER", employee_id=by_email["manager@acme.test"].id, department_id=depts["Engineering"].id)
    employee = User(email="employee@acme.test", password_hash=pw, full_name="Emily Carter", role="EMPLOYEE", employee_id=by_email["employee@acme.test"].id, department_id=depts["Engineering"].id)
    ops = User(email="grace.kim@acme.test", password_hash=pw, full_name="Grace Kim", role="MANAGER", employee_id=by_email["grace.kim@acme.test"].id, department_id=depts["Operations"].id)
    db.add_all([admin, manager, employee, ops])
    db.flush()

    hourly = [e for e in employees if e.pay_type == "HOURLY" and e.status == "ACTIVE"]
    approver = {depts["Engineering"].id: manager.id, depts["Operations"].id: ops.id}

    def add_sheet(e: Employee, monday: date, pattern: list[int], status: str, reason: str | None = None) -> None:
        decided = status in ("APPROVED", "REJECTED")
        t = Timesheet(
            employee_id=e.id,
            week_start=monday,
            status=status,
            reject_reason=reason,
            notes="Includes on-call Saturday" if reason else None,
            submitted_at=None if status == "DRAFT" else datetime.combine(monday + timedelta(days=4), datetime.min.time(), UTC),
            decided_at=datetime.combine(monday + timedelta(days=7), datetime.min.time(), UTC) if decided else None,
            decided_by_id=approver.get(e.department_id, admin.id) if decided else None,
        )
        t.entries = [TimesheetEntry(day_index=i, hours=Decimal(h)) for i, h in enumerate(pattern)]
        db.add(t)

    periods = [shift_month(today.year, today.month, -2), shift_month(today.year, today.month, -1)]
    latest_monday = today - timedelta(days=today.weekday())
    for y, m in periods:
        start, end = month_bounds(y, m)
        for i, monday in enumerate(mondays(start, end)):
            if monday == latest_monday:
                continue
            for j, e in enumerate(hourly):
                if e.hire_date > monday:
                    continue
                pattern = BUSY_WEEK if (i + j) % 3 == 0 else SHORT_WEEK if (i + j) % 4 == 1 else NORMAL_WEEK
                add_sheet(e, monday, pattern, "APPROVED")

    cur_start, cur_end = month_bounds(today.year, today.month)
    current = [m for m in mondays(cur_start, cur_end) if m <= today]
    if latest_monday not in current:
        current.append(latest_monday)
    states = ["SUBMITTED", "SUBMITTED", "DRAFT", "REJECTED", "APPROVED"]
    for j, e in enumerate(hourly):
        for i, monday in enumerate(current):
            status = states[j % len(states)] if i == len(current) - 1 else "APPROVED"
            add_sheet(e, monday, NORMAL_WEEK if j % 2 == 0 else BUSY_WEEK, status, "Saturday on-call hours need a ticket reference" if status == "REJECTED" else None)
    db.flush()

    for y, m in periods:
        start, end = month_bounds(y, m)
        paid_at = datetime.combine(end, datetime.min.time(), UTC) + timedelta(hours=9)
        run = PayRun(period_start=start, period_end=end, pay_date=end, status="PAID", calculated_at=paid_at, approved_at=paid_at, paid_at=paid_at)
        db.add(run)
        db.flush()
        gross_total = net_total = Decimal("0")
        for e in employees:
            if e.status != "ACTIVE" or e.hire_date > end:
                continue
            weeks = []
            if e.pay_type == "HOURLY":
                sheets = db.scalars(
                    select(Timesheet).where(
                        Timesheet.employee_id == e.id, Timesheet.status == "APPROVED", Timesheet.week_start >= start, Timesheet.week_start <= end
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
                other_deductions=sum((d.amount for d in db.scalars(select(EmployeeDeduction).where(EmployeeDeduction.employee_id == e.id))), Decimal("0")),
            )
            db.add(
                Payslip(
                    pay_run_id=run.id, employee_id=e.id, pay_type=e.pay_type, regular_hours=b.regular_hours, overtime_hours=b.overtime_hours,
                    gross=b.gross, tax=b.tax, social=b.social, pension=b.pension, other=b.other, net=b.net,
                )
            )
            gross_total += b.gross
            net_total += b.net
        run.total_gross = gross_total
        run.total_net = net_total
        for action, minutes in (("CREATE", 0), ("CALCULATE", 10), ("APPROVE", 30), ("MARK_PAID", 60)):
            db.add(
                AuditLog(
                    user_id=admin.id, user_email=admin.email, action=action, entity="PayRun", entity_id=str(run.id),
                    details=f"{start} to {end}" if action == "CREATE" else None, created_at=paid_at - timedelta(minutes=60 - minutes),
                )
            )

    draft = PayRun(period_start=cur_start, period_end=cur_end, pay_date=cur_end, status="DRAFT")
    db.add(draft)
    db.flush()
    db.add_all(
        [
            AuditLog(user_id=admin.id, user_email=admin.email, action="CREATE", entity="PayRun", entity_id=str(draft.id), details=f"{cur_start} to {cur_end}"),
            AuditLog(user_id=admin.id, user_email=admin.email, action="DEACTIVATE", entity="Employee", entity_id=str(by_email["george.adams@acme.test"].id), details="George Adams"),
            AuditLog(user_id=admin.id, user_email=admin.email, action="SALARY_CHANGE", entity="Employee", entity_id=str(by_email["tom.fischer@acme.test"].id), details=json.dumps({"amount": "86000", "effective": f"{today.year}-01-01"})),
            AuditLog(user_id=manager.id, user_email=manager.email, action="REJECT", entity="Timesheet", details="Saturday on-call hours need a ticket reference"),
            AuditLog(user_id=admin.id, user_email=admin.email, action="UPDATE", entity="TaxSettings", details="Initial tax configuration"),
        ]
    )
    db.commit()
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    with SessionLocal() as db:
        if seed(db):
            log.info("Demo data loaded: %d employees, %d departments", len(EMPLOYEES), len(DEPARTMENTS))
        else:
            log.info("Database already contains data, skipping seed")


if __name__ == "__main__":
    main()
