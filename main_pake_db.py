from flask import Flask, render_template, request, redirect, url_for, jsonify,flash,session
import os,uuid, json,random,string, pickle ,nltk,shutil,torch, gc
from PIL import Image
import numpy as np
from collections import defaultdict
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer
from keras.models import load_model
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights
from torch import nn
from facenet_pytorch import MTCNN
from copy import deepcopy
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from models import db, User, Product, HistoryDeteksi, Booking
import os

# Konfigurasi Aplikasi Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
project_directory = os.path.abspath(os.path.dirname(__file__))
upload_folder = os.path.join(project_directory, 'static', 'upload')
app.config['UPLOAD_FOLDER'] = upload_folder
app.config['SECRET_KEY'] = 'dmo42901i41;/.p`'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


db.init_app(app)

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
        return LoginUser(user.id, user.username, user.password,user.role)
    return None
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("history_pemesanan"))
        elif current_user.role == 'user':
            return redirect(url_for("get_bookings"))
    else:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username, password=password).first()
            if user:
                login_user(user)
                if user.role == "admin":
                    return redirect(url_for('history_pemesanan'))
                else:
                    return redirect(url_for('get_bookings'))
            flash('Invalid credentials')
        return render_template('admin/login.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("history_pemesanan"))
        elif current_user.role == 'user':
            return redirect(url_for("get_bookings"))
    else:
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
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Static Page Routes
@app.route('/')
def home():
    return render_template('skin_detection.html')

# Route Landing Page
@app.route("/home")
def home_view():
    return render_template("index.html")

# Chatbot Routes
@app.route("/bot")
def chatbot():
    return render_template("chatbot.html")

@app.route("/get")
def get_bot_response():
    user_input = str(request.args.get('msg'))
    result = generate_response(user_input)
    return str(result)

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
        hasil = predict_skin(destination)
        session["jenis_kulit"] = hasil
        if hasil == False:
            return jsonify({"msg": "Gagal, Tidak Terdeteksi Wajah"})
        # Bebaskan RAM setelah prediksi
        del img
        torch.cuda.empty_cache()
        gc.collect()
        if current_user.role == "user":
            new_history_deteksi = HistoryDeteksi(
                username=current_user.username,
                tanggal=datetime.now().strftime("%Y-%m-%d"),
                image_url=f"/static/upload/{random_name}",
                terdeteksi_kulit=hasil
            )
            db.session.add(new_history_deteksi)
            db.session.commit()
        return jsonify({"msg": "SUKSES", "hasil": hasil, "img": random_name})
    except Exception as e:
        return jsonify({"error": str(e)})

# Products Routes
@app.route("/products")
def products():
    products = Product.query.all()
    return render_template("products.html", list_products=products)

@app.route("/products_detail/<int:id>")
def products_detail(id):
    product = Product.query.get(id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    bookings = Booking.query.filter_by(product_id=id).all()
    return render_template("product_detail.html", product=product, bookings=bookings)

@app.route("/products_old")
def products_old():
    list_products = Product.query.all()
    list_product_by_treatment = []
    for product in list_products:
        if product['id'] in [1, 2, 3, 4, 5]:
            list_product_by_treatment.append(product)
    return render_template("products_old.html", list_products=list_product_by_treatment)

@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify(products)

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    products = Product.query.all()
    product = next((prod for prod in products if prod['id'] == product_id), None)
    if product is None:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(product)

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
    daily_chart_data = [daily_data[i] for i in range(1, 32)]  # Data harian untuk 1-31
    monthly_chart_data = [monthly_data[month] for month in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]]
    return render_template('admin/bookings.html', bookings=bookings, daily=daily_chart_data, monthly=monthly_chart_data)

@app.route('/bookings', methods=['POST'])
def book():
        data = request.json if request.is_json else request.form
        product_id = data.get('product_id')
        date = data.get('date', datetime.now().strftime("%Y-%m-%d"))
        time = data.get('time')

        # Filter untuk memeriksa apakah slot yang dipilih sudah dipesan
        existing_booking = Booking.query.filter_by(product_id=product_id, tanggal=date, jam=time).first()
        if existing_booking:
            if request.is_json:
                return jsonify({'message': 'The selected slot is already booked.'}), 409
            else:
                flash("Slot yang dipilih sudah dipesan.")
                return redirect(url_for('get_bookings'))

        # Proses pemesanan baru
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

@app.route('/admin/products', methods=['POST'])
@login_required
def tambah_product():
    products = Product.query.all()  # Muat produk dari file JSON
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
            file_url  = "/static/upload/"+random_name
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    else:
        file_url = "/static/upload/"+"treatment_5_icon.jpg"
    if products:
        last_id = max(product['id'] for product in products)
        product_id = last_id + 1
    else:
        product_id = 1  # Jika list kosong, mulai dari 1
    new_product = {
        'id': product_id,
        'nama': product_name,
        'deskripsi': product_description,
        'harga': product_price,
        'gambar': file_url,
        "rating": "4.5",
        "review": "100",
        "key_highlight": product_key_highlight,
        "kategori": product_kategori,
        "keterangan":product_keterangan,
    }
    products.append(new_product)
    save_products(products)
    return redirect(url_for('edit_product'))

@app.route('/admin/bookings', methods=['GET'])
@login_required
def get_bookings():
    bookings = Booking.query.all()
    sorted_bookings = sorted(bookings, key=lambda x: datetime.strptime(x['tanggal'], '%Y-%m-%d'), reverse=True)
    daily_data = defaultdict(int)
    monthly_data = defaultdict(int)
    for booking in bookings:
        date_obj = datetime.strptime(booking['tanggal'], '%Y-%m-%d')
        day = date_obj.day
        month = date_obj.strftime('%B')
        daily_data[day] += 1
        monthly_data[month] += 1
    daily_chart_data = [daily_data[i] for i in range(1, 32)]  # Data harian untuk 1-31
    monthly_chart_data = [monthly_data[month] for month in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]]
    return render_template('admin/bookings.html', bookings=sorted_bookings,daily= daily_chart_data, monthly= monthly_chart_data)

@app.route("/admin/edit_product")
@login_required
def edit_productt():
    list_products = Product.query.all()
    all_product = []
    for product in list_products:
        if product['id'] in [1, 2, 3, 4, 5]:
            None
        else:
            all_product.append(product)
    print(all_product)
    return render_template("admin/product_edit.html", list_products=all_product)

@app.route("/admin/edit_product_detail/<int:id>")
@login_required
def edit_product_detail(id):
    list_products = Product.query.all()
    product = next((product for product in list_products if product["id"] == id), None)
    if product:
        return render_template("admin/product_detail_edit.html", product=product)
    else:
        return jsonify({"error": "Product not found"}), 404

@app.route('/admin/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    products = Product.query.all()
    updated_product = request.form.to_dict()
    for i, product in enumerate(products):
        if product['id'] == product_id:
            updated_product["id"]=int(product_id)
            file = request.files.get('gambar')
            if file:
                try:
                    img = Image.open(file)
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                    random_name = uuid.uuid4().hex + ".jpg"
                    destination = os.path.join(app.config['UPLOAD_FOLDER'], random_name)
                    img.save(destination)
                    updated_product["gambar"] = "/static/upload/"+random_name
                except Exception as e:
                    return jsonify({"error": str(e)}), 400
            else:
                updated_product['gambar'] = product["gambar"]
            products[i] = updated_product
            save_products(products)
            return jsonify(updated_product)
    return jsonify({'error': 'Product not found'}), 404
    

@app.route('/admin/products/<int:product_id>', methods=['DELETE'])
@login_required
def hapus_product(product_id):
    products = Product.query.all()
    initial_count = len(products)
    products = [prod for prod in products if prod['id'] != product_id]
    save_products(products)
    final_count = len(products)
    if initial_count == final_count:
        app.logger.error(f"Produk dengan ID {product_id} tidak ditemukan.")
    else:
        app.logger.info(f"Produk dengan ID {product_id} berhasil dihapus.")
    return jsonify({'message': 'Product deleted'}), 200

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

# Fungsi Prediksi Kulit
label_index = {"dry": 0, "normal": 1, "oily": 2}
index_label = {0: "kering", 1: "normal", 2: "berminyak"}
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
model_location = os.path.join(project_directory,'model_detection','best_model_checkpoint.pth')
checkpoint = torch.load(model_location, map_location=torch.device('cpu'))
model_skin.load_state_dict(checkpoint['model_state_dict'])
optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
scheduler.load_state_dict(checkpoint['scheduler_state_dict'])

mtcnn = MTCNN(keep_all=False, device='cuda' if torch.cuda.is_available() else 'cpu')
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def predict_skin(image_path):
    img = Image.open(image_path).convert("RGB")
    boxes, _ = mtcnn.detect(img)
    if boxes is not None:
        box = boxes[0]
        img = img.crop(box)
        img = transform(img)  # Menggunakan transform untuk mengubah gambar menjadi tensor
        img = img.unsqueeze(0)  # Menambahkan dimensi batch
        model_skin.eval()
        with torch.no_grad():
            img = img.to(device)
            out = model_skin(img)
            index = out.argmax(1).item()
            hasil = index_label[index]
            return hasil
    else:
        return False

# Custom Error Handling
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Page not found"}), 404

# Bersihkan cache setiap 24 jam
def clear_cache():
    torch.cuda.empty_cache()
    gc.collect()

scheduler = BackgroundScheduler()
scheduler.add_job(func=clear_cache, trigger="interval", hours=24)
scheduler.start()

# CRUD for Users
@app.route('/users')
def list_users():
    users = User.query.all()
    return render_template('list_users.html', users=users)

@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        role = request.form['role']
        password = request.form['password']
        user = User(username=username, role=role, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('list_users'))
    return render_template('add_user.html')

@app.route('/users/edit/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.role = request.form['role']
        user.password = request.form['password']
        db.session.commit()
        return redirect(url_for('list_users'))
    return render_template('edit_user.html', user=user)

@app.route('/users/delete/<int:id>')
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('list_users'))

# CRUD for Products
@app.route('/products')
def list_products():
    products = Product.query.all()
    return render_template('list_products.html', products=products)

@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product = Product(
            nama=request.form['nama'],
            rating=request.form['rating'],
            review=request.form['review'],
            harga=request.form['harga'],
            deskripsi=request.form['deskripsi'],
            key_highlight=request.form['key_highlight'],
            kategori=request.form['kategori'],
            keterangan=request.form['keterangan'],
            gambar=request.form['gambar']
        )
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('list_products'))
    return render_template('add_product.html')

@app.route('/products/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.nama = request.form['nama']
        product.rating = request.form['rating']
        product.review = request.form['review']
        product.harga = request.form['harga']
        product.deskripsi = request.form['deskripsi']
        product.key_highlight = request.form['key_highlight']
        product.kategori = request.form['kategori']
        product.keterangan = request.form['keterangan']
        product.gambar = request.form['gambar']
        db.session.commit()
        return redirect(url_for('list_products'))
    return render_template('edit_product.html', product=product)

@app.route('/products/delete/<int:id>')
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('list_products'))

# CRUD for History Deteksi
@app.route('/history_deteksi')
def list_history_deteksi():
    histories = HistoryDeteksi.query.all()
    return render_template('list_history_deteksi.html', histories=histories)

@app.route('/history_deteksi/add', methods=['GET', 'POST'])
def add_history_deteksi():
    if request.method == 'POST':
        history = HistoryDeteksi(
            username=request.form['username'],
            tanggal=request.form['tanggal'],
            image_url=request.form['image_url'],
            terdeteksi_kulit=request.form['terdeteksi_kulit']
        )
        db.session.add(history)
        db.session.commit()
        return redirect(url_for('list_history_deteksi'))
    return render_template('add_history_deteksi.html')

@app.route('/history_deteksi/delete/<int:id>')
def delete_history_deteksi(id):
    history = HistoryDeteksi.query.get_or_404(id)
    db.session.delete(history)
    db.session.commit()
    return redirect(url_for('list_history_deteksi'))

# CRUD for Bookings
@app.route('/bookings')
def list_bookings():
    bookings = Booking.query.all()
    return render_template('list_bookings.html', bookings=bookings)

@app.route('/bookings/add', methods=['GET', 'POST'])
def add_booking():
    if request.method == 'POST':
        booking = Booking(
            product_id=request.form['product_id'],
            product_name=request.form['product_name'],
            nama_client=request.form['nama_client'],
            alamat=request.form['alamat'],
            no_hp=request.form['no_hp'],
            tanggal=request.form['tanggal'],
            jam=request.form['jam']
        )
        db.session.add(booking)
        db.session.commit()
        return redirect(url_for('list_bookings'))
    return render_template('add_booking.html')

@app.route('/bookings/delete/<int:id>')
def delete_booking(id):
    booking = Booking.query.get_or_404(id)
    db.session.delete(booking)
    db.session.commit()
    return redirect(url_for('list_bookings'))

if __name__ == '__main__':
    create_tables()
    app.run(host="0.0.0.0",debug=True)