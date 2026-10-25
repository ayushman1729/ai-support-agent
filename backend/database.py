import sqlite3
import os

# On Vercel serverless, root directory is read-only, so write SQLite DB in /tmp
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/support_system.db"
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "support_system.db")

def get_db_connection():
    db_exists = os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if not db_exists:
        init_db_conn(conn)
    return conn

def init_db_conn(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            item_name TEXT NOT NULL,
            status TEXT NOT NULL,
            courier TEXT,
            tracking_id TEXT,
            estimated_delivery TEXT,
            total_amount REAL NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            order_id INTEGER,
            issue_description TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT DEFAULT 'OPEN',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM orders")
    if cursor.fetchone()[0] == 0:
        seed_orders = [
            (101, "Rahul Sharma", "Sony WH-1000XM5 Headphones", "Shipped", "BlueDart", "BD889210", "Kal shaam 5 baje", 24999.00),
            (102, "Priya Singh", "Logitech MX Master 3S Mouse", "Processing", "Delhivery", "DL431102", "3 din ke andar", 8495.00),
            (103, "Amit Verma", "Samsung 4K Gaming Monitor", "Delivered", "EcomExpress", "EC991044", "Pehle hi deliver ho chuka hai (2 din pehle)", 31999.00),
            (104, "Sneha Patel", "Apple Watch Series 9", "Cancelled", None, None, None, 41900.00),
        ]
        cursor.executemany("""
            INSERT INTO orders (order_id, customer_name, item_name, status, courier, tracking_id, estimated_delivery, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, seed_orders)
    conn.commit()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    init_db_conn(conn)
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at", DB_PATH)
