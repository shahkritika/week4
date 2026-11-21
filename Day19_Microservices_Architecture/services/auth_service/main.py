from fastapi import FastAPI, HTTPException, status, Header, Depends
from datetime import datetime, timezone
from .database import get_db, init_db
from .auth_utils import hash_password, verify_password, create_access_token, decode_access_token
from .schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from typing import Optional

app = FastAPI(title="Auth & User Service", version="1.0.0", description="Autonomous Auth Microservice")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health_check():
    return {"service": "auth_service", "status": "healthy"}

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserRegister):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (user.username, user.email))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    created_at = datetime.now(timezone.utc).isoformat()
    hashed_pw = hash_password(user.password)
    cursor.execute(
        "INSERT INTO users (username, email, hashed_password, role, created_at) VALUES (?, ?, ?, ?, ?)",
        (user.username, user.email, hashed_pw, user.role or "user", created_at)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "role": user.role or "user",
        "created_at": created_at
    }

@app.post("/login", response_model=TokenResponse)
def login(creds: UserLogin):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (creds.username,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not verify_password(creds.password, row["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = create_access_token({"sub": row["username"], "user_id": row["id"], "role": row["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": row["username"],
        "role": row["role"]
    }

@app.get("/verify-token")
def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"valid": True, "user": payload}

@app.get("/users/me", response_model=UserResponse)
def get_current_user(authorization: Optional[str] = Header(None)):
    token_data = verify_token(authorization)
    username = token_data["user"]["sub"]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "role": row["role"],
        "created_at": row["created_at"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)

