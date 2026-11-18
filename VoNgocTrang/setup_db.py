import sqlite3

# Kết nối (hoặc tạo mới) file thoitranggenz.db
conn = sqlite3.connect('thoitranggenz.db')
cursor = conn.cursor()

# Tạo bảng users với cột 'role' (vai trò)
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
''')

# Thêm 2 tài khoản mẫu (1 Admin, 1 Khách hàng)
users_data = [
    ('ngoctrang', '123456', 'admin'),
    ('khachhang', '123', 'user')
]

try:
    cursor.executemany('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', users_data)
    conn.commit()
    print("Đã tạo Database và thêm tài khoản thành công!")
except sqlite3.IntegrityError:
    print("Dữ liệu đã tồn tại, không cần thêm lại.")

conn.close()