# app.py - PHIÊN BẢN CUỐI CÙNG - DUYỆT 2 CẤP HOÀN HẢO
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from functools import wraps
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "DTA_SPACE_2025_FINAL_SECRET_KEY"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT,
            department TEXT,
            city TEXT,
            content TEXT,
            nguon_kinh_phi TEXT,
            approver TEXT NOT NULL,
            submitter TEXT NOT NULL,
            submitter_name TEXT NOT NULL,
            submit_date TEXT NOT NULL,
            status TEXT DEFAULT 'Chờ duyệt',
            attachment TEXT,
            total_cost REAL DEFAULT 0,
            next_approver TEXT
        )
    ''')
    # Thêm cột nếu chưa có
    for col in ["total_cost REAL DEFAULT 0", "next_approver TEXT"]:
        try:
            col_name = col.split()[0]
            c.execute(f"ALTER TABLE proposals ADD COLUMN {col}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()

# === NGƯỜI DÙNG ===
USERS = {
    # ==================== BOD ====================
    "truongkhuong@dieutuongam.com": {"name": "TRƯƠNG HUỆ KHƯƠNG",           "role": "BOD",       "department": "BOD",                                   "password": "123456"},
    "uthue.dta@gmail.com":          {"name": "NGUYỄN THỊ HUỆ",              "role": "BOD",       "department": "BOD",                                   "password": "123456"},

    # ==================== PHÒNG HCNS-IT ====================
    "it@dieutuongam.com":           {"name": "TRẦN CÔNG KHÁNH",             "role": "Manager",   "department": "PHÒNG HCNS-IT",                         "password": "123456"},
    "anthanh@dieutuongam.com":      {"name": "NGUYỄN THỊ AN THANH",         "role": "Manager",   "department": "PHÒNG HCNS-IT",                         "password": "123456"},
    "hcns@dieutuongam.com":         {"name": "NHÂN SỰ DTA",                 "role": "Employee",  "department": "PHÒNG HCNS-IT",                         "password": "123456"},
    "yennhi@dieutuongam.com":       {"name": "TRẦN NGỌC YẾN NHI",           "role": "Employee",  "department": "PHÒNG HCNS-IT",                         "password": "123456"},
    "info@dieutuongam.com":         {"name": "Trung Tâm Nghệ Thuật Phật Giáo Diệu Tướng Am", "role": "Employee", "department": "PHÒNG HCNS-IT",              "password": "123456"},

    # ==================== PHÒNG TÀI CHÍNH KẾ TOÁN ====================
    "ketoan@dieutuongam.com":       {"name": "LÊ THỊ MAI ANH",              "role": "Manager",   "department": "PHÒNG TÀI CHÍNH KẾ TOÁN",                "password": "123456"},

    # ==================== PHÒNG KINH DOANH HCM ====================
    "xuanhoa@dieutuongam.com":      {"name": "LÊ XUÂN HOA",                 "role": "Manager",   "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "salesadmin@dieutuongam.com":   {"name": "NGUYỄN DUY ANH",              "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "hatrang@dieutuongam.com":      {"name": "PHẠM HÀ TRANG",               "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "hongtuyet@dieutuongam.com":    {"name": "NGUYỄN THỊ HỒNG TUYẾT",       "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "kho@dieutuongam.com":          {"name": "HUỲNH MINH TOÀN",             "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "thoainha@dieutuongam.com":     {"name": "TRẦN THOẠI NHÃ",              "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "troly@dieutuongam.com":        {"name": "NGUYỄN NGỌC DUY",             "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "thanhtuan.dta@gmail.com":      {"name": "BÀNH THANH TUẤN",             "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "thientinh.dta@gmail.com":      {"name": "BÙI THIỆN TÌNH",              "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "giathanh.dta@gmail.com":       {"name": "NGÔ GIA THÀNH",               "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "vannhuann.dta@gmail.com":      {"name": "PHẠM VĂN NHUẬN",              "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "minhhieuu.dta@gmail.com":      {"name": "LÊ MINH HIẾU",                "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "thanhtrung.dta@gmail.com":     {"name": "NGUYỄN THÀNH TRUNG",          "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "khanhngan.dta@gmail.com":      {"name": "NGUYỄN NGỌC KHÁNH NGÂN",      "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "thitrang.dta@gmail.com":       {"name": "NGUYỄN THỊ TRANG",            "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "thanhtienn.dta@gmail.com":     {"name": "NGUYỄN THANH TIẾN",           "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},

    # ==================== PHÒNG KINH DOANH HN ====================
    "nguyenngoc@dieutuongam.com":   {"name": "NGUYỄN THỊ NGỌC",             "role": "Manager",   "department": "PHÒNG KINH DOANH HN",                   "password": "123456"},
    "vuthuy@dieutuongam.com":       {"name": "VŨ THỊ THÙY",                 "role": "Employee",  "department": "PHÒNG KINH DOANH HN",                   "password": "123456"},
    "mydung.dta@gmail.com":         {"name": "HOÀNG THỊ MỸ DUNG",           "role": "Employee",  "department": "PHÒNG KINH DOANH HN",                   "password": "123456"},

    # ==================== PHÒNG TRUYỀN THÔNG & MARKETING ====================
    "marketing@dieutuongam.com":    {"name": "TUYỀN HUỲNH",                 "role": "Manager",   "department": "PHÒNG TRUYỀN THÔNG & MARKETING",         "password": "123456"},
    "hotro-kythuat@dieutuongam.com":{"name": "ĐỖ BÌNH TRỌNG",            "role": "Manager",   "department": "PHÒNG TRUYỀN THÔNG & MARKETING",         "password": "123456"},
    "ngocloi.dta@gmail.com":        {"name": "LÊ NGỌC LỢI",                 "role": "Employee",  "department": "PHÒNG TRUYỀN THÔNG & MARKETING",         "password": "123456"},
    "lehong.dta@gmail.com":         {"name": "LÊ THỊ HỒNG",                 "role": "Employee",  "department": "PHÒNG TRUYỀN THÔNG & MARKETING",         "password": "123456"},

    # ==================== PHÒNG KẾ HOẠCH TỔNG HỢP ====================
    "lehuyen@dieutuongam.com":      {"name": "NGUYỄN THỊ LỆ HUYỀN",         "role": "Manager",   "department": "PHÒNG KẾ HOẠCH TỔNG HỢP",               "password": "123456"},

    # ==================== PHÒNG SÁNG TẠO TỔNG HỢP ====================
    "thietke@dieutuongam.com":      {"name": "ĐẶNG THỊ MINH THÙY",          "role": "Manager",   "department": "PHÒNG SÁNG TẠO TỔNG HỢP",                "password": "123456"},
    "ptsp@dieutuongam.com":         {"name": "DƯƠNG NGỌC HIỂU",             "role": "Employee",  "department": "PHÒNG SÁNG TẠO TỔNG HỢP",                "password": "123456"},
    "qlda@dieutuongam.com":         {"name": "PHẠM THẾ HẢI",                "role": "Employee",  "department": "PHÒNG SÁNG TẠO TỔNG HỢP",                "password": "123456"},
    "minhdat.dta@gmail.com":        {"name": "LÂM MINH ĐẠT",                "role": "Employee",  "department": "PHÒNG SÁNG TẠO TỔNG HỢP",                "password": "123456"},
    "thanhvii.dat@gmail.com":       {"name": "LÊ THỊ THANH VI",             "role": "Employee",  "department": "PHÒNG SÁNG TẠO TỔNG HỢP",                "password": "123456"},
    "quangloi.dta@gmail.com":       {"name": "LÊ QUANG LỢI",                "role": "Employee",  "department": "PHÒNG SÁNG TẠO TỔNG HỢP",                "password": "123456"},
    "tranlinh.dta@gmail.com":       {"name": "NGUYỄN THỊ PHƯƠNG LINH",      "role": "Employee",  "department": "PHÒNG SÁNG TẠO TỔNG HỢP",                "password": "123456"},

    # ==================== BỘ PHẬN HỖ TRỢ - GIAO NHẬN ====================
    "hotro1.dta@gmail.com":         {"name": "NGUYỄN VĂN MẠNH",             "role": "Employee",  "department": "BỘ PHẬN HỖ TRỢ - GIAO NHẬN",              "password": "123456"},
}

DEPARTMENTS = ["PHÒNG HCNS-IT", "PHÒNG KINH DOANH HCM", "PHÒNG KINH DOANH HN",
               "PHÒNG TRUYỀN THÔNG & MARKETING", "PHÒNG TÀI CHÍNH KẾ TOÁN",
               "PHÒNG KẾ HOẠCH TỔNG HỢP", "PHÒNG SÁNG TẠO TỔNG HỢP", "BOD"]

NGUON_KINH_PHI = ["Ngân sách năm đã duyệt", "Dự phòng lãnh đạo", "Khoản mục khác"]

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user"):
            flash("Vui lòng đăng nhập để tiếp tục!", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        session.clear()
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = USERS.get(email)
        if user and user["password"] == password:
            session["user"] = {
                "email": email,
                "name": user["name"],
                "role": user["role"],
                "department": user["department"]
            }
            flash(f"Đăng nhập thành công! Chào {user['name']}", "success")
            return redirect(url_for("dashboard"))
        flash("Email hoặc mật khẩu không đúng!", "danger")
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    user = session["user"]
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    my_name = f"{user['name']} - {user['department']}"
    c.execute("""
        SELECT * FROM proposals 
        WHERE (approver = ? OR next_approver = ?) 
        AND status IN ('Chờ duyệt', 'Chờ duyệt cấp 2')
        ORDER BY id DESC
    """, (my_name, my_name))
    pending = c.fetchall()
    conn.close()
    return render_template("dashboard.html", user=user, pending=pending)

@app.route("/proposal", methods=["GET", "POST"])
@login_required
def proposal():
    user = session["user"]
    if user["email"] == "truongkhuong@dieutuongam.com":
        flash("Tài khoản BOD không được phép tạo đề xuất mới.", "warning")
        return redirect(url_for("dashboard"))
    
    today = datetime.now().strftime("%d/%m/%Y")

    if request.method == "POST":
        title = request.form.get("title")
        dept = request.form.get("department")
        city = request.form.get("city")
        ptype = request.form.get("type")
        content = request.form.get("content")
        nguon = request.form.get("nguon_kinh_phi")
        approver = request.form.get("approver")
        total_cost = float(request.form.get("total_cost", 0))
        file = request.files.get("attachment")

        if not all([title, dept, ptype, content, nguon, approver]):
            flash("Vui lòng điền đầy đủ các trường bắt buộc!", "danger")
            return redirect(url_for("proposal"))

        filename = None
        if file and file.filename:
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            INSERT INTO proposals 
            (title, type, department, city, content, nguon_kinh_phi, approver, 
             submitter, submitter_name, submit_date, total_cost, attachment, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Chờ duyệt')
        ''', (title, ptype, dept, city, content, nguon, approver,
              user["email"], user["name"], today, total_cost, filename))
        conn.commit()
        conn.close()
        flash(f"Đề xuất '{title}' đã được gửi thành công!", "success")
        return redirect(url_for("proposal"))

    approvers = [f"{v['name']} - {v['department']}" for k, v in USERS.items() if v["role"] in ["Manager", "BOD"]]
    return render_template("proposal.html",
                           user=user, departments=DEPARTMENTS,
                           approvers=approvers, today=today,
                           nguon_kinh_phi_list=NGUON_KINH_PHI)

@app.route("/list")
@login_required
def proposal_list():
    user = session["user"]
    if user["role"] not in ["Manager", "BOD"]:
        flash("Bạn không có quyền xem trang này!", "danger")
        return redirect(url_for("dashboard"))

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM proposals ORDER BY id DESC")
    proposals = c.fetchall()
    conn.close()
    return render_template("proposal_list.html", user=user, proposals=proposals)

@app.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/approve/<int:prop_id>", methods=["GET", "POST"])
@login_required
def approve(prop_id):
    user = session["user"]
    if user["role"] not in ["Manager", "BOD"]:
        flash("Bạn không có quyền duyệt!", "danger")
        return redirect(url_for("dashboard"))

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM proposals WHERE id = ?", (prop_id,))
    proposal = c.fetchone()
    if not proposal:
        flash("Đề xuất không tồn tại!", "danger")
        conn.close()
        return redirect(url_for("dashboard"))

    my_full = f"{user['name']} - {user['department']}"
    original_approver = proposal[7]   # Người được chọn lúc tạo đề xuất
    next_approver = proposal[14] if len(proposal) > 14 else None
    status = proposal[11]

    # Xác định người đang được phân công duyệt hiện tại
    current_turn = next_approver if next_approver else original_approver

    if current_turn != my_full:
        flash("Chưa đến lượt bạn duyệt đề xuất này!", "danger")
        conn.close()
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        decision = request.form.get("decision")
        next_person = request.form.get("next_approver")

        if decision == "reject":
            c.execute("UPDATE proposals SET status = 'Từ chối', next_approver = NULL WHERE id = ?", (prop_id,))
            conn.commit()
            flash(f"Đề xuất #{prop_id} đã bị TỪ CHỐI!", "danger")

        elif decision == "approve":
            # Nếu người hiện tại là BOD → kết thúc luôn
            if user["role"] == "BOD":
                c.execute("UPDATE proposals SET status = 'Đã duyệt', next_approver = NULL WHERE id = ?", (prop_id,))
                conn.commit()
                flash(f"BOD đã DUYỆT HOÀN TẤT đề xuất #{prop_id}!", "success")

            else:
                # Nếu chọn người tiếp theo là BOD → chuyển cho BOD (sẽ là người cuối)
                if next_person:
                    selected_name = next_person.split(" - ")[0].strip()
                    is_bod_next = any(
                        info["name"] == selected_name and info["role"] == "BOD"
                        for info in USERS.values()
                    )

                    if is_bod_next:
                        c.execute("UPDATE proposals SET next_approver = ? WHERE id = ?", (next_person, prop_id))
                        conn.commit()
                        flash(f"Đã duyệt → Chuyển cho BOD: {selected_name} → Đây sẽ là người duyệt cuối cùng", "success")
                    else:
                        c.execute("UPDATE proposals SET next_approver = ? WHERE id = ?", (next_person, prop_id))
                        conn.commit()
                        flash(f"Đã duyệt → Chuyển tiếp cho: {selected_name}", "success")
                else:
                    flash("Vui lòng chọn người phê duyệt tiếp theo!", "warning")
                    conn.close()
                    approvers = [f"{v['name']} - {v['department']}" for k, v in USERS.items() if v["role"] in ["Manager", "BOD"]]
                    return render_template("approve_form.html", proposal=proposal, approvers=approvers, is_bod=(user["role"] == "BOD"))

        conn.close()
        return redirect(url_for("dashboard"))

    # GET: hiển thị form
    approvers = [f"{v['name']} - {v['department']}" for k, v in USERS.items() if v["role"] in ["Manager", "BOD"]]
    is_bod = (user["role"] == "BOD")
    conn.close()
    return render_template("approve_form.html", proposal=proposal, approvers=approvers, is_bod=is_bod)
@app.route("/logout")
def logout():
    session.clear()
    flash("Bạn đã đăng xuất thành công!", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()
    print("="*60)
    print("HỆ THỐNG ĐÃ CHẠY THÀNH CÔNG! - DUYỆT 2 CẤP HOÀN HẢO")
    print("→ Truy cập: http://192.168.1.130:5000")
    print("="*60)
    app.run(host="0.0.0.0", port=5000, debug=False)