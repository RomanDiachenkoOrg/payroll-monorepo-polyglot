from collections.abc import Callable
from dataclasses import dataclass

import jwt
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from .db import get_db
from .errors import ApiError
from .security import decode_token


@dataclass
class CurrentUser:
    id: int
    email: str
    name: str
    role: str
    employee_id: int | None
    department_id: int | None


def current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ApiError(401, "Please sign in")
    try:
        claims = decode_token(authorization[7:])
    except jwt.PyJWTError:
        raise ApiError(401, "Your session has expired. Please sign in again.") from None
    return CurrentUser(
        id=int(claims["sub"]),
        email=claims["email"],
        name=claims["name"],
        role=claims["role"],
        employee_id=claims.get("emp"),
        department_id=claims.get("dept"),
    )


def require_role(*roles: str) -> Callable[[CurrentUser], CurrentUser]:
    def checker(user: CurrentUser = Depends(current_user)) -> CurrentUser:
        if user.role not in roles:
            raise ApiError(403, "You do not have permission to do this")
        return user

    return checker


DB = Depends(get_db)
