import sqlite3

def get_connection():
    return sqlite3.connect('logic_xu_ly/inventory.db')

def add_product(sku, name, category, stock, price, cost, status, min_threshold=10):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(products)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'min_threshold' in columns:
        cursor.execute('''
            INSERT INTO products (min_threshold, sku, name, category, stock, price, cost, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (min_threshold, sku, name, category, stock, price, cost, status))
    else:
        cursor.execute('''
            INSERT INTO products (sku, name, category, stock, price, cost, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (sku, name, category, stock, price, cost, status))

    conn.commit()
    conn.close()

def fetch_all_products():
    conn = get_connection()
    cursor = conn.cursor()
    # Luôn SELECT đúng 7 cột theo thứ tự cố định: sku(0),name(1),category(2),stock(3),price(4),cost(5),status(6)
    cursor.execute("SELECT sku, name, category, stock, price, cost, status FROM products")
    data = cursor.fetchall()
    conn.close()
    return data

def search_products(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT sku, name, category, stock, price, cost, status FROM products WHERE name LIKE ? OR sku LIKE ?"
    cursor.execute(query, (f'%{keyword}%', f'%{keyword}%'))
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_product_status(sku, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET status = ? WHERE sku = ?", (new_status, sku))
    conn.commit()
    conn.close()
def delete_product(sku):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE sku=?", (sku,))
    conn.commit()
    conn.close()
