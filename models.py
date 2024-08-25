from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

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
    product_id = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    nama_client = db.Column(db.String(100), nullable=False)
    alamat = db.Column(db.String(200), nullable=False)
    no_hp = db.Column(db.String(20), nullable=False)
    tanggal = db.Column(db.String(20), nullable=False)
    jam = db.Column(db.String(10), nullable=False)
