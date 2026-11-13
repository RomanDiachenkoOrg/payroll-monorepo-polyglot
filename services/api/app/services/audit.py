import json
from typing import Any

from sqlalchemy.orm import Session

from ..deps import CurrentUser
from ..models import AuditLog


def record(db: Session, user: CurrentUser | None, action: str, entity: str, entity_id: Any = None, details: Any = None) -> None:
    if details is not None and not isinstance(details, str):
        details = json.dumps(details, default=str)
    db.add(
        AuditLog(
            user_id=user.id if user else None,
            user_email=user.email if user else "system",
            action=action,
            entity=entity,
            entity_id=None if entity_id is None else str(entity_id),
            details=details,
        )
    )
