import sqlite3

def get_connection():
    return sqlite3.connect('logic_xu_ly/inventory.db')

# 1. Lấy danh sách hóa đơn
def fetch_all_invoices():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT invoice_no, customer_name, date, due_date, amount, status FROM invoices")
    data = cursor.fetchall()
    conn.close()
    return data

# 2. Thêm hóa đơn mới (Dùng cho nút 'Create Invoice')
def add_invoice(inv_no, customer, date, due_date, amount, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO invoices (invoice_no, customer_name, date, due_date, amount, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (inv_no, customer, date, due_date, amount, status))
    conn.commit()
    conn.close()

# 3. Xóa hoặc cập nhật trạng thái (Tùy chọn cho nút 'Actions')
def update_invoice_status(inv_no, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE invoices SET status = ? WHERE invoice_no = ?", (new_status, inv_no))
    conn.commit()
    conn.close()