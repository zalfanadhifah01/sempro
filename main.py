from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, Response,abort,send_from_directory,render_template_string
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from models import db, User, Product, HistoryDeteksi, Booking,Recommendation
import os, uuid, json, random, string, pickle,nltk, eventlet,io,base64,sys,gc,cv2,torch,logging,re, numpy as np
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from keras.models import load_model
from copy import deepcopy
from datetime import datetime
from collections import defaultdict
from PIL import Image
import tensorflow as tf
from torchvision import transforms
from torch import nn
from torchvision.models import resnet50, ResNet50_Weights
from flask_socketio import SocketIO, emit
from flask_bcrypt import Bcrypt
from functools import wraps
from flask_cors import CORS
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from datetime import timedelta, datetime,timezone
from itsdangerous import BadSignature, SignatureExpired
logging.basicConfig(level=logging.DEBUG)
logging.debug("Ini log dari debug")
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
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'qwdu92y17dqsu81')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME', 'znadhifah172@gmail.com'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD', 'xejgsdhtejxawdgj')
)

mail = Mail(app)
s = URLSafeTimedSerializer(app.config['JWT_SECRET_KEY'])
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

# Create tables
def create_tables():
    with app.app_context():
        db.create_all()

class LoginUser(UserMixin):
    def __init__(self, id, username, email,password, role):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.role = role

    def get_role(self):
        return self.role

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user:
        return LoginUser(user.id, user.username,user.email, user.password, user.role)    
# ==========================================================
# Chatbot Functionality
# ==========================================================
# Fungsi prediksi chatbot

# Variabel Global untuk Chatbot
global responses, lemmatizer, tokenizer, le, model

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
    file_path = os.path.join(project_directory, 'model_chatbot','tokenizer.pickle')
    with open(file_path, 'rb') as f:
        tokenizer = pickle.load(f)  # 'tokenizer' here is actually 'words'
    le_path = os.path.join(project_directory,'model_chatbot','label_encoder.pickle')
    le = pickle.load(open(le_path, 'rb'))
    model_path = os.path.join(project_directory,'model_chatbot','best_model.h5')
    model = load_model(model_path)
    lemmatizer = WordNetLemmatizer()
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)

# Function to remove punctuation and lemmatize
def clean_text(text):
    text = ''.join([char.lower() for char in text if char not in string.punctuation])
    text = [lemmatizer.lemmatize(word) for word in text.split()]
    return text

# Function to convert text to vector
def vectorization(text):
    text = clean_text(text)
    vector = [1 if word in text else 0 for word in tokenizer]  # 'tokenizer' is 'words'
    vector = np.array(vector).reshape(-1)
    vector = pad_sequences([vector], maxlen=len(tokenizer))  # Use 'maxlen' as the same length used in training
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
        session["jenis_kulit"] = "normal"
    elif response_tag == "jenis kulit saya berminyak":
        session["jenis_kulit"] = "berminyak"
    elif response_tag == "jenis kulit saya kering":
        session["jenis_kulit"] = "kering"
        
    if response_tag not in responses:
        return "Sorry, I didn't understand."
    
    answer = random.choice(responses[response_tag])
    return answer

# Persiapan Chatbot
preparation()
# Function to test chatbot on all classes (intents) in dataset
def test_all_classes():
    file_path = os.path.join(project_directory, 'model_chatbot','dataset.json')
    with open(file_path,encoding='utf-8') as file:
        data = json.load(file)
    for intent in responses.keys():
        print(f"Testing intent: {intent}")
        for pattern in data['intents']:
            if pattern['tag'] == intent:
                for example in pattern['patterns']:
                    print(f"Input: {example}")
                    response = generate_response(example)
                    print(f"Response: {response}")
                    print("-" * 40)

# Memanggil fungsi test_all_classes()
test_all_classes()


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
def handle_image(data):
    # Decode base64 image data
    image_data = data.get('image')  # Ambil data gambar (base64 format)
    sbuf = io.BytesIO(base64.b64decode(image_data))
    frame = np.array(Image.open(sbuf))
    stop_status = data.get('stop',False)
    random_name = ""
    if stop_status:
        random_name = uuid.uuid4().hex + ".jpg"
        destination = os.path.join(app.config['UPLOAD_FOLDER'], random_name)
        img = Image.open(sbuf)
        img.save(destination)
        print("Camera stopped. Processing last frame.")
    
    # Predict skin type from the frame
    result = predict_skin(frame)
    # Bebaskan RAM setelah prediksi
    del frame
    gc.collect()
    # Send the prediction result back to the client
    penjelasan_singkat = get_penjelasan_singkat(result)
    logging.debug(penjelasan_singkat)
    #rekomenadasi
    rekomendasi = get_rekomendasi(result)
    logging.debug(rekomendasi)
    emit('prediction', {'skin_type': result,"hasil": result, "img": random_name, "penjelasan_singkat":penjelasan_singkat,"rekomendasi":rekomendasi})

label_index = {"dry": 0, "normal": 1, "oily": 2, "kombinasi": 3, "sensitive": 4}
index_label = {0: "kering", 1: "normal", 2: "berminyak", 3: "kombinasi", 4: "sensitive"}
LR = 0.1
STEP = 15
GAMMA = 0.1
OUT_CLASSES = 5
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
        else:
            return None
    return None
@app.route("/penjelasan_singkat/<skin_type>")
def get_penjelasan_singkat(skin_type):
    if  skin_type == "normal":
     return "Kulit Normal adalah Kulit yang seimbang, tidak terlalu berminyak atau kering. Pori-pori kecil, tekstur halus, dan jarang mengalami masalah kulit."
    if  skin_type == "kering":
     return "Kulit Kering adalah Kulit yang kekurangan kelembapan, sering terasa kasar, kencang, atau bersisik. Cenderung lebih rentan terhadap kerutan."
    if  skin_type == "berminyak":
     return  "Kulit Berminyak adalah Produksi minyak berlebih, biasanya mengakibatkan wajah terlihat mengkilap. Rentan terhadap jerawat dan pori-pori besar."
    if  skin_type == "kombinasi":
     return "Kulit Kombinasi adalah Perpaduan kulit kering dan berminyak. Biasanya berminyak di area T-zone (dahi, hidung, dagu) dan kering di area lain."
    if  skin_type == "sensitive":
        return "Kulit Sensitif adalah Kulit yang mudah bereaksi terhadap produk atau lingkungan. Sering mengalami kemerahan, gatal, atau iritasi."

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
        logging.debug("1")
        from routes.routes import cek
        hasil = cek(file.filename)
        # penjelasan singkat
        penjelasan_singkat = get_penjelasan_singkat(hasil)
        logging.debug(penjelasan_singkat)
        #rekomenadasi
        rekomendasi = get_rekomendasi(hasil)
        logging.debug(rekomendasi)
        if current_user.is_authenticated:
            new_history_deteksi = HistoryDeteksi(
                username=current_user.username,
                tanggal=datetime.now().strftime("%Y-%m-%d"),
                image_url=f"/static/upload/{random_name}",
                terdeteksi_kulit=hasil
            )
            db.session.add(new_history_deteksi)
            db.session.commit()
            logging.debug("2")
            return jsonify({"msg": "SUKSES_simpan", "hasil": hasil, "img": random_name,"penjelasan_singkat":penjelasan_singkat,"rekomendasi":rekomendasi})
        else:
            
            logging.debug("3")
            return jsonify({"msg": "SUKSES", "hasil": hasil, "img": random_name,"penjelasan_singkat":penjelasan_singkat,"rekomendasi":rekomendasi})

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
            return redirect(url_for("get_bookings"))
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
                    return redirect(url_for('get_bookings'))
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
            return redirect(url_for("get_bookings"))
        elif current_user.role == 'user':
            return redirect(url_for("user_get_bookings"))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Error Username sudah ada")
            return redirect(url_for('register'))
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("Error Email sudah ada")
            return redirect(url_for('register'))
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password, role='user')
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
        return redirect(url_for('login'))
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
        email = request.form['email']

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
        email = request.form["email"]

        if not email:
            return jsonify({"msg": "Email harus diisi"})
            
        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({"msg": "Email tidak ditemukan"})

        token = s.dumps(email, salt='reset-password')

        reset_password_url = url_for('reset_password', token=token, _external=True)
        email_body = render_template_string('''
            Hello {{ user["name"] }},
            
            Anda menerima email ini, karena kami menerima permintaan untuk mengatur ulang kata sandi akun Anda dengan username = {{ user["username"] }}.
            
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
        password = request.form['password']

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

from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired

class RecommendationForm(FlaskForm):
    product_id = IntegerField('Product ID', validators=[DataRequired()])
    priority = IntegerField('Urutan', validators=[DataRequired()])
    type = SelectField('Type', choices=[('normal', 'Kulit Normal'), 
                                        ('kering', 'Kulit Kering'),
                                        ('berminyak', 'Kulit Berminyak'),
                                        ('kombinasi', 'Kulit Kombinasi'),
                                        ('sensitive', 'Kulit Sensitif')],
                       validators=[DataRequired()])
    submit = SubmitField('Save')

@app.route("/admin/recommendations", methods=['GET', 'POST'])
def manage_recommendations():
    form = RecommendationForm()
    if form.validate_on_submit():
        product_id = form.product_id.data
        priority = form.priority.data
        type = form.type.data
        
        # Check if recommendation already exists
        recommendation = Recommendation.query.filter_by(product_id=product_id, type=type).first()
        if recommendation:
            recommendation.priority = priority
        else:
            recommendation = Recommendation(product_id=product_id, priority=priority, type=type)
            db.session.add(recommendation)
        
        db.session.commit()
        return redirect(url_for('manage_recommendations'))

    recommendations = Recommendation.query.order_by(Recommendation.type, Recommendation.priority).all()
    return render_template('admin/admin_recommendations.html', form=form, recommendations=recommendations)
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

@app.route("/rekomendasi/<skin_type>")
def get_rekomendasi(skin_type):
    try:
        rekomendasi = f"Rekomendasi Treatment Kulit {skin_type.capitalize()}:<br>"
        recommendations = Recommendation.query.filter_by(type=skin_type).order_by(Recommendation.priority).all()
        logging.debug(recommendations)
        if not recommendations:
            rekomendasi = ""
        else:
            for rec in recommendations:
                product = Product.query.get(rec.product_id)
                if product:
                    rekomendasi += f"{rec.priority}. {product.nama} {product.harga}<br>"
                else:
                    rekomendasi += f"{rec.priority}. Produk dengan ID {rec.product_id} tidak ditemukan.<br>"
        logging.debug(rekomendasi)
    except Exception as e:
        rekomendasi = ""
    return rekomendasi

import signal
import sys

def graceful_shutdown(signal, frame):
    logging.debug("Shutting down gracefully...")
    socketio.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)
import atexit

def cleanup():
    logging.debug("Cleaning up resources...")

atexit.register(cleanup)

#app.run(host="0.0.0.0",debug=True)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app,debug=True)