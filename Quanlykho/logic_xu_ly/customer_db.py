import sqlite3

def get_connection():
    return sqlite3.connect('logic_xu_ly/inventory.db')

def add_customer(name, email, phone, orders, balance, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO customers (name, email, phone, total_orders, balance, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, email, phone, orders, balance, status))
    conn.commit()
    conn.close()

def fetch_all_customers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone, total_orders, status FROM customers")
    data = cursor.fetchall()
    conn.close()
    return data

# Lọc danh sách tìm khách hàng theo tên/mail ở thanh tìm kiếm
def search_customers(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    # Tìm kiếm theo tên hoặc loại hàng
    query = "SELECT * FROM customers WHERE name LIKE ? OR email LIKE ?"
    cursor.execute(query, (f'%{keyword}%', f'%{keyword}%'))
    rows = cursor.fetchall()
    conn.close()
    return rows
def update_customer_status(customer_id, new_status):
    conn = sqlite3.connect('logic_xu_ly/inventory.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE customers SET status = ? WHERE id = ?", (new_status, customer_id))
    conn.commit()
    conn.close()
def delete_customer(customer_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id=?", (customer_id,))
    conn.commit()
    conn.close()

def get_next_stt():
    conn = get_connection()
    cursor = conn.cursor()
    # Đếm xem hiện tại có bao nhiêu dòng trong bảng customers
    cursor.execute("SELECT COUNT(*) FROM customers")
    count = cursor.fetchone()[0]
    conn.close()
    return count + 1