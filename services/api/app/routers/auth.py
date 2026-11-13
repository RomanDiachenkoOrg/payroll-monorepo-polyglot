from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import CurrentUser, current_user
from ..errors import ApiError
from ..mappers import user_out
from ..models import User
from ..schemas import LoginIn, LoginOut, UserOut
from ..security import create_token, verify_password
from ..services import audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    if not user or not user.is_active or not verify_password(body.password, user.password_hash):
        raise ApiError(401, "Invalid email or password")
    user.last_login_at = datetime.now(UTC)
    token = create_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "name": user.full_name,
            "role": user.role,
            "emp": user.employee_id,
            "dept": user.department_id,
        }
    )
    audit.record(db, CurrentUser(user.id, user.email, user.full_name, user.role, user.employee_id, user.department_id), "LOGIN", "User", user.id)
    db.commit()
    return LoginOut(token=token, user=user_out(user))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser = Depends(current_user), db: Session = Depends(get_db)):
    u = db.get(User, user.id)
    if not u or not u.is_active:
        raise ApiError(401, "Your session has expired. Please sign in again.")
    return user_out(u)


@router.post("/logout")
def logout(user: CurrentUser = Depends(current_user), db: Session = Depends(get_db)):
    audit.record(db, user, "LOGOUT", "User", user.id)
    db.commit()
    return {"ok": True}
