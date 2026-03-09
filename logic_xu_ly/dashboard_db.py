import sqlite3

def get_dashboard_stats():
    conn = sqlite3.connect('logic_xu_ly/inventory.db')
    cursor = conn.cursor()
    
    # 1. Tổng số sản phẩm (Total Products)
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]
    
    # 2. Tổng giá trị kho (Total Value) = Giá * Số lượng
    cursor.execute("SELECT SUM(price * stock) FROM products")
    total_value = cursor.fetchone()[0] or 0 # Nếu null trả về 0
    
    # 3. Sản phẩm sắp hết hàng (Low Stock - dưới 20 cái)
    cursor.execute("SELECT COUNT(*) FROM products WHERE stock > 0 AND stock < 20")
    low_stock = cursor.fetchone()[0]
    
    # 4. Sản phẩm hết hàng (Out of Stock)
    cursor.execute("SELECT COUNT(*) FROM products WHERE stock = 0")
    out_of_stock = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total_products": total_products,
        "total_value": f"${total_value:,.2f}",
        "low_stock": low_stock,
        "out_of_stock": out_of_stock
    }

def get_category_distribution():
    """Lấy dữ liệu cho biểu đồ tròn (Pie Chart)"""
    conn = sqlite3.connect('logic_xu_ly/inventory.db')
    cursor = conn.cursor()
    # Đếm số lượng sản phẩm theo từng loại (Electronics, Office Supplies...)
    cursor.execute("SELECT category, COUNT(*) FROM products GROUP BY category")
    data = cursor.fetchall()
    conn.close()
    return data # Trả về danh sách [('Electronics', 10), ('Furniture', 5)]
