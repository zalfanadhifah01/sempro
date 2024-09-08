from flask import Flask, jsonify, request, session, render_template, send_from_directory, abort, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from functools import wraps
import os,uuid

app = Flask(__name__)

project_directory = os.path.abspath(os.path.dirname(__file__))
upload_folder = os.path.join(project_directory, 'static', 'upload')
detect_folder = os.path.join(project_directory, 'static', 'detect')
app.config['UPLOAD_FOLDER'] = upload_folder 
app.config['PROJECT_FOLDER'] = project_directory 
app.config['DETECT_FOLDER'] = detect_folder 
app.config['SQLALCHEMY_DATABASE_URI'] =  'sqlite:///database.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'bukan rahasia')
app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT', b'asayibiuuoyo192382qo')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Allow CORS
from flask_cors import CORS
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


import json
class User(db.Model):
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

if __name__ == '__main__':
    # Perform operations inside the app context
    with app.app_context():
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
                db.session.commit() 
                print(f"Product with id {product_data['id']} added successfully.")
        
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
                db.session.commit()  
                print(f"Booking with ID {record['id']} added successfully.")
        
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
                db.session.commit()  # Commit user data
                print(f"Record with id {record['id']} added successfully.")
        
        # Load user data from a JSON file
        with open('users.json', 'r') as file:
            user_data = json.load(file)

        # Insert or update each user record
        for record in user_data:
            existing_user = User.query.filter_by(username=record['username']).first()

            if existing_user:
                print(f"User with username {record['username']} already exists. Skipping insertion.")
            else:
                hashed_password = bcrypt.generate_password_hash(record['password']).decode('utf-8')
                new_user = User(
                    id=record['id'],
                    username=record['username'],
                    role=record['role'],
                    password=hashed_password
                )
                db.session.add(new_user)
                db.session.commit()  # Commit user data
                print(f"User with username {record['username']} added successfully.")
        data = Product.query.all()
        print(data)
        data = User.query.all()
        print(data)
        data = HistoryDeteksi.query.all()
        print(data)
        data = Booking.query.all()
        print(data)        
        print("Database update complete.")
    app.run(host="0.0.0.0", debug=True, port=4040)
