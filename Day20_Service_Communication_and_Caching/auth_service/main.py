import os
import sqlite3
import hashlib
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from fastapi import FastAPI, HTTPException, status, Header, Request, Response
from pydantic import BaseModel

# Configure structured logging with correlation ID
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [ReqID: %(request_id)s] %(message)s")

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = "N/A"
        return True

logger = logging.getLogger("AuthService")
logger.addFilter(RequestIdFilter())

DB_PATH = os.getenv("AUTH_DB_PATH", "auth_day20.db")
SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key-week4-microservices")
ALGORITHM = "HS256"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def hash_pw(pw: str):
    return hashlib.sha256(("microservices_salt_" + pw).encode("utf-8")).hexdigest()

app = FastAPI(title="Auth Microservice (Day 20)", version="2.0.0")

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID", f"req-{uuid.uuid4().hex[:8]}")
    request.state.request_id = req_id
    extra = {"request_id": req_id}
    logger.info(f"Incoming {request.method} {request.url.path}", extra=extra)
    
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    logger.info(f"Completed {request.method} {request.url.path} with status {response.status_code}", extra=extra)
    return response

@app.on_event("startup")
def startup():
    init_db()

class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[str] = "user"

class UserLogin(BaseModel):
    username: str
    password: str

@app.post("/register", status_code=201)
def register(user: UserRegister, request: Request):
    extra = {"request_id": getattr(request.state, "request_id", "N/A")}
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (user.username, user.email))
    if cursor.fetchone():
        conn.close()
        logger.warning(f"Registration failed: user '{user.username}' exists", extra=extra)
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    created_at = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO users (username, email, hashed_password, role, created_at) VALUES (?, ?, ?, ?, ?)",
        (user.username, user.email, hash_pw(user.password), user.role or "user", created_at)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    logger.info(f"User '{user.username}' registered successfully with ID {user_id}", extra=extra)
    return {"id": user_id, "username": user.username, "email": user.email, "role": user.role or "user"}

@app.post("/login")
def login(creds: UserLogin, request: Request):
    extra = {"request_id": getattr(request.state, "request_id", "N/A")}
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (creds.username,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or row["hashed_password"] != hash_pw(creds.password):
        logger.warning(f"Failed login attempt for user '{creds.username}'", extra=extra)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = jwt.encode(
        {"sub": row["username"], "user_id": row["id"], "role": row["role"], "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    logger.info(f"JWT issued for user '{row['username']}'", extra=extra)
    return {"access_token": token, "token_type": "bearer", "username": row["username"], "role": row["role"]}

@app.get("/verify-token")
def verify_token(request: Request, authorization: Optional[str] = Header(None)):
    extra = {"request_id": getattr(request.state, "request_id", "N/A")}
    logger.info("Inter-service token verification requested", extra=extra)
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Token verification rejected: Missing Bearer header", extra=extra)
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"Token verified valid for user '{payload.get('sub')}'", extra=extra)
        return {"valid": True, "user": payload}
    except Exception as e:
        logger.warning(f"Token verification failed: {str(e)}", extra=extra)
        raise HTTPException(status_code=401, detail="Invalid or expired token")

