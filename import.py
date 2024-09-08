import json
import hashlib
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with app
db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    role = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.String(10), nullable=True)
    review = db.Column(db.Text, nullable=True)
    harga = db.Column(db.String(50), nullable=False)
    deskripsi = db.Column(db.Text, nullable=False)
    key_highlight = db.Column(db.Text, nullable=False)
    kategori = db.Column(db.String(100), nullable=False)
    keterangan = db.Column(db.Text, nullable=True)
    gambar = db.Column(db.String(200), nullable=True)

class HistoryDeteksi(db.Model):
    __tablename__ = 'history_deteksi'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    tanggal = db.Column(db.String(20), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    terdeteksi_kulit = db.Column(db.String(50), nullable=False)

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)  # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Optional foreign key
    status = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    nama_client = db.Column(db.String(100), nullable=False)
    alamat = db.Column(db.String(200), nullable=False)
    no_hp = db.Column(db.String(20), nullable=False)
    tanggal = db.Column(db.String(20), nullable=False)
    jam = db.Column(db.String(10), nullable=False)

# Perform operations inside the app context
with app.app_context():
    db.drop_all()  # Hapus semua tabel
    db.create_all()  # Buat ulang tabel
    
    # Load products from the products.json file
    with open('products.json', 'r') as file:
        products_data = json.load(file)

    # Filter products with id between 6 and 26
    filtered_products = [p for p in products_data if 6 <= p['id'] <= 26]

    # Insert each filtered product into the database
    for product_data in filtered_products:
        existing_product = Product.query.filter_by(id=product_data['id']).first()

        if existing_product:
            print(f"Product with id {product_data['id']} already exists. Skipping insertion.")
        else:
            new_product = Product(
                id=product_data['id'],
                nama=product_data['nama'],
                rating=product_data.get('rating', ""),
                review=product_data.get('review', ""),
                harga=product_data['harga'],
                deskripsi=product_data['deskripsi'],
                key_highlight=product_data.get('key_highlight', ""),
                kategori=product_data.get('kategori', ""),
                keterangan=product_data.get('keterangan', ""),
                gambar=product_data.get('gambar', "")
            )
            db.session.add(new_product)
            print(f"Product with id {product_data['id']} added successfully.")
    db.session.commit()  # Commit product data
    
    # Load bookings data from a JSON file
    with open('bookings.json', 'r') as file:
        booking_data = json.load(file)

    # Insert or update each booking record
    for record in booking_data:
        existing_booking = Booking.query.filter_by(id=record['id']).first()

        if existing_booking:
            print(f"Booking with ID {record['id']} already exists. Skipping insertion.")
        else:
            new_booking = Booking(
                id=record['id'],
                user_id=record.get('user_id'),  # Use get to avoid KeyError
                product_id=record['product_id'],
                tanggal=record['tanggal'],
                status=record['status'],
                product_name=record['product_name'],
                nama_client=record['nama_client'],
                alamat=record['alamat'],
                no_hp=record['no_hp'],
                jam=record['jam']
            )
            db.session.add(new_booking)
            print(f"Booking with ID {record['id']} added successfully.")
    db.session.commit()  # Commit booking data
    
    # Load history deteksi data from a JSON file
    with open('history_deteksi.json', 'r') as file:
        history_deteksi_data = json.load(file)

    # Insert or update each history deteksi record
    for record in history_deteksi_data:
        existing_record = HistoryDeteksi.query.filter_by(id=record['id']).first()

        if existing_record:
            print(f"Record with id {record['id']} already exists. Skipping insertion.")
        else:
            new_record = HistoryDeteksi(
                id=record['id'],
                username=record['username'],
                tanggal=record['tanggal'],
                image_url=record['image_url'],
                terdeteksi_kulit=record['terdeteksi_kulit']
            )
            db.session.add(new_record)
            print(f"Record with id {record['id']} added successfully.")
    db.session.commit()  # Commit history deteksi data
    
    # Load user data from a JSON file
    with open('users.json', 'r') as file:
        user_data = json.load(file)

    # Insert or update each user record
    for record in user_data:
        existing_user = User.query.filter_by(username=record['username']).first()

        if existing_user:
            print(f"User with username {record['username']} already exists. Skipping insertion.")
        else:
            # Hash the password with SHA-256
            hashed_password = hashlib.sha256(record['password'].encode()).hexdigest()
            new_user = User(
                id=record['id'],
                username=record['username'],
                role=record['role'],
                password=hashed_password
            )
            db.session.add(new_user)
            print(f"User with username {record['username']} added successfully.")
    db.session.commit()  # Commit user data
    existing_product = Product.query.all()
    print(existing_booking)


print("Database update complete.")
