import sqlite3

def check_login(username, password):
    conn = sqlite3.connect('logic_xu_ly/inventory.db')
    cursor = conn.cursor()
    
    # Tìm người dùng có username và password khớp
    query = "SELECT role FROM users WHERE username = ? AND password = ?"
    cursor.execute(query, (username, password))
    result = cursor.fetchone() # Trả về dòng chứa 'role' nếu đúng, ngược lại là None
    
    conn.close()
    return result # Trả về ('Administrator',) hoặc None
