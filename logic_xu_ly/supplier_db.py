import sqlite3

# Hàm kết nối
def get_connection():
    return sqlite3.connect('logic_xu_ly/inventory.db')

def add_supplier(name, category, email, phone, address, contact_person):
    conn = get_connection() #connect file inventory.db
    cursor = conn.cursor() # trỏ vào từng dòng
    # soạn nội dung
    sql = "INSERT INTO suppliers (name, category, email, phone, address, contact_person) VALUES (?,?,?,?,?,?)"
    # viết nội dung
    cursor.execute(sql, (name, category, email, phone, address, contact_person))
    conn.commit() #lưu file
    conn.close()

# Hàm trả về danh sách tất cả nhà cung cấp
def fetch_all_suppliers():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Lấy đầy đủ các cột để hiện lên bảng
    cursor.execute("SELECT id, name, category, email, phone, address, contact_person FROM suppliers")
    rows = cursor.fetchall() # trỏ tất cả các hàng và lưu dữ liệu
    
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