from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
import bcrypt
import jwt
import os
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

from db import get_db
from models import LoginRequest, ChangePasswordRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Load .env from backend/ directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

JWT_SECRET = os.getenv("JWT_SECRET", "moviezone_secret_key_change_in_production")


def create_token(admin_id: str, username: str) -> str:
    payload = {
        "id": admin_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access denied. No token provided.")
    token = authorization.split(" ")[1]
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")


@router.post("/login")
def login(req: LoginRequest):
    conn = get_db()
    admin = conn.execute("SELECT * FROM admins WHERE username = ?", (req.username,)).fetchone()
    conn.close()

    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    if not bcrypt.checkpw(req.password.encode(), admin["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    token = create_token(admin["id"], admin["username"])
    return {"token": token, "username": admin["username"]}


@router.get("/verify")
def verify(authorization: Optional[str] = Header(None)):
    payload = verify_token(authorization)
    return {"valid": True, "admin": payload}


@router.post("/change-password")
def change_password(req: ChangePasswordRequest, authorization: Optional[str] = Header(None)):
    payload = verify_token(authorization)
    conn = get_db()
    admin = conn.execute("SELECT * FROM admins WHERE id = ?", (payload["id"],)).fetchone()

    if not bcrypt.checkpw(req.currentPassword.encode(), admin["password"].encode()):
        conn.close()
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    hashed = bcrypt.hashpw(req.newPassword.encode(), bcrypt.gensalt()).decode()
    conn.execute("UPDATE admins SET password = ? WHERE id = ?", (hashed, payload["id"]))
    conn.commit()
    conn.close()
    return {"message": "Password updated successfully."}
