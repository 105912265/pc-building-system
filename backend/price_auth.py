"""Phase 5 registration, login and Admin/User authentication.

Uses existing `user` + `price_account` tables; the latter is a legacy name
from the earlier price lookup prototype, retained to avoid a schema migration.
Accounts imported from Phase 3 have no password unless registered.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
import mysql.connector
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from backend.database import get_db_connection

router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer = HTTPBearer(auto_error=False)


class Registration(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)


class Login(BaseModel):
    email: EmailStr
    password: str


def hash_password(password: str) -> str:
    """Scrypt with fresh per-account salt (no plaintext passwords stored)."""
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return "scrypt$16384$8$1$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(key).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        alg, n, r, p, salt_b64, hash_b64 = stored.split("$")
        if alg != "scrypt" or (int(n), int(r), int(p)) != (16384, 8, 1):
            return False
        salt = base64.urlsafe_b64decode(salt_b64)
        expected = base64.urlsafe_b64decode(hash_b64)
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, KeyError):
        return False


def jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 32:
        raise HTTPException(503, "JWT_SECRET is not configured (32+ characters required)")
    return secret


def create_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "iat": now, "exp": now + timedelta(hours=2)},
        jwt_secret(), algorithm="HS256",
    )


def get_current_user(auth: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if auth is None:
        raise HTTPException(401, "Sign in and provide a Bearer token")
    try:
        payload = jwt.decode(auth.credentials, jwt_secret(), algorithms=["HS256"])
        user_id = int(payload["sub"])
        if user_id <= 0:
            raise ValueError("Invalid user")
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        raise HTTPException(401, "Invalid or expired token")

    db = get_db_connection()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT u.user_id, u.username, u.email, a.role "
            "FROM `user` u JOIN price_account a ON a.user_id=u.user_id WHERE u.user_id=%s",
            (user_id,),
        )
        account = cursor.fetchone()
        if not account:
            raise HTTPException(401, "Account not found")
        return account
    finally:
        if cursor:
            cursor.close()
        db.close()


@router.post("/register", status_code=201)
def register(body: Registration):
    db = get_db_connection()
    cursor = None
    try:
        cursor = db.cursor()
        # Existing `user.email` has a UNIQUE index; concurrent duplicates fail safely.
        cursor.execute(
            "INSERT INTO `user`(username,email,created_at) VALUES (%s,%s,UTC_TIMESTAMP())",
            (body.username.strip(), str(body.email).lower()),
        )
        user_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO price_account(user_id,password_hash,role) VALUES(%s,%s,'user')",
            (user_id, hash_password(body.password)),
        )
        db.commit()
        return {"user_id": user_id, "email": str(body.email).lower(), "role": "user"}
    except mysql.connector.IntegrityError:
        db.rollback()
        raise HTTPException(409, "That email is already registered")
    except Exception:
        db.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        db.close()


@router.post("/login")
def login(body: Login):
    db = get_db_connection()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT u.user_id, a.password_hash FROM `user` u "
            "JOIN price_account a ON a.user_id=u.user_id WHERE u.email=%s",
            (str(body.email).lower(),),
        )
        user = cursor.fetchone()
        if not user or not verify_password(body.password, user["password_hash"]):
            raise HTTPException(401, "Incorrect email or password")
        return {"access_token": create_token(user["user_id"]), "token_type": "bearer"}
    finally:
        if cursor:
            cursor.close()
        db.close()


@router.get("/me")
def me(account: dict = Depends(get_current_user)):
    """Return the currently signed-in user and role; no search quotas."""
    return account


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dependency for future Admin-only component/report endpoints."""
    if user["role"] != "admin":
        raise HTTPException(403, "Administrator access required")
    return user
