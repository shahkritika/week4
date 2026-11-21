from fastapi import FastAPI, HTTPException, status, Query
from typing import List, Optional
from .database import get_db, init_db
from .schemas import ItemCreate, ItemResponse, ItemUpdate, StockUpdate

app = FastAPI(title="Inventory & Catalog Service", version="1.0.0", description="Autonomous Inventory Microservice")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health_check():
    return {"service": "inventory_service", "status": "healthy"}

@app.get("/items", response_model=List[ItemResponse])
def get_items(category: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    if category:
        cursor.execute("SELECT * FROM items WHERE category = ?", (category,))
    else:
        cursor.execute("SELECT * FROM items")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")
    return dict(row)

@app.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate):
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
    item_id = cursor.lastrowid
    conn.close()
    return {
        "id": item_id,
        "sku": item.sku,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "stock_quantity": item.stock_quantity,
        "category": item.category
    }

@app.put("/items/{item_id}/stock", response_model=ItemResponse)
def update_stock(item_id: int, update: StockUpdate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")
    
    new_stock = row["stock_quantity"] + update.delta
    if new_stock < 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Insufficient stock; stock cannot fall below 0")
    
    cursor.execute("UPDATE items SET stock_quantity = ? WHERE id = ?", (new_stock, item_id))
    conn.commit()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    updated_row = cursor.fetchone()
    conn.close()
    return dict(updated_row)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)

