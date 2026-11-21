import os
import time
import json
import uuid
import logging
import sqlite3
from typing import Optional, List
import httpx
from fastapi import FastAPI, HTTPException, status, Header, Request, Response
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [ReqID: %(request_id)s] %(message)s")

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = "N/A"
        return True

logger = logging.getLogger("InventoryService")
logger.addFilter(RequestIdFilter())

DB_PATH = os.getenv("INVENTORY_DB_PATH", "inventory_day20.db")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# High-reliability Redis Cache client with in-memory fallback
class RedisCache:
    def __init__(self):
        self._memory_store = {}
        self._redis = None
        try:
            import redis
            self._redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, socket_connect_timeout=1)
            self._redis.ping()
            logger.info("Connected to external Redis server", extra={"request_id": "SYS"})
        except Exception:
            self._redis = None
            logger.info("Using embedded Redis-compatible TTL cache manager", extra={"request_id": "SYS"})

    def get(self, key: str):
        if self._redis:
            try:
                return self._redis.get(key)
            except Exception:
                pass
        
        entry = self._memory_store.get(key)
        if entry:
            val, exp = entry
            if time.time() < exp:
                return val
            else:
                del self._memory_store[key]
        return None

    def setex(self, key: str, ttl_seconds: int, value: str):
        if self._redis:
            try:
                self._redis.setex(key, ttl_seconds, value)
                return
            except Exception:
                pass
        self._memory_store[key] = (value, time.time() + ttl_seconds)

    def delete(self, key: str):
        if self._redis:
            try:
                self._redis.delete(key)
            except Exception:
                pass
        if key in self._memory_store:
            del self._memory_store[key]

cache = RedisCache()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        stock_quantity INTEGER NOT NULL DEFAULT 0,
        category TEXT DEFAULT 'general'
    )
    """)
    cursor.execute("SELECT COUNT(*) as count FROM items")
    if cursor.fetchone()["count"] == 0:
        cursor.executemany("""
        INSERT INTO items (sku, name, description, price, stock_quantity, category)
        VALUES (?, ?, ?, ?, ?, ?)
        """, [
            ("SKU-LAPTOP-01", "Developer Laptop Pro", "High performance 32GB RAM workstation", 1499.99, 15, "Electronics"),
            ("SKU-KEYBD-02", "Mechanical Keyboard", "RGB Wireless mechanical switches", 129.50, 45, "Peripherals"),
            ("SKU-MOUSE-03", "Ergonomic Optical Mouse", "Precision sensor with side buttons", 59.99, 80, "Peripherals"),
            ("SKU-MONTR-04", "27-inch 4K Monitor", "UltraHD IPS display with USB-C hub", 399.00, 20, "Displays")
        ])
    conn.commit()
    conn.close()

app = FastAPI(title="Inventory Microservice (Day 20)", version="2.0.0")

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

async def validate_token_with_auth_service(auth_header: Optional[str], req_id: str):
    extra = {"request_id": req_id}
    if not auth_header:
        logger.warning("Access denied: Missing Authorization header", extra=extra)
        raise HTTPException(status_code=401, detail="Authentication required: Missing Authorization header")
    
    logger.info(f"Dispatching token validation call to Auth Service ({AUTH_SERVICE_URL}/verify-token)", extra=extra)
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                f"{AUTH_SERVICE_URL}/verify-token",
                headers={"Authorization": auth_header, "X-Request-ID": req_id}
            )
            if resp.status_code != 200:
                logger.warning(f"Auth service rejected token with status {resp.status_code}", extra=extra)
                raise HTTPException(status_code=401, detail="Invalid or expired authentication token")
            auth_data = resp.json()
            logger.info(f"Token validated successfully by Auth Service for user: {auth_data['user']['sub']}", extra=extra)
            return auth_data["user"]
    except httpx.RequestError as exc:
        logger.error(f"Failed to communicate with Auth Service: {str(exc)}", extra=extra)
        raise HTTPException(status_code=503, detail="Auth Service unavailable for token verification")

class ItemCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = ""
    price: float
    stock_quantity: int
    category: Optional[str] = "general"

@app.get("/items")
def get_items(request: Request):
    req_id = getattr(request.state, "request_id", "N/A")
    extra = {"request_id": req_id}
    cache_key = "items:all"
    
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info("[REDIS CACHE HIT] Returning cached items list (TTL 60s)", extra=extra)
        return json.loads(cached_data)
    
    logger.info("[REDIS CACHE MISS] Querying database for items and populating cache", extra=extra)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    rows = cursor.fetchall()
    conn.close()
    
    items = [dict(row) for row in rows]
    cache.setex(cache_key, 60, json.dumps(items))
    logger.info(f"[REDIS CACHE SET] Stored {len(items)} items in cache with 60s TTL", extra=extra)
    return items

@app.post("/items", status_code=201)
async def create_item(
    item: ItemCreate,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    req_id = getattr(request.state, "request_id", "N/A")
    extra = {"request_id": req_id}
    # Validate token through Auth Service
    user = await validate_token_with_auth_service(authorization, req_id)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM items WHERE sku = ?", (item.sku,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    cursor.execute(
        "INSERT INTO items (sku, name, description, price, stock_quantity, category) VALUES (?, ?, ?, ?, ?, ?)",
        (item.sku, item.name, item.description, item.price, item.stock_quantity, item.category)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    
    # Invalidate cache on write
    cache.delete("items:all")
    logger.info(f"[CACHE INVALIDATION] Invalided 'items:all' cache following creation of SKU '{item.sku}' by {user.get('sub')}", extra=extra)
    return {"id": new_id, **item.dict()}

