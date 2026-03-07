import sqlite3

#Khởi tạo cấu trúc bảng
def setup():
    conn = sqlite3.connect('logic_xu_ly/inventory.db')
    cursor = conn.cursor()
    
    # Lệnh này sẽ tạo bảng nếu nó chưa tồn tại
    # Supplier
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            contact_person TEXT
        )
    ''')

    # Customers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            total_orders INTEGER DEFAULT 0,
            balance REAL DEFAULT 0.0,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # Products 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            sku TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            stock INTEGER DEFAULT 0,
            price REAL,
            cost REAL,
            status TEXT
        )
    ''')
    #Invoices
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            date TEXT,
            due_date TEXT,
            amount REAL,
            status TEXT DEFAULT 'pending' -- paid, pending, overdue, draft
        )
    ''')
    conn.commit()
    conn.close()
    print("Đã tạo bảng 'suppliers' 'customers' 'products' thành công!")

if __name__ == "__main__":
    setup()
