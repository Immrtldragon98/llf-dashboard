from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Header, HTTPException, Depends
from passlib.context import CryptContext
from sqlalchemy import text
from app.core.config import JWT_SECRET, ACCESS_TOKEN_HOURS
from app.db.session import engine

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def issue_token(username: str, role: str, user_id: int):
    return jwt.encode(
        {"sub": username, "role": role, "uid": user_id,
         "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_HOURS)},
        JWT_SECRET, algorithm="HS256"
    )

def current_user(authorization: str | None = Header(None, alias="Authorization")):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Login required")
    try:
        payload = jwt.decode(authorization[7:], JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired login")
    with engine.begin() as c:
        row = c.execute(text("SELECT id,username,role,active FROM users WHERE id=:id"),
                        {"id":payload["uid"]}).mappings().first()
    if not row or not row["active"]:
        raise HTTPException(401, "User inactive")
    return dict(row)

def admin_only(user=Depends(current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Admin access required")
    return user
