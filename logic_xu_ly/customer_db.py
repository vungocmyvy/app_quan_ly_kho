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
    cursor.execute("SELECT * FROM customers")
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
