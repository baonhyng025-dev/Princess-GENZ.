from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = 'khoa_bi_mat_cua_ngoc_trang'

DB_NAME = 'thoitrang_v8.db'

@app.context_processor
def inject_cart_count():
    count = 0
    if session.get('username'):
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(quantity) FROM cart WHERE username = ?", (session['username'],))
            result = cursor.fetchone()[0]
            if result: count = result
            conn.close()
        except: pass
    return dict(cart_count=count)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, price REAL NOT NULL, stock INTEGER NOT NULL, image TEXT NOT NULL, category TEXT DEFAULT 'Hiện Đại')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cart (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, product_id INTEGER NOT NULL, quantity INTEGER DEFAULT 1)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, product_name TEXT NOT NULL, price REAL NOT NULL, quantity INTEGER NOT NULL, total_price REAL NOT NULL, phone TEXT, address TEXT, payment TEXT, status TEXT DEFAULT 'Chờ duyệt')''')

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('ngoctrang', '123456', 'super_admin')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('nhanvien1', '123', 'sub_admin')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('khachhang', '123', 'user')")
    
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        categories = ['Váy Dài', 'Váy Ngắn', 'Công Chúa', 'Phối Đồ', 'Hiện Đại']
        images = ['sp1.jpg', 'sp2.jpg', 'sp3.jpg', 'sp4.jpg']
        sample_products = []
        
        for cat in categories:
            for i in range(1, 17):
                name = f"Thiết Kế {cat} Mộng Mơ - Mẫu {i}"
                price = 350000 + (i * 25000)
                stock = 10 + i
                img = images[i % 4]
                sample_products.append((name, price, stock, img, cat))
                
        cursor.executemany("INSERT INTO products (name, price, stock, image, category) VALUES (?, ?, ?, ?, ?)", sample_products)
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    cursor.execute("SELECT * FROM products WHERE id != ? LIMIT 4", (product_id,))
    related_products = cursor.fetchall()
    conn.close()
    if product:
        return render_template('product.html', product=product, related_products=related_products)
    return "Không tìm thấy vật phẩm!", 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['username'] = user[1]
            session['role'] = user[3]
            if session['role'] in ['super_admin', 'sub_admin']: return redirect(url_for('admin_page', tab='dashboard'))
            else: return redirect(url_for('index'))
        else: error = "Tên đăng nhập hoặc mật khẩu sai!"
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone(): error = "Tên đăng nhập này đã có người sử dụng!"
        else:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'user')", (username, password))
            conn.commit(); conn.close()
            return redirect(url_for('login'))
        conn.close()
    return render_template('register.html', error=error)

@app.route('/add_to_cart/<int:product_id>', methods=['GET', 'POST'])
def add_to_cart(product_id):
    if not session.get('username'): return redirect(url_for('login'))
    qty = int(request.form.get('quantity', 1)) if request.method == 'POST' else 1
    action = request.form.get('action', 'add') if request.method == 'POST' else 'add'
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM cart WHERE username = ? AND product_id = ?", (session['username'], product_id))
    item = cursor.fetchone()
    if item: cursor.execute("UPDATE cart SET quantity = quantity + ? WHERE id = ?", (qty, item[0]))
    else: cursor.execute("INSERT INTO cart (username, product_id, quantity) VALUES (?, ?, ?)", (session['username'], product_id, qty))
    conn.commit(); conn.close()
    if action == 'buy': return redirect(url_for('cart'))
    else: return redirect(request.referrer or url_for('index'))

@app.route('/update_cart_qty/<int:cart_id>/<action>')
def update_cart_qty(cart_id, action):
    if not session.get('username'): return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT quantity FROM cart WHERE id = ? AND username = ?", (cart_id, session['username']))
    item = cursor.fetchone()
    if item:
        qty = item[0]
        if action == 'increase': cursor.execute("UPDATE cart SET quantity = quantity + 1 WHERE id = ?", (cart_id,))
        elif action == 'decrease':
            if qty > 1: cursor.execute("UPDATE cart SET quantity = quantity - 1 WHERE id = ?", (cart_id,))
            else: cursor.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
    conn.commit(); conn.close()
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:cart_id>')
def remove_from_cart(cart_id):
    if not session.get('username'): return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE id = ? AND username = ?", (cart_id, session['username']))
    conn.commit(); conn.close()
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    if not session.get('username'): return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT cart.id, products.name, products.price, cart.quantity, products.image, products.id FROM cart JOIN products ON cart.product_id = products.id WHERE cart.username = ?', (session['username'],))
    cart_items = cursor.fetchall()
    total = sum(item[2] * item[3] for item in cart_items)
    conn.close()
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/checkout', methods=['POST'])
def checkout():
    if not session.get('username'): return redirect(url_for('login'))
    phone, address, payment = request.form.get('phone', ''), request.form.get('address', ''), request.form.get('payment', 'COD')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT products.name, products.price, cart.quantity, products.id FROM cart JOIN products ON cart.product_id = products.id WHERE cart.username = ?', (session['username'],))
    cart_items = cursor.fetchall()
    for item in cart_items:
        name, price, qty, prod_id = item
        cursor.execute("INSERT INTO orders (username, product_name, price, quantity, total_price, phone, address, payment) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (session['username'], name, price, qty, price * qty, phone, address, payment))
        cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, prod_id))
    cursor.execute("DELETE FROM cart WHERE username = ?", (session['username'],))
    conn.commit(); conn.close()
    return redirect(url_for('success_page'))

@app.route('/success')
def success_page(): return "<h1 style='text-align:center; margin-top:50px; font-family:sans-serif;'>✨ Thư đặt hàng đã được gửi đến Vương Quốc! <br><br> <a href='/' style='color:#ec4899; text-decoration:none;'>Về trang chủ</a></h1>"

# --- THUẬT TOÁN XÉT DUYỆT THẺ VIP NẰM Ở ĐÂY ---
@app.route('/my_orders')
def my_orders():
    if not session.get('username'): return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Lấy toàn bộ lịch sử đơn hàng
    cursor.execute("SELECT id, product_name, price, quantity, total_price, status, phone, address, payment FROM orders WHERE username = ? ORDER BY id DESC", (session['username'],))
    orders = cursor.fetchall()
    
    # 2. Tính tổng tiền CÁC ĐƠN ĐÃ HOÀN THÀNH (chỉ đơn giao thành công mới được cộng điểm VIP)
    cursor.execute("SELECT SUM(total_price) FROM orders WHERE username = ? AND status = 'Hoàn thành'", (session['username'],))
    total_spend_result = cursor.fetchone()[0]
    total_spend = total_spend_result if total_spend_result else 0
    
    # 3. Thuật toán phân hạng thẻ
    tier = 'Thành Viên'
    next_tier = 'Hạng Bạc'
    target = 2000000
    
    if total_spend >= 15000000:
        tier = 'Kim Cương'
        next_tier = 'MAX'
        target = 15000000
    elif total_spend >= 5000000:
        tier = 'Hạng Vàng'
        next_tier = 'Kim Cương'
        target = 15000000
    elif total_spend >= 2000000:
        tier = 'Hạng Bạc'
        next_tier = 'Hạng Vàng'
        target = 5000000
        
    progress = (total_spend / target) * 100 if target > 0 else 0
    progress = min(progress, 100) # Khóa tiến trình không vượt quá 100%
    
    conn.close()
    return render_template('my_orders.html', orders=orders, total_spend=total_spend, tier=tier, next_tier=next_tier, target=target, progress=progress)

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

@app.route('/admin')
@app.route('/admin/<tab>')
def admin_page(tab='dashboard'):
    if session.get('role') not in ['super_admin', 'sub_admin']: return "Không có quyền!", 403
    if session.get('role') == 'sub_admin' and tab in ['users', 'dashboard']: return redirect(url_for('admin_page', tab='orders'))
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    products, orders, users, stats = [], [], [], {}
    if tab == 'products': cursor.execute("SELECT * FROM products"); products = cursor.fetchall()
    elif tab == 'orders': cursor.execute("SELECT * FROM orders ORDER BY id DESC"); orders = cursor.fetchall()
    elif tab == 'users' and session.get('role') == 'super_admin': cursor.execute("SELECT id, username, role FROM users"); users = cursor.fetchall()
    elif tab == 'dashboard' and session.get('role') == 'super_admin':
        cursor.execute("SELECT SUM(total_price) FROM orders WHERE status = 'Hoàn thành'"); rev = cursor.fetchone()[0]; stats['revenue'] = rev if rev else 0
        cursor.execute("SELECT COUNT(*) FROM orders"); stats['total_orders'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users"); stats['total_users'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM products"); stats['total_products'] = cursor.fetchone()[0]
    conn.close()
    return render_template('admin.html', active_tab=tab, products=products, users=users, orders=orders, stats=stats)

@app.route('/admin/update_order/<int:order_id>', methods=['POST'])
def update_order(order_id):
    conn = sqlite3.connect(DB_NAME); conn.execute("UPDATE orders SET status = ? WHERE id = ?", (request.form.get('status'), order_id)); conn.commit(); conn.close()
    return redirect(url_for('admin_page', tab='orders'))

@app.route('/info/<slug>')
def info_page(slug):
    pages = {
        'size': {
            'title': '📐 Hướng Dẫn Chọn Size',
            'content': '''
                <h3 class="text-xl font-bold text-pink-500 mb-4">1. Bảng Size Tiêu Chuẩn</h3>
                <div class="overflow-x-auto mb-8">
                    <table class="w-full text-left border-collapse rounded-2xl overflow-hidden shadow-sm">
                        <thead><tr class="bg-gradient-to-r from-pink-100 to-purple-100 text-pink-600"><th class="p-4">Size</th><th class="p-4">Cân nặng (kg)</th><th class="p-4">Vòng eo (cm)</th><th class="p-4">Vòng 1 (cm)</th></tr></thead>
                        <tbody class="bg-white">
                            <tr class="border-b border-pink-50"><td class="p-4 font-bold text-gray-700">S (Small)</td><td class="p-4 text-gray-600">40 - 47 kg</td><td class="p-4 text-gray-600">58 - 64 cm</td><td class="p-4 text-gray-600">78 - 83 cm</td></tr>
                            <tr class="border-b border-pink-50 bg-pink-50/30"><td class="p-4 font-bold text-gray-700">M (Medium)</td><td class="p-4 text-gray-600">48 - 54 kg</td><td class="p-4 text-gray-600">65 - 70 cm</td><td class="p-4 text-gray-600">84 - 88 cm</td></tr>
                            <tr><td class="p-4 font-bold text-gray-700">L (Large)</td><td class="p-4 text-gray-600">55 - 60 kg</td><td class="p-4 text-gray-600">71 - 76 cm</td><td class="p-4 text-gray-600">89 - 94 cm</td></tr>
                        </tbody>
                    </table>
                </div>
                <h3 class="text-xl font-bold text-purple-500 mb-3">2. Lưu ý từ Tinh Linh Thợ May</h3>
                <p class="text-gray-600 leading-relaxed bg-purple-50 p-6 rounded-2xl border border-purple-100">Nếu số đo của công chúa nằm giữa 2 size, hãy ưu tiên chọn size lớn hơn để có cảm giác thoải mái nhất khi diện váy lấp lánh nhé.</p>
            '''
        },
        'doi-tra': {
            'title': '🔄 Chính Sách Đổi Trả',
            'content': '<p>Đổi trả miễn phí 30 ngày nếu sản phẩm còn nguyên tag.</p>'
        },
        'bao-mat': {
            'title': '🛡️ Chính Sách Bảo Mật',
            'content': '<p>Dữ liệu cá nhân và thanh toán được mã hóa đa tầng tuyệt đối an toàn.</p>'
        },
        'vip': {
            'title': '👑 Đặc Quyền Thẻ VIP',
            'content': '<p>Tích lũy mua sắm từ 2Tr (Hạng Bạc), 5Tr (Hạng Vàng), 15Tr (Kim Cương) để nhận ưu đãi lên đến 15%.</p>'
        },
        'store': {
            'title': '🏰 Hệ Thống Lâu Đài',
            'content': '<p>Ghé thăm các store tại TP.HCM và Hà Nội để thử đồ trực tiếp nhé.</p>'
        },
        'tra-cuu': {
            'title': '🚐 Tra Cứu Đơn Hàng',
            'content': '<p>Quý khách có thể xem trạng thái đơn hàng trực tiếp trong mục "Tài khoản -> Đơn Hàng".</p>'
        }
    }
    
    page_data = pages.get(slug, {'title': 'Trang Thông Tin', 'content': '<p>Đang cập nhật...</p>'})
    return render_template('info.html', title=page_data['title'], content=page_data['content'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8000)