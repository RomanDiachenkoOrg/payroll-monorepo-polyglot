import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import CurrentUser, current_user
from ..errors import forbidden, not_found
from ..mappers import payslip_out
from ..models import Payslip
from ..schemas import PayslipOut

router = APIRouter(prefix="/payslips", tags=["payslips"])

RELEASED = ("APPROVED", "PAID")


def _load(db: Session, user: CurrentUser, slip_id: int) -> PayslipOut:
    p = db.get(Payslip, slip_id)
    if not p:
        raise not_found("Payslip")
    own = user.employee_id == p.employee_id
    if user.role == "EMPLOYEE" or (user.role == "MANAGER" and own):
        if not own or p.pay_run.status not in RELEASED:
            raise not_found("Payslip")
    elif user.role == "MANAGER" and p.employee.department_id != user.department_id:
        raise forbidden("You can only view payslips of your department")
    return payslip_out(p)


@router.get("/{slip_id}", response_model=PayslipOut)
def get_payslip(slip_id: int, user: CurrentUser = Depends(current_user), db: Session = Depends(get_db)):
    return _load(db, user, slip_id)


def payslip_csv(p: PayslipOut) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(["Item", "Value"])
    w.writerow(["Employee", p.employee_name])
    w.writerow(["Department", p.department_name])
    w.writerow(["Period", f"{p.period_start} to {p.period_end}"])
    w.writerow(["Pay date", p.pay_date])
    if p.pay_type == "HOURLY":
        w.writerow(["Regular hours", p.regular_hours])
        w.writerow(["Overtime hours", p.overtime_hours])
    for label, value in (
        ("Gross pay", p.gross),
        ("Income tax", p.tax),
        ("Social contribution", p.social),
        ("Pension", p.pension),
        ("Other deductions", p.other),
        ("Net pay", p.net),
    ):
        w.writerow([label, f"{value:.2f}"])
    return buf.getvalue()


@router.get("/{slip_id}/csv")
def export_csv(slip_id: int, user: CurrentUser = Depends(current_user), db: Session = Depends(get_db)):
    p = _load(db, user, slip_id)
    name = f"payslip-{p.period_start:%Y-%m}-{p.employee_name.lower().replace(' ', '-')}.csv"
    return Response(
        content=payslip_csv(p),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )
