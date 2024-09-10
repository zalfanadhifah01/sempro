from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, Response,abort,send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from models import db, User, Product, HistoryDeteksi, Booking
import os, uuid, json, random, string, pickle,nltk, eventlet,io,base64,sys
import numpy as np
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from keras.models import load_model
from copy import deepcopy
from datetime import datetime
from collections import defaultdict
from PIL import Image
import gc
import tensorflow as tf
import cv2
import torch
from torchvision import transforms
from torch import nn
from torchvision.models import resnet50, ResNet50_Weights
from flask_socketio import SocketIO, emit
from flask_bcrypt import Bcrypt
from functools import wraps
from flask_cors import CORS
# Konfigurasi Aplikasi Flask
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
project_directory = os.path.abspath(os.path.dirname(__file__))
upload_folder = os.path.join(project_directory, 'static', 'upload')
app.config['UPLOAD_FOLDER'] = upload_folder
app.config['SECRET_KEY'] = 'dmo42901i41;/.p`'
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT', b'asayibiuuoyo192382qo')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
db.init_app(app)
bcrypt = Bcrypt(app)

# Allow CORS
CORS(app)

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(app.static_folder, 'sitemap.xml')

@app.route('/robots.txt')
def robots():
    return """User-agent: *
    Disallow: /private/
    Disallow: /cgi-bin/
    Disallow: /images/
    Disallow: /pages/thankyou.html
    """

@app.errorhandler(404)
def page_not_found(error):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'Not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404

@app.route('/invalid')
def invalid():
    abort(404)

def login_role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'id' not in session:
                return redirect(url_for('login'))
            if session.get('role') != required_role:
                return jsonify({"msg": "Permission denied"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
# Create tables
def create_tables():
    with app.app_context():
        db.create_all()

class LoginUser(UserMixin):
    def __init__(self, id, username, password, role):
        self.id = id
        self.username = username
        self.password = password
        self.role = role

    def get_role(self):
        return self.role

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user:
        return LoginUser(user.id, user.username, user.password, user.role)
    
# ==========================================================
# Chatbot Functionality
# ==========================================================

# Variabel Global untuk Chatbot
global responses, lemmatizer, tokenizer, le, model, input_shape
input_shape = 11

# Load response dataset
def load_response():
    global responses
    responses = {}
    file_path = os.path.join(project_directory, 'model_chatbot','dataset.json')
    with open(file_path,encoding='utf-8') as file:
        data = json.load(file)
    for intent in data['intents']:
        responses[intent['tag']] = intent['responses']

# Preparation function
def preparation():
    load_response()
    global lemmatizer, tokenizer, le, model
    file_path = os.path.join(project_directory, 'model_chatbot','tokenizers.pkl')
    with open(file_path, 'rb') as f:
        tokenizer = pickle.load(f)
    le_path = os.path.join(project_directory,'model_chatbot','le.pkl')
    le = pickle.load(open(le_path, 'rb'))
    model_path = os.path.join(project_directory,'model_chatbot2','chatbot_model.h5')
    model = load_model(model_path)
    #model = load_model('model_chatbot2/chatbot_model.h5')
    lemmatizer = WordNetLemmatizer()
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

# Function to remove punctuation
def remove_punctuation(text):
    return ''.join([char.lower() for char in text if char not in string.punctuation])

# Function to convert text to vector
def vectorization(text):
    text = remove_punctuation(text)
    vector = tokenizer.texts_to_sequences([text])
    vector = np.array(vector).reshape(-1)
    vector = pad_sequences([vector], maxlen=input_shape)
    return vector

# Function to predict response tag
def predict(vector):
    output = model.predict(vector)
    output = output.argmax()
    response_tag = le.inverse_transform([output])[0]
    return response_tag

# Function to generate response
def generate_response(text):
    vector = vectorization(text)
    response_tag = predict(vector)
    if response_tag == "jenis kulit saya normal":
        session["jenis_kulit"]="normal"
        return response_tag
    elif response_tag == "jenis kulit saya berminyak":
        session["jenis_kulit"]="berminyak"
        return response_tag
    elif response_tag == "jenis kulit saya kering":
        session["jenis_kulit"]="kering"
        return response_tag
    elif response_tag not in responses:
        return "Sorry, I didn't understand."
    answer = random.choice(responses[response_tag])
    return answer

# Persiapan Chatbot
preparation()

# Chatbot Routes
@app.route("/bot")
def chatbot():
    return render_template("chatbot.html")

@app.route("/get")
def get_bot_response():
    user_input = str(request.args.get('msg'))
    result = generate_response(user_input)
    return str(result)

# ==============================================
# Fungsi dan Route untuk Prediksi Kulit
# ==============================================
# Mapping antara label dan index


# Mapping label dan index

# WebSocket event for receiving image frames and sending back prediction
socketio = SocketIO(app, async_mode='eventlet')

@socketio.on('image_frame')
def handle_image(data_image):
    # Decode base64 image data
    sbuf = io.BytesIO(base64.b64decode(data_image))
    frame = np.array(Image.open(sbuf))

    # Predict skin type from the frame
    result = predict_skin(frame)
    # Bebaskan RAM setelah prediksi
    del frame
    gc.collect()
    # Send the prediction result back to the client
    emit('prediction', {'skin_type': result})

label_index = {"dry": 0, "normal": 1, "oily": 2, "kombinasi": 3, "sensitive": 4}
index_label = {0: "kering", 1: "normal", 2: "berminyak", 3: "kombinasi", 4: "sensitive"}
LR = 0.1
STEP = 15
GAMMA = 0.1
OUT_CLASSES = 3
IMG_SIZE = 224

resnet = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
num_ftrs = resnet.fc.in_features
resnet.fc = nn.Linear(num_ftrs, OUT_CLASSES)
device = "cuda" if torch.cuda.is_available() else "cpu"
model_skin = deepcopy(resnet)
model_skin = model_skin.to(device)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model_skin.parameters(), lr=LR)
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=STEP, gamma=GAMMA)

# Load the checkpoint
model_location = os.path.join(project_directory,'model_detection','best_model_checkpoint_old.pth')
checkpoint = torch.load(model_location, map_location=torch.device('cpu'))
model_skin.load_state_dict(checkpoint['model_state_dict'])
optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
scheduler.load_state_dict(checkpoint['scheduler_state_dict'])

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Deteksi wajah dan prediksi jenis kulit
def predict_skin(frame):
    prototxt = os.path.join(project_directory,'model_detection','deploy.prototxt')
    mobile_net_ssd = os.path.join(project_directory,'model_detection','res10_300x300_ssd_iter_140000.caffemodel')
    net = cv2.dnn.readNetFromCaffe(prototxt, mobile_net_ssd)

    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()

    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
            face = frame[startY:endY, startX:endX]

            # Proses prediksi kulit
            img = Image.fromarray(cv2.cvtColor(face, cv2.COLOR_BGR2RGB)).convert("RGB")
            img = transform(img).unsqueeze(0).to(device)

            model_skin.eval()
            with torch.no_grad():
                out = model_skin(img)
                index = out.argmax(1).item()
                return index_label[index]

    return None


# Route utama untuk halaman HTML
@app.route('/cobaa')
def index():
    return render_template('cobaa.html')

# Skin Detection Routes
@app.route("/skin_detection")
def skin_detection():
    return redirect(url_for('home'))
@app.route("/skin_detection_submit", methods=["POST"])
def skin_detection_submit():
    file = request.files['gambar']
    try:
        img = Image.open(file)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        random_name = uuid.uuid4().hex + ".jpg"
        destination = os.path.join(app.config['UPLOAD_FOLDER'], random_name)
        img.save(destination)
        
        # Membaca gambar sebagai numpy array
        img_array = np.array(Image.open(destination))

        hasil = predict_skin(img_array)  # Memasukkan array gambar, bukan path
        if not hasil:
            return jsonify({"msg": "Gagal, Tidak Terdeteksi Wajah"})
        session["jenis_kulit"] = hasil
        # Bebaskan RAM setelah prediksi
        del img
        gc.collect()
        if current_user.is_authenticated:
            new_history_deteksi = HistoryDeteksi(
                username=current_user.username,
                tanggal=datetime.now().strftime("%Y-%m-%d"),
                image_url=f"/static/upload/{random_name}",
                terdeteksi_kulit=hasil
            )
            db.session.add(new_history_deteksi)
            db.session.commit()
            return jsonify({"msg": "SUKSES_simpan", "hasil": hasil, "img": random_name})
        else:
            return jsonify({"msg": "SUKSES", "hasil": hasil, "img": random_name})

    except Exception as e:
        return jsonify({"error": str(e)})


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
                    return redirect(url_for('user_get_bookings'))
            else:
                flash('password salah', 'danger')
        else:
            flash('username tidak ada', 'danger')
    return render_template('admin/login.html')

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
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists")
            return redirect(url_for('register'))
        new_user = User(username=username, password=password, role='user')
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('get_bookings'))
    return render_template('admin/register.html')

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
    return render_template("product_detail.html", product=product, bookings=bookings)

# Route untuk daftar produk lama
@app.route("/products_old")
def products_old():
    list_products = Product.query.all()
    list_product_by_treatment = [product for product in list_products if product.id in [1, 2, 3, 4, 5]]
    return render_template("products_old.html", list_products=list_product_by_treatment)

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

# Route untuk history pemesanan user
@app.route('/user/history_booking', methods=['GET'])
@login_required
def history_pemesanan():
    bookings = Booking.query.filter_by(nama_client=current_user.username).order_by(Booking.tanggal.desc()).all()
    daily_data = defaultdict(int)
    monthly_data = defaultdict(int)
    for booking in bookings:
        date_obj = datetime.strptime(booking.tanggal, '%Y-%m-%d')
        day = date_obj.day
        month = date_obj.strftime('%B')
        daily_data[day] += 1
        monthly_data[month] += 1
    daily_chart_data = [daily_data[i] for i in range(1, 32)]
    monthly_chart_data = [monthly_data[month] for month in [
        "January", "February", "March", "April", "May", "June", 
        "July", "August", "September", "October", "November", "December"]]
    return render_template('admin/bookings.html', bookings=bookings, daily=daily_chart_data, monthly=monthly_chart_data)

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

# Route untuk menambah produk
@app.route('/admin/products', methods=['POST'])
@login_required
def tambah_product():
    product_name = request.form['nama']
    product_description = request.form['deskripsi']
    product_price = request.form['harga']
    product_image = request.files['gambar']
    product_key_highlight = request.form['key_highlight']
    product_kategori = request.form['kategori']
    product_keterangan = request.form['keterangan']
    product_diskon = request.form['diskon']
    
    if product_image:
        try:
            img = Image.open(product_image)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            random_name = uuid.uuid4().hex + ".jpg"
            destination = os.path.join(app.config['UPLOAD_FOLDER'], random_name)
            img.save(destination)
            file_url = "/static/upload/" + random_name
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    else:
        file_url = "/static/upload/treatment_5_icon.jpg"

    last_product = Product.query.order_by(Product.id.desc()).first()
    product_id = last_product.id + 1 if last_product else 1
    
    new_product = Product(
        id=product_id,
        nama=product_name,
        deskripsi=product_description,
        harga=product_price,
        gambar=file_url,
        key_highlight=product_key_highlight,
        kategori=product_kategori,
        keterangan=product_keterangan,
        diskon=product_diskon
    )
    db.session.add(new_product)
    db.session.commit()

    return redirect(url_for('edit_product'))

# Route untuk menampilkan daftar pemesanan
@app.route('/admin/bookings', methods=['GET'])
@login_required
def get_bookings():
    bookings = Booking.query.all()
    daily_data, monthly_data = defaultdict(int), defaultdict(int)
    
    for booking in bookings:
        date_obj = datetime.strptime(booking.tanggal, '%Y-%m-%d')
        day, month = date_obj.day, date_obj.strftime('%B')
        daily_data[day] += 1
        monthly_data[month] += 1
    
    daily_chart_data = [daily_data[i] for i in range(1, 32)]
    monthly_chart_data = [monthly_data[month] for month in [
        "January", "February", "March", "April", "May", "June", 
        "July", "August", "September", "October", "November", "December"]]
    
    sorted_bookings = sorted(bookings, key=lambda x: datetime.strptime(x.tanggal, '%Y-%m-%d'), reverse=True)
    
    return render_template('admin/bookings.html', bookings=sorted_bookings, daily=daily_chart_data, monthly=monthly_chart_data)
@app.route('/user/bookings', methods=['GET'])
@login_required
def user_get_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id)
    daily_data, monthly_data = defaultdict(int), defaultdict(int)
    
    for booking in bookings:
        date_obj = datetime.strptime(booking.tanggal, '%Y-%m-%d')
        day, month = date_obj.day, date_obj.strftime('%B')
        daily_data[day] += 1
        monthly_data[month] += 1
    
    daily_chart_data = [daily_data[i] for i in range(1, 32)]
    monthly_chart_data = [monthly_data[month] for month in [
        "January", "February", "March", "April", "May", "June", 
        "July", "August", "September", "October", "November", "December"]]
    
    sorted_bookings = sorted(bookings, key=lambda x: datetime.strptime(x.tanggal, '%Y-%m-%d'), reverse=True)
    
    return render_template('user/history_bookings.html', bookings=sorted_bookings, daily=daily_chart_data, monthly=monthly_chart_data)
@app.route('/user/deteksi', methods=['GET'])
@login_required
def user_get_deteksi():
    bookings = HistoryDeteksi.query.filter_by(username=current_user.username)
    daily_data, monthly_data = defaultdict(int), defaultdict(int)
    
    for booking in bookings:
        date_obj = datetime.strptime(booking.tanggal, '%Y-%m-%d')
        day, month = date_obj.day, date_obj.strftime('%B')
        daily_data[day] += 1
        monthly_data[month] += 1
    
    daily_chart_data = [daily_data[i] for i in range(1, 32)]
    monthly_chart_data = [monthly_data[month] for month in [
        "January", "February", "March", "April", "May", "June", 
        "July", "August", "September", "October", "November", "December"]]
    
    sorted_bookings = sorted(bookings, key=lambda x: datetime.strptime(x.tanggal, '%Y-%m-%d'), reverse=True)
    
    return render_template('user/history_deteksi.html', bookings=sorted_bookings, daily=daily_chart_data, monthly=monthly_chart_data)
# Route untuk mengedit produk
@app.route("/admin/edit_product")
@login_required
def edit_product():
    list_products = Product.query.all()
    all_product = [product for product in list_products if product.id not in [1, 2, 3, 4, 5]]
    return render_template("admin/product_edit.html", list_products=all_product)

# Route untuk detail edit produk
@app.route("/admin/edit_product_detail/<int:id>")
@login_required
def edit_product_detail(id):
    product = Product.query.get(id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return render_template("admin/product_detail_edit.html", product=product)

# Route untuk memperbarui produk
@app.route('/admin/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    updated_product = request.form.to_dict()
    file_url = "/static/upload/treatment_5_icon.jpg"
    
    if 'gambar' in request.files:
        image = request.files['gambar']
        if image:
            try:
                img = Image.open(image)
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                random_name = uuid.uuid4().hex + ".jpg"
                destination = os.path.join(app.config['UPLOAD_FOLDER'], random_name)
                img.save(destination)
                file_url = "/static/upload/" + random_name
            except Exception as e:
                return jsonify({"error": str(e)}), 400
    
    product.nama = updated_product.get('nama', product.nama)
    product.deskripsi = updated_product.get('deskripsi', product.deskripsi)
    product.harga = updated_product.get('harga', product.harga)
    product.gambar = file_url
    product.key_highlight = updated_product.get('key_highlight', product.key_highlight)
    product.kategori = updated_product.get('kategori', product.kategori)
    product.keterangan = updated_product.get('keterangan', product.keterangan)
    product.diskon = updated_product.get('diskon', product.diskon)

    db.session.commit()

    return jsonify({'message': 'Product updated successfully'})

@app.route("/rekomendasi_kering")
def get_rekomendasi_kering():
    rekomendasi = "Rekomendasi Treatment Kulit Kering:<br>"
    list_products = Product.query.all()
    rekomendasi += f"1. {list_products[19]['nama']} {list_products[19]['harga']}<br>"
    rekomendasi += f"2. {list_products[7]['nama']} {list_products[7]['harga']}<br> Paket <br>"
    rekomendasi += f"1. {list_products[10]['nama']} {list_products[10]['harga']}<br>"
    rekomendasi += f"2. {list_products[22]['nama']} {list_products[22]['harga']}<br><br>"
    return rekomendasi

@app.route("/rekomendasi_berminyak")
def get_rekomendasi_berminyak():
    rekomendasi = "Rekomendasi Treatment Kulit Berminyak:<br>"
    list_products = Product.query.all()
    rekomendasi += f"1. {list_products[17]['nama']} {list_products[17]['harga']}<br>"
    rekomendasi += f"2. {list_products[15]['nama']} {list_products[15]['harga']}<br> Paket <br>"
    rekomendasi += f"1. {list_products[11]['nama']} {list_products[11]['harga']}<br>"
    rekomendasi += f"2. {list_products[12]['nama']} {list_products[12]['harga']}<br><br>"
    return rekomendasi

@app.route("/rekomendasi_normal")
def get_rekomendasi_normal():
    rekomendasi = "Rekomendasi Treatment Kulit Normal:<br>"
    list_products = Product.query.all()
    rekomendasi += f"1. {list_products[14]['nama']} {list_products[14]['harga']}<br>"
    rekomendasi += f"2. {list_products[7]['nama']} {list_products[7]['harga']}<br>"
    rekomendasi += f"3. {list_products[15]['nama']} {list_products[15]['harga']}<br> Paket <br>"
    rekomendasi += f"1. {list_products[16]['nama']} {list_products[16]['harga']}<br>"
    rekomendasi += f"2. {list_products[20]['nama']} {list_products[20]['harga']}<br><br>"
    return rekomendasi

# Custom Error Handling
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Page not found"}), 404
import signal
import sys

def graceful_shutdown(signal, frame):
    print("Shutting down gracefully...")
    socketio.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)
import atexit

def cleanup():
    print("Cleaning up resources...")

atexit.register(cleanup)

#app.run(host="0.0.0.0",debug=True)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app,debug=True)