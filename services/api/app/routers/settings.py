import math
from datetime import datetime, time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import CurrentUser, require_role
from ..errors import bad_request
from ..models import AuditLog, Setting, TaxBracket, User
from ..schemas import AuditOut, BracketIo, Page, TaxSettingsIo, UserRow
from ..services import audit
from ..services.calc import Bracket
from ..services.settings_store import load_config, validate_brackets

router = APIRouter(tags=["settings"])


def _tax_out(db: Session) -> TaxSettingsIo:
    cfg = load_config(db)
    return TaxSettingsIo(
        brackets=[BracketIo(lower=b.lower, upper=b.upper, rate=b.rate) for b in cfg.brackets],
        social_rate=cfg.social_rate,
        pension_rate=cfg.pension_rate,
    )


@router.get("/settings/tax", response_model=TaxSettingsIo)
def get_tax(_: CurrentUser = Depends(require_role("ADMIN", "MANAGER")), db: Session = Depends(get_db)):
    return _tax_out(db)


@router.put("/settings/tax", response_model=TaxSettingsIo)
def put_tax(body: TaxSettingsIo, user: CurrentUser = Depends(require_role("ADMIN")), db: Session = Depends(get_db)):
    brackets = [Bracket(b.lower, b.upper, b.rate) for b in body.brackets]
    errors = validate_brackets(brackets)
    if errors:
        raise bad_request(errors[0], {"brackets": "; ".join(errors)})
    db.execute(delete(TaxBracket))
    for i, b in enumerate(sorted(brackets, key=lambda x: x.lower)):
        db.add(TaxBracket(sort_order=i, lower=b.lower, upper=b.upper, rate=b.rate))
    for key, value in (("social_rate", body.social_rate), ("pension_rate", body.pension_rate)):
        row = db.get(Setting, key)
        if row:
            row.value = str(value)
        else:
            db.add(Setting(key=key, value=str(value)))
    audit.record(db, user, "UPDATE", "TaxSettings", None, body.model_dump(mode="json"))
    db.commit()
    return _tax_out(db)


@router.get("/users", response_model=list[UserRow])
def list_users(_: CurrentUser = Depends(require_role("ADMIN")), db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.email)).unique().all()
    return [
        UserRow(
            id=u.id,
            email=u.email,
            name=u.full_name,
            role=u.role,
            active=u.is_active,
            department=u.department.name if u.department else None,
            last_login_at=u.last_login_at,
        )
        for u in users
    ]


@router.get("/audit", response_model=Page[AuditOut])
def audit_log(
    entity: str | None = None,
    action: str | None = None,
    q: str | None = None,
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200, alias="pageSize"),
    _: CurrentUser = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    stmt = select(AuditLog)
    if entity:
        stmt = stmt.where(AuditLog.entity == entity)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if q:
        stmt = stmt.where(or_(AuditLog.user_email.ilike(f"%{q}%"), AuditLog.details.ilike(f"%{q}%")))
    if date_from:
        stmt = stmt.where(AuditLog.created_at >= datetime.combine(datetime.fromisoformat(date_from).date(), time.min))
    if date_to:
        stmt = stmt.where(AuditLog.created_at <= datetime.combine(datetime.fromisoformat(date_to).date(), time.max))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return Page[AuditOut](
        items=[AuditOut.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size),
    )


@router.get("/audit/facets")
def audit_facets(_: CurrentUser = Depends(require_role("ADMIN")), db: Session = Depends(get_db)):
    entities = db.scalars(select(AuditLog.entity).distinct().order_by(AuditLog.entity)).all()
    actions = db.scalars(select(AuditLog.action).distinct().order_by(AuditLog.action)).all()
    return {"entities": entities, "actions": actions}
