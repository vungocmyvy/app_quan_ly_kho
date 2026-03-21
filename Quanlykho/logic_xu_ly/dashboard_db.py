import sqlite3
from datetime import datetime

DB_PATH = 'logic_xu_ly/inventory.db'


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_dashboard_stats():
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM products")
    total_products = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(price * stock), 0) FROM products")
    total_value = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM products WHERE stock > 0 AND stock < 20")
    low_stock = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM products WHERE stock = 0")
    out_of_stock = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM customers")
    total_customers = cur.fetchone()[0]

    conn.close()
    return {
        "total_products":  total_products,
        "total_value":     f"{total_value:,.0f} ₫",
        "low_stock":       low_stock,
        "out_of_stock":    out_of_stock,
        "total_customers": total_customers,
    }


def get_category_distribution():
    """Pie chart – số lượng SP theo danh mục từ DB thực."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT COALESCE(NULLIF(TRIM(category), ''), 'Khác') AS cat,
               COUNT(*)
        FROM   products
        GROUP  BY cat
        ORDER  BY 2 DESC
    """)
    data = cur.fetchall()
    conn.close()
    if not data:
        data = [("Electronics",35),("Clothing",20),("Food",15),
                ("Furniture",20),("Khác",10)]
    return data


def get_monthly_trend():
    """
    Line chart – 6 tháng gần nhất.
    - Doanh thu : tổng amount trong bảng invoices
    - Nhập kho  : tổng total_amount trong bảng purchase_orders (nếu có)
    Nếu cả hai đều rỗng → hiện data demo để giao diện không trắng.
    """
    conn = get_connection()
    cur  = conn.cursor()

    # Xác định cột tiền của invoices
    cur.execute("PRAGMA table_info(invoices)")
    inv_cols   = {r[1] for r in cur.fetchall()}
    amount_col = "amount" if "amount" in inv_cols else "total_amount"

    # Kiểm tra bảng purchase_orders có tồn tại không
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='purchase_orders'")
    has_po = cur.fetchone() is not None

    months    = []
    sales     = []
    purchases = []

    now = datetime.now()
    for i in range(5, -1, -1):
        m = now.month - i
        y = now.year
        while m <= 0:
            m += 12
            y -= 1

        months.append(datetime(y, m, 1).strftime("%b"))
        ym_str = f"{y:04d}-{m:02d}"

        # --- Doanh thu từ invoices ---
        try:
            cur.execute(f"""
                SELECT COALESCE(SUM(CAST({amount_col} AS REAL)), 0)
                FROM   invoices
                WHERE  date IS NOT NULL
                  AND  (
                       strftime('%Y-%m', date) = ?
                    OR date LIKE ?
                  )
            """, (ym_str, f"{ym_str}%"))
            sales.append(cur.fetchone()[0] or 0.0)
        except Exception:
            sales.append(0.0)

        # --- Nhập kho từ purchase_orders ---
        try:
            if has_po:
                cur.execute("""
                    SELECT COALESCE(SUM(total_amount), 0)
                    FROM   purchase_orders
                    WHERE  order_date IS NOT NULL
                      AND  (
                           strftime('%Y-%m', order_date) = ?
                        OR order_date LIKE ?
                      )
                """, (ym_str, f"{ym_str}%"))
                purchases.append(cur.fetchone()[0] or 0.0)
            else:
                purchases.append(0.0)
        except Exception:
            purchases.append(0.0)

    conn.close()

    # Nếu không có dữ liệu thực → demo
    if sum(sales) == 0 and sum(purchases) == 0:
        sales     = [45_000_000, 52_000_000, 48_000_000,
                     61_000_000, 55_000_000, 68_000_000]
        purchases = [32_000_000, 35_000_000, 30_000_000,
                     42_000_000, 38_000_000, 45_000_000]
        months    = ["Jan","Feb","Mar","Apr","May","Jun"]

    return months, sales, purchases


def get_recent_activities():
    """Lấy 5 hóa đơn mới nhất."""
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("PRAGMA table_info(invoices)")
    cols       = {r[1] for r in cur.fetchall()}
    amount_col = "amount" if "amount" in cols else "total_amount"
    inv_col    = "invoice_no" if "invoice_no" in cols else "CAST(id AS TEXT)"

    cur.execute(f"""
        SELECT {inv_col}, customer_name, date, {amount_col}, status
        FROM   invoices
        ORDER  BY id DESC
        LIMIT  5
    """)
    rows = cur.fetchall()
    conn.close()
    return rows
