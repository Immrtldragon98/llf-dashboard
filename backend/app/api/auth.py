from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from app.db.session import engine
from app.schemas.common import LoginIn
from app.core.security import pwd, issue_token, current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login")
def login(payload: LoginIn):
    with engine.begin() as c:
        row = c.execute(text("SELECT id,username,password_hash,role,active FROM users WHERE username=:u"),
                        {"u":payload.username}).mappings().first()
    if not row or not row["active"] or not pwd.verify(payload.password, row["password_hash"]):
        raise HTTPException(401, "Invalid username or password")
    return {"token":issue_token(row["username"],row["role"],row["id"]),
            "username":row["username"],"role":row["role"]}

@router.get("/me")
def me(user=Depends(current_user)):
    return user
