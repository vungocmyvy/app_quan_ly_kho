import sqlite3

# Thống nhất đường dẫn database
DB_PATH = 'logic_xu_ly/inventory.db'

def check_login(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT role FROM users WHERE username = ? AND password = ?"
    cursor.execute(query, (username, password))
    result = cursor.fetchone()
    conn.close()
    return result

def register_user(username, password, role="User"):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       (username, password, role))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
def update_password(username, new_password):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
        conn.commit()
        updated_rows = cursor.rowcount
        conn.close()
        return updated_rows > 0
    except Exception as e:
        print(f"Lỗi update: {e}")
        return False
