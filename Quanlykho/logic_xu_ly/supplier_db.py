import sqlite3

# Hàm kết nối
def get_connection():
    return sqlite3.connect('logic_xu_ly/inventory.db')

def add_supplier(name, category, email, phone, address, contact_person, total_orders):
    conn = sqlite3.connect('logic_xu_ly/inventory.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO suppliers (name, category, email, phone, address, contact_person, total_orders)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, category, email, phone, address, contact_person, total_orders))
    conn.commit()
    conn.close()

# Hàm trả về danh sách tất cả nhà cung cấp
def fetch_all_suppliers():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, category, email, phone, address, contact_person, total_orders FROM suppliers")
    rows = cursor.fetchall() 
    
    conn.close()
    return rows

# Lọc danh sách nhà cung cấp khi gõ tên loại hàng ở thanh tìm kiếm
def search_suppliers(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    # Tìm kiếm theo tên hoặc loại hàng
    query = "SELECT * FROM suppliers WHERE name LIKE ? OR category LIKE ?"
    cursor.execute(query, (f'%{keyword}%', f'%{keyword}%'))
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_supplier_status(supplier_id, new_status):
    conn = sqlite3.connect('logic_xu_ly/inventory.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE suppliers SET category = ? WHERE id = ?", (new_status, supplier_id))
    conn.commit()
    conn.close()

def delete_supplier(supplier_id):
    conn = sqlite3.connect('logic_xu_ly/inventory.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
    conn.commit() 
    
    conn.close()

def get_next_stt():
    conn = sqlite3.connect('logic_xu_ly/inventory.db')
    cursor = conn.cursor()
    # Đếm tổng số dòng hiện có trong bảng suppliers
    cursor.execute("SELECT COUNT(*) FROM suppliers")
    count = cursor.fetchone()[0]
    conn.close()
    return count + 1