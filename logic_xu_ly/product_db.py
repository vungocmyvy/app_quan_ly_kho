import sqlite3

def get_connection():
    return sqlite3.connect('logic_xu_ly/inventory.db')

def add_product(sku, name, category, stock, price, cost, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (sku, name, category, stock, price, cost, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (sku, name, category, stock, price, cost, status))
    conn.commit()
    conn.close()

def fetch_all_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products") #lấy tất cả dữ liệu từ bảng products
    data = cursor.fetchall()
    conn.close()
    return data

# Lọc danh sách tìm sản phẩm theo sku/ tên sản phẩm ở thanh tìm kiếm
def search_suppliers(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    # Tìm kiếm theo tên hoặc loại hàng
    query = "SELECT * FROM suppliers WHERE name LIKE ? OR category LIKE ?"
    cursor.execute(query, (f'%{keyword}%', f'%{keyword}%'))
    rows = cursor.fetchall()
    conn.close()
    return rows