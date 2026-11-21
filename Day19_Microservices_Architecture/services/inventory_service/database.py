import os
import sqlite3

DB_PATH = os.getenv("INVENTORY_DB_PATH", "inventory.db")

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
    # Seed default sample data if empty
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

