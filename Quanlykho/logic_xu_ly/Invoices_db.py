import sqlite3

DB_PATH = 'logic_xu_ly/inventory.db'


def get_connection():
    return sqlite3.connect(DB_PATH)


def _ensure_columns():
    """Tự động thêm cột còn thiếu – chạy khi import."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("PRAGMA table_info(invoices)")
    existing = {r[1] for r in cur.fetchall()}
    needed = {
        "invoice_no": "TEXT",
        "due_date":   "TEXT",
        "amount":     "REAL DEFAULT 0",
    }
    for col, typ in needed.items():
        if col not in existing:
            cur.execute(f"ALTER TABLE invoices ADD COLUMN {col} {typ}")
    conn.commit()
    conn.close()


_ensure_columns()


# ── Khách hàng cho ComboBox ─────────────────────────────────────────────────
def fetch_customer_names():
    """Trả về [(id, name, phone, email), ...]"""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id, name, phone, email FROM customers ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows


# ── Sản phẩm cho ComboBox ────────────────────────────────────────────────────
def fetch_available_products():
    """Trả về [(sku, name, price, stock), ...]"""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT sku, name, price, stock
        FROM   products
        WHERE  stock > 0
        ORDER  BY name
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


# ── Đọc tất cả hóa đơn ──────────────────────────────────────────────────────
def fetch_all_invoices():
    """
    Luôn trả về 7 cột:
        0 = id (INTEGER – dùng cho xóa/sửa)
        1 = invoice_no hiển thị (COALESCE invoice_no, id)
        2 = customer_name
        3 = date
        4 = due_date
        5 = amount
        6 = status
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT
            id,
            COALESCE(NULLIF(TRIM(invoice_no), ''), CAST(id AS TEXT)) AS hd_no,
            customer_name,
            COALESCE(date,     '')               AS ngay_tao,
            COALESCE(due_date, '')               AS ngay_han,
            COALESCE(amount, total_amount, 0)    AS tong_tien,
            COALESCE(status, 'pending')          AS trang_thai
        FROM   invoices
        ORDER  BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


# ── Thêm hóa đơn ─────────────────────────────────────────────────────────────
def add_invoice(invoice_no, customer_name, date, due_date, amount, status):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO invoices
            (invoice_no, customer_name, date, due_date, amount, total_amount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (invoice_no, customer_name, date, due_date,
          amount, amount, status))
    conn.commit()
    conn.close()


# ── Cập nhật hóa đơn (dùng id) ───────────────────────────────────────────────
def update_invoice(row_id, invoice_no, customer_name, date, due_date,
                   amount, status):
    """row_id là id INTEGER thực trong DB."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        UPDATE invoices
        SET    invoice_no    = ?,
               customer_name = ?,
               date          = ?,
               due_date      = ?,
               amount        = ?,
               total_amount  = ?,
               status        = ?
        WHERE  id = ?
    """, (invoice_no, customer_name, date, due_date,
          amount, amount, status, row_id))
    conn.commit()
    conn.close()


# ── Cập nhật trạng thái (dùng id) ────────────────────────────────────────────
def update_invoice_status(row_id, new_status):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("UPDATE invoices SET status=? WHERE id=?",
                (new_status, row_id))
    conn.commit()
    conn.close()


# ── Xóa hóa đơn (dùng id) ────────────────────────────────────────────────────
def delete_invoice(row_id):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("DELETE FROM invoices WHERE id=?", (row_id,))
    conn.commit()
    conn.close()
