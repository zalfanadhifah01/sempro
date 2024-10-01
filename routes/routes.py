from main import app,bcrypt,s,mail
from flask import render_template,request,jsonify,redirect,url_for,flash,render_template_string
from flask_login import current_user,login_user,login_required,logout_user
from models import db, Product, Recommendation,User,Booking
import re
from flask_mail import Message
from datetime import datetime
from itsdangerous import BadSignature, SignatureExpired
# ==============================================
# Fungsi dan Route lainnya
# ==============================================
# Static Page Routes

# Route untuk tampilan utama
@app.route('/')
def home():
    return render_template('skin_detection.html')

# Route Landing Page
@app.route("/home")
def home_view():
    return render_template("index.html")

# Route untuk halaman login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("history_pemesanan"))
        elif current_user.role == 'user':
            return redirect(url_for("user_get_bookings"))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Mencari user berdasarkan username atau email
        user = User.query.filter_by(username=username).first()

        # Pastikan user ditemukan sebelum login
        if user: 
            if bcrypt.check_password_hash(user.password, password):
                login_user(user)  
                if user.role == "admin":
                    return redirect(url_for('history_pemesanan'))
                else:
                    next_url = request.args.get('next_url')
                    if next_url:
                        return redirect(next_url)
                    else:
                        return redirect(url_for('user_get_bookings'))
            else:
                flash('password salah', 'danger')
        else:
            flash('username tidak ada', 'danger')
    return render_template('admin/login.html')
# Function to validate email format
def is_valid_email(email):
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$'
    return re.match(regex, email)
# Route untuk halaman register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("history_pemesanan"))
        elif current_user.role == 'user':
            return redirect(url_for("user_get_bookings"))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists")
            return redirect(url_for('register'))
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("email already exists")
            return redirect(url_for('register'))
        new_user = User(username=username, email=email, password=password, role='user')
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
            
        token = s.dumps(email, salt='email-confirm')

        conf_email_url = url_for('confirm_email', token=token, _external=True)
        email_body = render_template_string('''
            Hello {{ username }},
            
            Anda menerima email ini, karena kami memerlukan verifikasi email untuk akun Anda agar aktif dan dapat digunakan.
            
            Silakan klik tautan di bawah ini untuk verifikasi email Anda. Tautan ini akan kedaluwarsa dalam 1 jam.
            
            confirm youe email: {{ conf_email_url }}
            
            hubungi dukungan jika Anda memiliki pertanyaan.
            
            Untuk bantuan lebih lanjut, silakan hubungi tim dukungan kami di developer zulfanisa0103@gmail.com .
            
            Salam Hangat,
            
            Admin
        ''', username=username,  conf_email_url=conf_email_url)

        msg = Message('Confirmasi Email Anda',
                    sender='zulfanisa0103@gmail.com', recipients=[email])

        msg.body = email_body
        mail.send(msg)

        flash(" Register berhasil silahkan cek email anda.")
        return redirect(url_for('get_bookings'))
    return render_template('admin/register.html')



@app.route('/confirm_email/<token>', methods=['GET'])
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        return jsonify({"msg": "Token telah kedaluwarsa"}), 400
    except BadSignature:
        return jsonify({"msg": "Token tidak valid"}), 400
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    # Update the verify_email field to True
    user.verify_email = True
    db.session.commit()
    return '''
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <title>Email Verify</title>
      </head>
      <body>
        <h1>Email Telah Terverifikasi </h1>
      </body>
    </html>
    '''.format(token)
@app.route("/verif_email",methods=["GET","POST"])
def verif_email():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"msg": "Email harus diisi"})
            
        user = User.query.filter_by(email=email).first()
        print(user)
        if not user:
            return jsonify({"msg": "Email tidak ditemukan"})

        verified_user = User.query.filter_by(email=email,verify_email=True).first()
        print(verified_user)
        if verified_user:
            return jsonify({"msg": "user sudah terverifikasi"})

        token = s.dumps(email, salt='email-confirm')

        conf_email_url = url_for('confirm_email', token=token, _external=True)
        email_body = render_template_string('''
            Hello {{ username }},
            
            Anda menerima email ini, karena kami memerlukan verifikasi email untuk akun Anda agar aktif dan dapat digunakan.
            
            Silakan klik tautan di bawah ini untuk verifikasi email Anda. Tautan ini akan kedaluwarsa dalam 1 jam.
            
            confirm youe email: {{ conf_email_url }}
            
            hubungi dukungan jika Anda memiliki pertanyaan.
            
            Untuk bantuan lebih lanjut, silakan hubungi tim dukungan kami di developer zulfanisa0103@gmail.com .
            
            Salam Hangat,
            
            Pejuang D4
        ''', username=user.username,  conf_email_url=conf_email_url)

        msg = Message('Confirmasi Email Anda',
                    sender='zulfanisa0103@gmail.com', recipients=[email])

        msg.body = email_body
        mail.send(msg)

        flash("Silahkan cek email anda.")

        return jsonify({"msg":"Silahkan cek email anda."})
    else:
        return render_template("verif_email.html")
    
@app.route("/forgotpassword",methods=["GET","POST"])
def forgot_password():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"msg": "Email harus diisi"})
            
        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({"msg": "Email tidak ditemukan"})

        token = s.dumps(email, salt='reset-password')

        reset_password_url = url_for('reset_password', token=token, _external=True)
        email_body = render_template_string('''
            Hello {{ user["name"] }},
            
            Anda menerima email ini, karena kami menerima permintaan untuk mengatur ulang kata sandi akun Anda.
            
            Silakan klik tautan di bawah ini untuk mengatur ulang kata sandi Anda. Tautan ini akan kedaluwarsa dalam 1 jam.
            
            Reset your password: {{ reset_password_url }}
            
            Jika Anda tidak meminta pengaturan ulang kata sandi, abaikan email ini atau hubungi dukungan jika Anda memiliki pertanyaan.
            
            Untuk bantuan lebih lanjut, silakan hubungi tim dukungan kami di developer zulfanisa0103@gmail.com .
            
            Salam Hangat,
            
            Mriki_Project
        ''', user=user,  reset_password_url=reset_password_url)

        msg = Message('Reset Kata Sandi Anda',
                    sender='zulfanisa0103@gmail.com ', recipients=[email])

        msg.body = email_body
        mail.send(msg)


        return jsonify({"msg": "Email untuk mereset kata sandi telah dikirim."})
    else:
        return render_template("forgot_password.html")


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='reset-password', max_age=3600)
    except SignatureExpired:
        return jsonify({"msg": "Token telah kedaluwarsa"}), 400
    except BadSignature:
        return jsonify({"msg": "Token tidak valid"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({"msg": "User not found"}), 404
    if request.method == 'POST':
        data = request.get_json()
        password = data.get('password')

        # Hash the new password and update it in the database
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()

        flash('Password berhasil direset. Silakan login dengan password baru Anda.')
        return jsonify({"msg": "Sukses"})
    return render_template("reset_password.html",token=token)

# Route untuk logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Route untuk daftar produk
@app.route("/products")
def products():
    products = Product.query.all()
    return render_template("products.html", list_products=products)

# Route untuk detail produk
@app.route("/products_detail/<int:id>")
def products_detail(id):
    product = Product.query.get(id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    bookings = Booking.query.filter_by(product_id=id).all()
    # Ubah booking menjadi list of dictionaries
    bookings_data = []
    for booking in bookings:
        bookings_data.append({
            "id": booking.id,
            "product_id": booking.product_id,
            "user_id": booking.user_id,
            "status": booking.status,
            "product_name": booking.product_name,
            "nama_client": booking.nama_client,
            "alamat": booking.alamat,
            "no_hp": booking.no_hp,
            "tanggal": booking.tanggal,
            "jam": booking.jam
        })
    return render_template("product_detail.html", product=product, bookings=bookings_data)

# Route untuk daftar produk lama
@app.route("/products_old")
def products_old():
    list_products = Product.query.all()
    list_product_by_treatment = [product for product in list_products if product.id in [1, 2, 3, 4, 5]]
    return render_template("products_old.html", list_products=list_product_by_treatment)
def cek(nama):
    if nama == "bv575247-c06d-4e75-2313-931d3df9fd275.jpeg" :
        return "berminyak"
    elif nama == "oc471247-c06d-4e75-9013-97d3df9fd.png":
        return "normal"
    elif nama == "bc421247-c06d-4e15-9013-97d3df9fd24918.jpg":
        return "sensitive"
    elif nama == "ad4752257-c02d-4e75-9013-97d3df9fd321.jpg":
        return "kering"
    elif nama == "bc475247-c06d-4e75-9013-97d3df9fd275.png":
        return "kombinasi"

# API untuk mendapatkan semua produk
@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([product.serialize for product in products])

# API untuk mendapatkan produk berdasarkan ID
@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(product.serialize)

# Route untuk melakukan pemesanan
@app.route('/bookings', methods=['POST'])
@login_required
def book():
    data = request.json if request.is_json else request.form
    product_id = data.get('product_id')
    date = data.get('date', datetime.now().strftime("%Y-%m-%d"))
    time = data.get('time')

    existing_booking = Booking.query.filter_by(product_id=product_id, tanggal=date, jam=time).first()
    if existing_booking:
        if request.is_json:
            return jsonify({'message': 'The selected slot is already booked.'}), 409
        else:
            flash("Slot yang dipilih sudah dipesan.")
            return redirect(url_for('get_bookings'))

    new_booking = Booking(
        product_id=product_id,
        nama_client=current_user.username,
        tanggal=date,
        jam=time,
        status='pending'
    )
    db.session.add(new_booking)
    db.session.commit()

    if request.is_json:
        return jsonify({'message': 'Booking successful'}), 200
    else:
        flash("Booking berhasil dilakukan")
        return redirect(url_for('get_bookings'))



@app.route("/rekomendasi_kering")
def get_rekomendasi_kering():
    rekomendasi = "Rekomendasi Treatment Kulit Kering:<br>"
    list_products = Product.query.all()

    # Pastikan produk yang diakses benar-benar ada
    try:
        rekomendasi += f"1. {list_products[18].nama} {list_products[18].harga}<br>"
        rekomendasi += f"2. {list_products[6].nama} {list_products[6].harga}<br> Paket <br>"
        rekomendasi += f"1. {list_products[9].nama} {list_products[9].harga}<br>"
        rekomendasi += f"2. {list_products[21].nama} {list_products[21].harga}<br><br>"
    except IndexError:
        return "Error: Produk tidak tersedia atau indeks tidak valid."

    return rekomendasi


@app.route("/rekomendasi_berminyak")
def get_rekomendasi_berminyak():
    rekomendasi = "Rekomendasi Treatment Kulit Berminyak:<br>"
    list_products = Product.query.all()

    try:
        rekomendasi += f"1. {list_products[16].nama} {list_products[16].harga}<br>"
        rekomendasi += f"2. {list_products[14].nama} {list_products[14].harga}<br> Paket <br>"
        rekomendasi += f"1. {list_products[10].nama} {list_products[10].harga}<br>"
        rekomendasi += f"2. {list_products[11].nama} {list_products[11].harga}<br><br>"
    except IndexError:
        return "Error: Produk tidak tersedia atau indeks tidak valid."

    return rekomendasi


@app.route("/rekomendasi_normal")
def get_rekomendasi_normal():
    rekomendasi = "Rekomendasi Treatment Kulit Normal:<br>"
    list_products = Product.query.all()

    try:
        rekomendasi += f"1. {list_products[13].nama} {list_products[13].harga}<br>"
        rekomendasi += f"2. {list_products[6].nama} {list_products[6].harga}<br>"
        rekomendasi += f"3. {list_products[14].nama} {list_products[14].harga}<br> Paket <br>"
        rekomendasi += f"1. {list_products[15].nama} {list_products[15].harga}<br>"
        rekomendasi += f"2. {list_products[19].nama} {list_products[19].harga}<br><br>"
    except IndexError:
        return "Error: Produk tidak tersedia atau indeks tidak valid."

    return rekomendasi


@app.route('/delete_recommendation/<int:rec_id>', methods=['POST'])
def delete_recommendation(rec_id):
    try:
        recommendation = Recommendation.query.get(rec_id)
        if recommendation:
            db.session.delete(recommendation)
            db.session.commit()
            flash('Rekomendasi berhasil dihapus!', 'success')
        else:
            flash('Rekomendasi tidak ditemukan.', 'error')
    except Exception as e:
        flash('Terjadi kesalahan saat menghapus rekomendasi.', 'error')
    return redirect(url_for('manage_recommendations'))

