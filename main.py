from flask import Flask, render_template, request, redirect, url_for, jsonify,flash
import os
import uuid
import json
import random
import string
import pickle
from PIL import Image
import nltk
import numpy as np
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer
from keras.models import load_model
import torch
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights
from torch import nn
from facenet_pytorch import MTCNN
from copy import deepcopy
import shutil
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# Konfigurasi Aplikasi Flask
app = Flask(__name__)
project_directory = os.path.abspath(os.path.dirname(__file__))
upload_folder = os.path.join(project_directory, 'static', 'upload')
app.config['UPLOAD_FOLDER'] = upload_folder
app.config['SECRET_KEY'] = 'bukan rahasia'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Load users from JSON file
def load_users():
    with open('users.json', 'r') as file:
        return json.load(file)

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    users = load_users()
    user = next((u for u in users if u['id'] == int(user_id)), None)
    if user:
        return User(user['id'], user['username'], user['password'])
    return None

# Load products from JSON file
def load_products():
    with open('products.json', 'r') as file:
        return json.load(file)

# Save products to JSON file
def save_bookings(bookings):
    with open('bookings.json', 'w') as file:
        json.dump(bookings, file, indent=4)

# Load products from JSON file
def load_bookings():
    with open('bookings.json', 'r') as file:
        return json.load(file)

# Save products to JSON file
def save_products(products):
    with open('products.json', 'w') as file:
        json.dump(products, file, indent=4)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        if user:
            login_user(User(user['id'], user['username'], user['password']))
            return redirect(url_for('admin'))
        flash('Invalid credentials')
    return render_template('admin/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    products = load_products()
    return render_template('admin/index.html', products=products)
# Variabel Global untuk Chatbot
global responses, lemmatizer, tokenizer, le, model, input_shape
input_shape = 11

# Load response dataset
def load_response():
    global responses
    responses = {}
    with open('model_chatbot/dataset.json') as file:
        data = json.load(file)
    for intent in data['intents']:
        responses[intent['tag']] = intent['responses']

# Preparation function
def preparation():
    load_response()
    global lemmatizer, tokenizer, le, model
    with open('model_chatbot/tokenizers.pkl', 'rb') as f:
        tokenizer = pickle.load(f)
    le = pickle.load(open('model_chatbot/le.pkl', 'rb'))
    model = load_model('model_chatbot/chat_model.h5')
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
    if response_tag not in responses:
        return "Sorry, I didn't understand."
    answer = random.choice(responses[response_tag])
    return answer

# Persiapan Chatbot
preparation()

# Route Handlers
@app.route("/home")
def home_view():
    return render_template("index.html")

@app.route("/")
def home():
    return render_template("skin_detection.html")

@app.route("/bot")
def chatbot():
    return render_template("chatbot.html")

@app.route("/skin_detection")
def skin_detection():
    return redirect(url_for('home'))

@app.route("/get")
def get_bot_response():
    user_input = str(request.args.get('msg'))
    result = generate_response(user_input)
    return str(result)

@app.route("/rekomendasi_kering")
def get_rekomendasi_kering():
    rekomendasi = "Rekomendasi Treatment Kulit Kering:<br>"
    list_products = load_products()
    for product in list_products:
        if product['id'] == 19:
            rekomendasi += f"1. {product['nama']} {product['harga']}<br>"
        elif product['id'] == 7:
            rekomendasi += f"2. {product['nama']} {product['harga']}<br> Paket <br>"
        elif product['id'] == 10:
            rekomendasi += f"3. {product['nama']} {product['harga']}<br>"
        elif product['id'] == 22:
            rekomendasi += f"4. {product['nama']} {product['harga']}<br><br>"
    return rekomendasi

@app.route("/rekomendasi_berminyak")
def get_rekomendasi_berminyak():
    rekomendasi = "Rekomendasi Treatment Kulit Berminyak:<br>"
    list_products = load_products()
    for product in list_products:
        if product['id'] == 17:
            rekomendasi += f"1. {product['nama']} {product['harga']}<br>"
        elif product['id'] == 15:
            rekomendasi += f"2. {product['nama']} {product['harga']}<br> Paket <br>"
        elif product['id'] == 11:
            rekomendasi += f"3. {product['nama']} {product['harga']}<br>"
        elif product['id'] == 12:
            rekomendasi += f"4. {product['nama']} {product['harga']}<br><br>"
    return rekomendasi

@app.route("/rekomendasi_normal")
def get_rekomendasi_normal():
    rekomendasi = "Rekomendasi Treatment Kulit Normal:<br>"
    list_products = load_products()
    for product in list_products:
        if product['id'] == 14:
            rekomendasi += f"1. {product['nama']} {product['harga']}<br>"
        elif product['id'] == 7:
            rekomendasi += f"1. {product['nama']} {product['harga']}<br>"
        elif product['id'] == 15:
            rekomendasi += f"2. {product['nama']} {product['harga']}<br> Paket <br>"
        elif product['id'] == 16:
            rekomendasi += f"3. {product['nama']} {product['harga']}<br>"
        elif product['id'] == 20:
            rekomendasi += f"4. {product['nama']} {product['harga']}<br><br>"
    return rekomendasi
@app.route("/skin_detection")
def skin_detect():
    return render_template("skin_detection.html")

# Fungsi Prediksi Kulit
mtcnn = MTCNN(keep_all=False, device='cuda' if torch.cuda.is_available() else 'cpu')
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
checkpoint = torch.load('./model_detection/best_model_checkpoint.pth', map_location=torch.device('cpu'))
model_skin.load_state_dict(checkpoint['model_state_dict'])
optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
scheduler.load_state_dict(checkpoint['scheduler_state_dict'])

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
        if hasil == False:
            return jsonify({"msg": "Gagal, Tidak Terdeteksi Wajah"})
        return jsonify({"msg": "SUKSES", "hasil": hasil, "img": random_name})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/products_old")
def products_old():
    list_products = load_products()
    list_product_by_treatment = []
    for product in list_products:
        if product['id'] in [1, 2, 3, 4, 5]:
            list_product_by_treatment.append(product)
    return render_template("products_old.html", list_products=list_product_by_treatment)

@app.route("/products")
def products():
    list_products = load_products()
    all_product = []
    for product in list_products:
        if product['id'] in [1, 2, 3, 4, 5]:
            None
        else:
            all_product.append(product)
    return render_template("products.html", list_products=all_product)
@app.route("/products_detail/<int:id>")
def products_detail(id):
    list_products = load_products()
    list_bookings = load_bookings()
    print(list_bookings)  # Debugging purposes
    
    bookings = [booking for booking in list_bookings if int(booking["product_id"]) == id]
    print(bookings)  # Debugging purposes
    
    product = next((product for product in list_products if product["id"] == id), None)
    
    if product:
        return render_template("product_detail.html", product=product, bookings=bookings)
    else:
        return jsonify({"error": "Product not found"}), 404

@app.route('/api/products', methods=['GET'])
def get_products():
    products = load_products()
    return jsonify(products)

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    products = load_products()
    product = next((prod for prod in products if prod['id'] == product_id), None)
    if product is None:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(product)

@app.route('/bookings', methods=['POST'])
def book():
    data = request.json
    bookings = load_bookings()
    # Check if the booking with the same product_id, date, and time already exists
    for booking in bookings:
        if (booking['product_id'] == data['product_id'] and 
            booking['tanggal'] == data['date'] and 
            booking['jam'] == data['time']):
            return jsonify({'message': 'The selected slot is already booked.'}), 409
    new_booking = {
        'id': len(bookings) + 1,
        'product_id': data['product_id'],
        'product_name': data['productName'],
        'nama_client': data['name'],
        'alamat': data['address'],
        'no_hp': data['phone'],
        'tanggal': data['date'],
        'jam': data['time']
    }
    bookings.append(new_booking)
    save_bookings(bookings)
    return jsonify({'message': 'Booking successful'}), 200

@app.route('/products', methods=['POST'])
@login_required
def add_product():
    new_product = request.json
    products = load_products()
    new_product['id'] = max(prod['id'] for prod in products) + 1
    products.append(new_product)
    save_products(products)
    return jsonify(new_product), 201

@app.route('/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    updated_product = request.json
    products = load_products()
    for i, product in enumerate(products):
        if product['id'] == product_id:
            products[i] = updated_product
            save_products(products)
            return jsonify(updated_product)
    return jsonify({'error': 'Product not found'}), 404

@app.route('/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    products = load_products()
    products = [prod for prod in products if prod['id'] != product_id]
    save_products(products)
    return jsonify({'message': 'Product deleted'}), 200

def backup_file():
    source = 'products.json'
    destination = '/backup_db'
    if not os.path.exists(destination):
        os.makedirs(destination)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_filename = f"products_backup_{timestamp}.json"
    backup_path = os.path.join(destination, backup_filename)
    shutil.copy2(source, backup_path)
    print(f"Backup created at {backup_path}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=backup_file, trigger="cron", hour=0, minute=0)
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True)
