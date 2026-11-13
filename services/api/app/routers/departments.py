from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import CurrentUser, current_user, require_role
from ..errors import conflict, not_found
from ..models import Department, Employee, User
from ..schemas import DepartmentIn, DepartmentOut
from ..services import audit

router = APIRouter(prefix="/departments", tags=["departments"])


def _out(db: Session, d: Department) -> DepartmentOut:
    rows = dict(
        db.execute(
            select(Employee.status, func.count(Employee.id)).where(Employee.department_id == d.id).group_by(Employee.status)
        ).all()
    )
    return DepartmentOut(
        id=d.id,
        name=d.name,
        code=d.code,
        manager_name=d.manager_name,
        active_employees=rows.get("ACTIVE", 0),
        total_employees=sum(rows.values()),
    )


def _ensure_unique(db: Session, body: DepartmentIn, except_id: int | None = None) -> None:
    q = select(Department).where(or_(Department.name == body.name, Department.code == body.code))
    if except_id:
        q = q.where(Department.id != except_id)
    clash = db.scalar(q)
    if clash:
        errors = {}
        if clash.name == body.name:
            errors["name"] = "A department with this name already exists"
        if clash.code == body.code:
            errors["code"] = "This code is already used"
        raise conflict("Department already exists", errors)


@router.get("", response_model=list[DepartmentOut])
def list_departments(_: CurrentUser = Depends(current_user), db: Session = Depends(get_db)):
    return [_out(db, d) for d in db.scalars(select(Department).order_by(Department.name)).all()]


@router.post("", response_model=DepartmentOut, status_code=201)
def create_department(body: DepartmentIn, user: CurrentUser = Depends(require_role("ADMIN")), db: Session = Depends(get_db)):
    _ensure_unique(db, body)
    d = Department(**body.model_dump())
    db.add(d)
    db.flush()
    audit.record(db, user, "CREATE", "Department", d.id, d.name)
    db.commit()
    return _out(db, d)


@router.put("/{dept_id}", response_model=DepartmentOut)
def update_department(dept_id: int, body: DepartmentIn, user: CurrentUser = Depends(require_role("ADMIN")), db: Session = Depends(get_db)):
    d = db.get(Department, dept_id)
    if not d:
        raise not_found("Department")
    _ensure_unique(db, body, dept_id)
    for k, v in body.model_dump().items():
        setattr(d, k, v)
    audit.record(db, user, "UPDATE", "Department", d.id, d.name)
    db.commit()
    return _out(db, d)


@router.delete("/{dept_id}", status_code=204)
def delete_department(dept_id: int, user: CurrentUser = Depends(require_role("ADMIN")), db: Session = Depends(get_db)):
    d = db.get(Department, dept_id)
    if not d:
        raise not_found("Department")
    active = db.scalar(select(func.count(Employee.id)).where(Employee.department_id == d.id, Employee.status == "ACTIVE")) or 0
    if active:
        raise conflict(f"Cannot delete {d.name}: it still has {active} active employee{'s' if active != 1 else ''}.")
    others = db.scalar(select(func.count(Employee.id)).where(Employee.department_id == d.id)) or 0
    if others:
        raise conflict(f"Cannot delete {d.name}: move its {others} former employee record(s) to another department first.")
    for u in db.scalars(select(User).where(User.department_id == d.id)).all():
        u.department_id = None
    db.delete(d)
    audit.record(db, user, "DELETE", "Department", dept_id, d.name)
    db.commit()
    return Response(status_code=204)
