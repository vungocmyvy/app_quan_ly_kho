import sqlite3

DB_PATH = 'logic_xu_ly/inventory.db'


def get_connection():
    return sqlite3.connect(DB_PATH)


def _ensure_table():
    """Tạo bảng + thêm cột còn thiếu nếu DB cũ."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name    TEXT,
            order_date       TEXT,
            expected_delivery TEXT,
            delivery_location TEXT,
            product_sku      TEXT,
            product_name     TEXT,
            quantity         INTEGER DEFAULT 0,
            unit_price       REAL    DEFAULT 0,
            subtotal         REAL    DEFAULT 0,
            shipping_cost    REAL    DEFAULT 0,
            total_amount     REAL    DEFAULT 0,
            shipping_method  TEXT    DEFAULT 'Tiêu chuẩn (3-5 ngày)',
            priority         TEXT    DEFAULT 'Bình thường',
            weight_kg        REAL    DEFAULT 1.0,
            notes            TEXT    DEFAULT '',
            status           TEXT    DEFAULT 'pending'
        )
    """)
    # Thêm cột mới nếu DB cũ chưa có
    cur.execute("PRAGMA table_info(purchase_orders)")
    existing = {r[1] for r in cur.fetchall()}
    new_cols = {
        "subtotal":        "REAL DEFAULT 0",
        "shipping_cost":   "REAL DEFAULT 0",
        "shipping_method": "TEXT DEFAULT 'Tiêu chuẩn (3-5 ngày)'",
        "priority":        "TEXT DEFAULT 'Bình thường'",
        "weight_kg":       "REAL DEFAULT 1.0",
        "notes":           "TEXT DEFAULT ''",
    }
    for col, typ in new_cols.items():
        if col not in existing:
            cur.execute(f"ALTER TABLE purchase_orders ADD COLUMN {col} {typ}")
    conn.commit()
    conn.close()


_ensure_table()


def add_purchase_order(supplier_name, order_date, expected_delivery,
                       delivery_location, product_sku, product_name,
                       quantity, unit_price, subtotal, shipping_cost,
                       total_amount, shipping_method='Tiêu chuẩn (3-5 ngày)',
                       priority='Bình thường', weight_kg=1.0,
                       notes='', status='pending'):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO purchase_orders
            (supplier_name, order_date, expected_delivery, delivery_location,
             product_sku, product_name, quantity, unit_price,
             subtotal, shipping_cost, total_amount,
             shipping_method, priority, weight_kg, notes, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (supplier_name, order_date, expected_delivery, delivery_location,
          product_sku, product_name, quantity, unit_price,
          subtotal, shipping_cost, total_amount,
          shipping_method, priority, weight_kg, notes, status))
    conn.commit()
    conn.close()


def fetch_all_purchase_orders():
    """Trả về 8 cột để hiển thị bảng:
       (id, supplier_name, order_date, expected_delivery,
        product_name, quantity, total_amount, status)
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, supplier_name, order_date, expected_delivery,
               product_name, quantity, total_amount, status
        FROM   purchase_orders
        ORDER  BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def search_purchase_orders(keyword):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, supplier_name, order_date, expected_delivery,
               product_name, quantity, total_amount, status
        FROM   purchase_orders
        WHERE  LOWER(supplier_name) LIKE ? OR LOWER(product_name) LIKE ?
        ORDER  BY id DESC
    """, (f'%{keyword.lower()}%', f'%{keyword.lower()}%'))
    rows = cur.fetchall()
    conn.close()
    return rows


def update_purchase_order_status(order_id, new_status):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("UPDATE purchase_orders SET status=? WHERE id=?",
                (new_status, order_id))
    conn.commit()
    conn.close()


def delete_purchase_order(order_id):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("DELETE FROM purchase_orders WHERE id=?", (order_id,))
    conn.commit()
    conn.close()
