from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Setting, TaxBracket
from .calc import DEFAULT_BRACKETS, Bracket, CalcConfig


def load_config(db: Session) -> CalcConfig:
    rows = db.scalars(select(TaxBracket).order_by(TaxBracket.sort_order)).all()
    brackets = [Bracket(r.lower, r.upper, r.rate) for r in rows] or list(DEFAULT_BRACKETS)
    values = {s.key: s.value for s in db.scalars(select(Setting)).all()}
    return CalcConfig(
        brackets=brackets,
        social_rate=Decimal(values.get("social_rate", "0.05")),
        pension_rate=Decimal(values.get("pension_rate", "0.03")),
    )


def validate_brackets(brackets: list[Bracket]) -> list[str]:
    errors: list[str] = []
    if not brackets:
        return ["At least one bracket is required"]
    ordered = sorted(brackets, key=lambda b: b.lower)
    if ordered[0].lower != 0:
        errors.append("The first bracket must start at 0")
    for i, b in enumerate(ordered):
        if b.rate < 0 or b.rate > 1:
            errors.append(f"Bracket {i + 1}: rate must be between 0 and 100%")
        nxt = ordered[i + 1] if i + 1 < len(ordered) else None
        if nxt is not None and b.upper != nxt.lower:
            errors.append(f"Bracket {i + 1} must end where bracket {i + 2} starts")
        if nxt is None and b.upper is not None:
            errors.append("The last bracket must have no upper limit")
    return errors
