from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import CurrentUser, current_user
from ..errors import not_found
from ..mappers import employee_out, payslip_out
from ..models import Employee, MailboxMessage, PayRun, Payslip
from ..schemas import EmployeeDetailOut, EmployeeOut, MailOut, PayslipOut, ProfileIn, SalaryHistoryOut
from ..services import audit

router = APIRouter(prefix="/me", tags=["me"])


def _employee(db: Session, user: CurrentUser) -> Employee:
    if not user.employee_id:
        raise not_found("Employee profile")
    e = db.get(Employee, user.employee_id)
    if not e:
        raise not_found("Employee profile")
    return e


@router.get("/profile", response_model=EmployeeDetailOut)
def profile(user: CurrentUser = Depends(current_user), db: Session = Depends(get_db)):
    e = _employee(db, user)
    return EmployeeDetailOut(
        **employee_out(e).model_dump(),
        salary_history=[SalaryHistoryOut.model_validate(s) for s in e.salary_history],
        payslips=[],
    )


@router.put("/profile", response_model=EmployeeOut)
def update_profile(body: ProfileIn, user: CurrentUser = Depends(current_user), db: Session = Depends(get_db)):
    e = _employee(db, user)
    changes = body.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(e, k, v)
    audit.record(db, user, "UPDATE_PROFILE", "Employee", e.id, {"fields": list(changes)})
    db.commit()
    db.refresh(e)
    return employee_out(e)


@router.get("/payslips", response_model=list[PayslipOut])
def my_payslips(user: CurrentUser = Depends(current_user), db: Session = Depends(get_db)):
    if not user.employee_id:
        return []
    rows = db.scalars(
        select(Payslip)
        .join(PayRun)
        .where(Payslip.employee_id == user.employee_id, PayRun.status.in_(["APPROVED", "PAID"]))
        .order_by(PayRun.period_start.desc())
    ).all()
    return [payslip_out(p) for p in rows]


@router.get("/mailbox", response_model=list[MailOut])
def my_mailbox(user: CurrentUser = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(MailboxMessage).where(MailboxMessage.recipient == user.email).order_by(MailboxMessage.created_at.desc()).limit(50)
    ).all()
    return [MailOut.model_validate(m) for m in rows]
