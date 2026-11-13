from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Response
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import CurrentUser, current_user, require_role
from ..errors import bad_request, conflict, forbidden, not_found
from ..mappers import timesheet_out
from ..models import Employee, Timesheet, TimesheetEntry
from ..schemas import RejectIn, TimesheetIn, TimesheetOut, TimesheetUpdateIn
from ..services import audit, events

router = APIRouter(prefix="/timesheets", tags=["timesheets"])


def _scoped(stmt, user: CurrentUser):
    if user.role == "ADMIN":
        return stmt
    if user.role == "MANAGER":
        return stmt.join(Employee, Employee.id == Timesheet.employee_id).where(
            or_(Employee.department_id == user.department_id, Timesheet.employee_id == user.employee_id)
        )
    return stmt.where(Timesheet.employee_id == user.employee_id)


def _load(db: Session, user: CurrentUser, ts_id: int) -> Timesheet:
    t = db.scalar(_scoped(select(Timesheet).where(Timesheet.id == ts_id), user))
    if not t:
        raise not_found("Timesheet")
    return t


def _can_edit(user: CurrentUser, t: Timesheet) -> bool:
    return user.role == "ADMIN" or user.employee_id == t.employee_id


def _can_decide(user: CurrentUser, t: Timesheet) -> bool:
    if user.role == "ADMIN":
        return True
    return user.role == "MANAGER" and t.employee.department_id == user.department_id and t.employee_id != user.employee_id


@router.get("", response_model=list[TimesheetOut])
def list_timesheets(
    status: Literal["DRAFT", "SUBMITTED", "APPROVED", "REJECTED"] | None = None,
    mine: bool = False,
    user: CurrentUser = Depends(current_user),
    db: Session = Depends(get_db),
):
    stmt = _scoped(select(Timesheet), user)
    if status:
        stmt = stmt.where(Timesheet.status == status)
    if mine:
        stmt = stmt.where(Timesheet.employee_id == user.employee_id)
    rows = db.scalars(stmt.order_by(Timesheet.week_start.desc(), Timesheet.id.desc()).limit(300)).unique().all()
    return [timesheet_out(t) for t in rows]


@router.get("/{ts_id}", response_model=TimesheetOut)
def get_timesheet(ts_id: int, user: CurrentUser = Depends(current_user), db: Session = Depends(get_db)):
    return timesheet_out(_load(db, user, ts_id))


@router.post("", response_model=TimesheetOut, status_code=201)
def create_timesheet(body: TimesheetIn, user: CurrentUser = Depends(current_user), db: Session = Depends(get_db)):
    employee_id = body.employee_id if user.role == "ADMIN" and body.employee_id else user.employee_id
    if not employee_id:
        raise bad_request("Your account is not linked to an employee record")
    e = db.get(Employee, employee_id)
    if not e or e.status != "ACTIVE":
        raise bad_request("Employee is not active")
    if db.scalar(select(Timesheet).where(Timesheet.employee_id == employee_id, Timesheet.week_start == body.week_start)):
        raise conflict("A timesheet for this week already exists", {"weekStart": "A timesheet for this week already exists"})
    t = Timesheet(employee_id=employee_id, week_start=body.week_start, notes=body.notes, status="DRAFT")
    t.entries = [TimesheetEntry(day_index=i, hours=h) for i, h in enumerate(body.hours)]
    db.add(t)
    db.flush()
    audit.record(db, user, "CREATE", "Timesheet", t.id, f"Week of {t.week_start}")
    db.commit()
    db.refresh(t)
    return timesheet_out(t)


@router.put("/{ts_id}", response_model=TimesheetOut)
def update_timesheet(ts_id: int, body: TimesheetUpdateIn, user: CurrentUser = Depends(current_user), db: Session = Depends(get_db)):
    t = _load(db, user, ts_id)
    if not _can_edit(user, t):
        raise forbidden("You can only edit your own timesheets")
    if t.status not in ("DRAFT", "REJECTED"):
        raise conflict(f"A {t.status.lower()} timesheet cannot be edited")
    t.entries.clear()
    db.flush()
    t.entries.extend(TimesheetEntry(day_index=i, hours=h) for i, h in enumerate(body.hours))
    t.notes = body.notes
    t.status = "DRAFT"
    audit.record(db, user, "UPDATE", "Timesheet", t.id)
    db.commit()
    db.refresh(t)
    return timesheet_out(t)


@router.post("/{ts_id}/submit", response_model=TimesheetOut)
def submit_timesheet(ts_id: int, user: CurrentUser = Depends(current_user), db: Session = Depends(get_db)):
    t = _load(db, user, ts_id)
    if not _can_edit(user, t):
        raise forbidden("You can only submit your own timesheets")
    if t.status not in ("DRAFT", "REJECTED"):
        raise conflict("Only draft or rejected timesheets can be submitted")
    if t.total_hours <= 0:
        raise bad_request("Enter at least one hour before submitting")
    t.status = "SUBMITTED"
    t.submitted_at = datetime.now(UTC)
    audit.record(db, user, "SUBMIT", "Timesheet", t.id, f"Week of {t.week_start}")
    db.commit()
    return timesheet_out(t)


@router.post("/{ts_id}/approve", response_model=TimesheetOut)
def approve_timesheet(ts_id: int, user: CurrentUser = Depends(require_role("ADMIN", "MANAGER")), db: Session = Depends(get_db)):
    t = _load(db, user, ts_id)
    if not _can_decide(user, t):
        raise forbidden("You can only approve timesheets of your department")
    if t.status in ("APPROVED", "REJECTED"):
        raise conflict(f"This timesheet is already {t.status.lower()}")
    t.status = "APPROVED"
    t.decided_at = datetime.now(UTC)
    t.decided_by_id = user.id
    t.reject_reason = None
    audit.record(db, user, "APPROVE", "Timesheet", t.id, f"{t.employee.full_name}, week of {t.week_start}")
    db.commit()
    db.refresh(t)
    return timesheet_out(t)


@router.post("/{ts_id}/reject", response_model=TimesheetOut)
def reject_timesheet(ts_id: int, body: RejectIn, user: CurrentUser = Depends(require_role("ADMIN", "MANAGER")), db: Session = Depends(get_db)):
    t = _load(db, user, ts_id)
    if not _can_decide(user, t):
        raise forbidden("You can only reject timesheets of your department")
    if t.status != "SUBMITTED":
        raise conflict("Only submitted timesheets can be rejected")
    t.status = "REJECTED"
    t.decided_at = datetime.now(UTC)
    t.decided_by_id = user.id
    t.reject_reason = body.reason.strip()
    audit.record(db, user, "REJECT", "Timesheet", t.id, t.reject_reason)
    db.commit()
    db.refresh(t)
    events.publish("timesheet.rejected", timesheetId=t.id)
    return timesheet_out(t)


@router.delete("/{ts_id}", status_code=204)
def delete_timesheet(ts_id: int, user: CurrentUser = Depends(current_user), db: Session = Depends(get_db)):
    t = _load(db, user, ts_id)
    if not _can_edit(user, t):
        raise forbidden()
    if t.status != "DRAFT":
        raise conflict("Only draft timesheets can be deleted")
    db.delete(t)
    audit.record(db, user, "DELETE", "Timesheet", ts_id)
    db.commit()
    return Response(status_code=204)
