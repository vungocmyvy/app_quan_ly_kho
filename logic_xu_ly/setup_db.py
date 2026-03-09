import sqlite3

def setup():
    conn = sqlite3.connect('logic_xu_ly/inventory.db')
    cursor = conn.cursor()
    
    # 1. Bảng Suppliers
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

    # 2. Bảng Customers 
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
    
    # 3. Bảng Products 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            min_threshold INTEGER DEFAULT 10,
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

    # Invoices
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        date TEXT,
        total_amount REAL,
        status TEXT
    )
    ''')

    #login
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        role TEXT
    )
    ''')
    # Thêm một tài khoản mặc định để đăng nhập
    cursor.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin123', 'Administrator')")
    
    conn.commit()
    conn.close()
    print("Đã tạo bảng 'suppliers' 'customers' 'products' 'invoices' thành công!")

if __name__ == "__main__":
    setup()
