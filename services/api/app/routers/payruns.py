from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import CurrentUser, require_role
from ..errors import conflict, not_found
from ..mappers import pay_run_out, payslip_out
from ..models import PayRun, Payslip
from ..schemas import PayRunDetailOut, PayRunIn, PayRunOut
from ..services import audit, events
from ..services.payroll import calculate_pay_run

router = APIRouter(prefix="/payruns", tags=["pay runs"])

TRANSITIONS = {
    "DRAFT": {"CALCULATED"},
    "CALCULATED": {"CALCULATED", "APPROVED"},
    "APPROVED": {"PAID"},
    "PAID": set(),
}


def _get(db: Session, run_id: int) -> PayRun:
    run = db.get(PayRun, run_id)
    if not run:
        raise not_found("Pay run")
    return run


def _transition(run: PayRun, target: str) -> None:
    if target not in TRANSITIONS[run.status]:
        if run.status == "PAID":
            raise conflict("This pay run is paid and locked")
        raise conflict(f"Cannot move a pay run from {run.status.lower()} to {target.lower()}")


def _count(db: Session, run_id: int) -> int:
    return db.scalar(select(func.count(Payslip.id)).where(Payslip.pay_run_id == run_id)) or 0


@router.get("", response_model=list[PayRunOut])
def list_pay_runs(_: CurrentUser = Depends(require_role("ADMIN", "MANAGER")), db: Session = Depends(get_db)):
    counts = dict(db.execute(select(Payslip.pay_run_id, func.count(Payslip.id)).group_by(Payslip.pay_run_id)).all())
    runs = db.scalars(select(PayRun).order_by(PayRun.period_start.desc())).all()
    return [pay_run_out(r, counts.get(r.id, 0)) for r in runs]


@router.get("/{run_id}", response_model=PayRunDetailOut)
def get_pay_run(run_id: int, _: CurrentUser = Depends(require_role("ADMIN", "MANAGER")), db: Session = Depends(get_db)):
    run = _get(db, run_id)
    lines = sorted(
        (payslip_out(p) for p in db.scalars(select(Payslip).where(Payslip.pay_run_id == run.id)).all()),
        key=lambda p: (p.department_name, p.employee_name),
    )
    return PayRunDetailOut(**pay_run_out(run, len(lines)).model_dump(), lines=lines)


@router.post("", response_model=PayRunOut, status_code=201)
def create_pay_run(body: PayRunIn, user: CurrentUser = Depends(require_role("ADMIN")), db: Session = Depends(get_db)):
    overlap = db.scalar(select(PayRun).where(PayRun.period_start <= body.period_end, PayRun.period_end >= body.period_start))
    if overlap:
        raise conflict(
            f"The period overlaps pay run #{overlap.id} ({overlap.period_start} to {overlap.period_end})",
            {"periodStart": "Overlaps an existing pay run"},
        )
    run = PayRun(**body.model_dump(), status="DRAFT")
    db.add(run)
    db.flush()
    audit.record(db, user, "CREATE", "PayRun", run.id, f"{run.period_start} to {run.period_end}")
    db.commit()
    db.refresh(run)
    return pay_run_out(run)


@router.post("/{run_id}/calculate", response_model=PayRunOut)
def calculate(run_id: int, user: CurrentUser = Depends(require_role("ADMIN")), db: Session = Depends(get_db)):
    run = _get(db, run_id)
    _transition(run, "CALCULATED")
    summary = calculate_pay_run(db, run)
    audit.record(db, user, "CALCULATE", "PayRun", run.id, summary)
    db.commit()
    return pay_run_out(run, _count(db, run.id))


@router.post("/{run_id}/approve", response_model=PayRunOut)
def approve(run_id: int, user: CurrentUser = Depends(require_role("ADMIN")), db: Session = Depends(get_db)):
    run = _get(db, run_id)
    _transition(run, "APPROVED")
    run.status = "APPROVED"
    run.approved_at = datetime.now(UTC)
    audit.record(db, user, "APPROVE", "PayRun", run.id)
    db.commit()
    events.publish("payrun.approved", payRunId=run.id)
    return pay_run_out(run, _count(db, run.id))


@router.post("/{run_id}/pay", response_model=PayRunOut)
def mark_paid(run_id: int, user: CurrentUser = Depends(require_role("ADMIN")), db: Session = Depends(get_db)):
    run = _get(db, run_id)
    _transition(run, "PAID")
    run.status = "PAID"
    run.paid_at = datetime.now(UTC)
    audit.record(db, user, "MARK_PAID", "PayRun", run.id)
    db.commit()
    return pay_run_out(run, _count(db, run.id))


@router.delete("/{run_id}", status_code=204)
def delete_pay_run(run_id: int, user: CurrentUser = Depends(require_role("ADMIN")), db: Session = Depends(get_db)):
    run = _get(db, run_id)
    if run.status not in ("DRAFT", "CALCULATED"):
        raise conflict("Only draft or calculated pay runs can be deleted")
    db.delete(run)
    audit.record(db, user, "DELETE", "PayRun", run_id)
    db.commit()
    return Response(status_code=204)
