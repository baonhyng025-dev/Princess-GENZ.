import sqlite3

# Kết nối vào database
conn = sqlite3.connect('thoitranggenz.db')
cursor = conn.cursor()

# Điền thông tin tài khoản bạn muốn tạo ở đây
ten_tai_khoan = 'nhanvien1'
mat_khau = '123'
chuc_vu = 'sub_admin'  # sub_admin là nhân viên, super_admin là sếp

try:
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (ten_tai_khoan, mat_khau, chuc_vu))
    conn.commit()
    print(f"✅ Đã tạo thành công tài khoản: {ten_tai_khoan} - Quyền: {chuc_vu}")
except sqlite3.IntegrityError:
    print("❌ Tên tài khoản này đã tồn tại, hãy chọn tên khác!")

conn.close()