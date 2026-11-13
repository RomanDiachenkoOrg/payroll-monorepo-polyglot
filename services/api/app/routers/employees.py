import math
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import CurrentUser, require_role
from ..errors import bad_request, conflict, not_found
from ..mappers import employee_out, payslip_out
from ..models import Department, DeductionType, Employee, EmployeeDeduction, PayRun, Payslip, SalaryHistory, User
from ..schemas import EmployeeDetailOut, EmployeeIn, EmployeeOut, Page, SalaryChangeIn, SalaryHistoryOut
from ..services import audit

router = APIRouter(prefix="/employees", tags=["employees"])

SORTS = {
    "name": (Employee.last_name, Employee.first_name),
    "email": (Employee.email,),
    "department": (Department.name, Employee.last_name),
    "title": (Employee.title,),
    "hireDate": (Employee.hire_date,),
    "status": (Employee.status, Employee.last_name),
}


def _get(db: Session, emp_id: int) -> Employee:
    e = db.get(Employee, emp_id)
    if not e:
        raise not_found("Employee")
    return e


def _check(db: Session, body: EmployeeIn, except_id: int | None = None) -> None:
    clash = db.scalar(select(Employee).where(Employee.email == body.email))
    if clash and clash.id != except_id:
        raise conflict("Email is already in use", {"email": "Email is already in use by another employee"})
    if not db.get(Department, body.department_id):
        raise bad_request("Unknown department", {"departmentId": "Select a valid department"})


def _set_health(db: Session, e: Employee, amount) -> None:
    dtype = db.scalar(select(DeductionType).where(DeductionType.code == "HEALTH"))
    if not dtype:
        return
    existing = next((d for d in e.deductions if d.deduction_type_id == dtype.id), None)
    if amount and amount > 0:
        if existing:
            existing.amount = amount
        else:
            e.deductions.append(EmployeeDeduction(deduction_type_id=dtype.id, amount=amount))
    elif existing:
        e.deductions.remove(existing)


@router.get("", response_model=Page[EmployeeOut])
def list_employees(
    q: str | None = None,
    department_id: int | None = Query(default=None, alias="departmentId"),
    status: Literal["ACTIVE", "INACTIVE", "ALL"] = "ALL",
    sort_by: str = Query(default="name", alias="sortBy"),
    sort_dir: Literal["asc", "desc"] = Query(default="asc", alias="sortDir"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100, alias="pageSize"),
    _: CurrentUser = Depends(require_role("ADMIN", "MANAGER")),
    db: Session = Depends(get_db),
):
    stmt = select(Employee).join(Department)
    if q:
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Employee.first_name).like(like),
                func.lower(Employee.last_name).like(like),
                func.lower(Employee.email).like(like),
                func.lower(Employee.title).like(like),
            )
        )
    if department_id:
        stmt = stmt.where(Employee.department_id == department_id)
    if status != "ALL":
        stmt = stmt.where(Employee.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    cols = SORTS.get(sort_by, SORTS["name"])
    order = [c.desc() if sort_dir == "desc" else c.asc() for c in cols]
    rows = db.scalars(stmt.order_by(*order, Employee.id).offset((page - 1) * page_size).limit(page_size)).unique().all()
    return Page[EmployeeOut](
        items=[employee_out(e) for e in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size),
    )


@router.get("/options")
def employee_options(_: CurrentUser = Depends(require_role("ADMIN", "MANAGER")), db: Session = Depends(get_db)):
    rows = db.scalars(select(Employee).where(Employee.status == "ACTIVE").order_by(Employee.last_name)).unique().all()
    return [{"id": e.id, "name": e.full_name, "departmentId": e.department_id} for e in rows]


@router.get("/{emp_id}", response_model=EmployeeDetailOut)
def get_employee(emp_id: int, _: CurrentUser = Depends(require_role("ADMIN", "MANAGER")), db: Session = Depends(get_db)):
    e = _get(db, emp_id)
    slips = db.scalars(
        select(Payslip).join(PayRun).where(Payslip.employee_id == e.id).order_by(PayRun.period_start.desc())
    ).all()
    return EmployeeDetailOut(
        **employee_out(e).model_dump(),
        salary_history=[SalaryHistoryOut.model_validate(s) for s in e.salary_history],
        payslips=[payslip_out(p) for p in slips],
    )


@router.post("", response_model=EmployeeOut, status_code=201)
def create_employee(body: EmployeeIn, user: CurrentUser = Depends(require_role("ADMIN")), db: Session = Depends(get_db)):
    _check(db, body)
    data = body.model_dump(exclude={"health_insurance"})
    e = Employee(**data, status="ACTIVE")
    e.salary_history.append(
        SalaryHistory(effective_date=body.hire_date, annual_salary=body.annual_salary, hourly_rate=body.hourly_rate, reason="Starting salary")
    )
    db.add(e)
    db.flush()
    _set_health(db, e, body.health_insurance)
    audit.record(db, user, "CREATE", "Employee", e.id, e.full_name)
    db.commit()
    db.refresh(e)
    return employee_out(e)


@router.put("/{emp_id}", response_model=EmployeeOut)
def update_employee(emp_id: int, body: EmployeeIn, user: CurrentUser = Depends(require_role("ADMIN")), db: Session = Depends(get_db)):
    e = _get(db, emp_id)
    _check(db, body, emp_id)
    for k, v in body.model_dump(exclude={"health_insurance"}).items():
        setattr(e, k, v)
    _set_health(db, e, body.health_insurance)
    audit.record(db, user, "UPDATE", "Employee", e.id, e.full_name)
    db.commit()
    db.refresh(e)
    return employee_out(e)


@router.post("/{emp_id}/deactivate", response_model=EmployeeOut)
def deactivate(emp_id: int, user: CurrentUser = Depends(require_role("ADMIN")), db: Session = Depends(get_db)):
    e = _get(db, emp_id)
    if e.status == "INACTIVE":
        raise conflict("Employee is already inactive")
    e.status = "INACTIVE"
    for u in db.scalars(select(User).where(User.employee_id == e.id)).all():
        u.is_active = False
    audit.record(db, user, "DEACTIVATE", "Employee", e.id, e.full_name)
    db.commit()
    return employee_out(e)


@router.post("/{emp_id}/activate", response_model=EmployeeOut)
def activate(emp_id: int, user: CurrentUser = Depends(require_role("ADMIN")), db: Session = Depends(get_db)):
    e = _get(db, emp_id)
    e.status = "ACTIVE"
    for u in db.scalars(select(User).where(User.employee_id == e.id)).all():
        u.is_active = True
    audit.record(db, user, "ACTIVATE", "Employee", e.id, e.full_name)
    db.commit()
    return employee_out(e)


@router.post("/{emp_id}/salary", response_model=SalaryHistoryOut, status_code=201)
def add_salary_change(emp_id: int, body: SalaryChangeIn, user: CurrentUser = Depends(require_role("ADMIN")), db: Session = Depends(get_db)):
    e = _get(db, emp_id)
    entry = SalaryHistory(
        employee_id=e.id,
        effective_date=body.effective_date,
        annual_salary=body.amount if e.pay_type == "SALARIED" else None,
        hourly_rate=body.amount if e.pay_type == "HOURLY" else None,
        reason=body.reason,
    )
    db.add(entry)
    if body.effective_date <= date.today():
        if e.pay_type == "SALARIED":
            e.annual_salary = body.amount
        else:
            e.hourly_rate = body.amount
    audit.record(db, user, "SALARY_CHANGE", "Employee", e.id, {"amount": body.amount, "effective": body.effective_date})
    db.commit()
    return SalaryHistoryOut.model_validate(entry)
