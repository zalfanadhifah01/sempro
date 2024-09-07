import json,hashlib
from models import db, User, Product, HistoryDeteksi, Booking
from flask import Flask
app = Flask(__name__)
# Perform operations inside the app context
with app.app_context():
    # Load products from the products.json file
    with open('products.json', 'r') as file:
        products_data = json.load(file)

    # Filter products with id between 6 and 26
    filtered_products = [p for p in products_data if 6 <= p['id'] <= 26]

    # Insert each filtered product into the database
    for product_data in filtered_products:
        # Check if the product with the given ID already exists in the database
        existing_product = Product.query.filter_by(id=product_data['id']).first()

        if existing_product:
            print(f"Product with id {product_data['id']} already exists. Skipping insertion.")
        else:
            # Create a new product instance and add it to the database
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

    # Load bookings data from a JSON file
    with open('bookings.json', 'r') as file:
        booking_data = json.load(file)

    # Insert or update each booking record
    for record in booking_data:
        # Check if the record with the given ID already exists in the database
        existing_booking = Booking.query.filter_by(id=record['id']).first()

        if existing_booking:
            print(f"Booking with ID {record['id']} already exists. Skipping insertion.")
        else:
            # Create a new booking instance and add it to the database
            new_booking = Booking(
                id=record['id'],
                user_id=record['user_id'],
                product_id=record['product_id'],
                booking_date=record['booking_date'],
                status=record['status']
            )
            db.session.add(new_booking)
            print(f"Booking with ID {record['id']} added successfully.")

    # Load history deteksi data from a JSON file
    with open('history_deteksi.json', 'r') as file:
        history_deteksi_data = json.load(file)

    # Insert or update each history deteksi record
    for record in history_deteksi_data:
        # Check if the record with the given ID already exists in the database
        existing_record = HistoryDeteksi.query.filter_by(id=record['id']).first()

        if existing_record:
            print(f"Record with id {record['id']} already exists. Skipping insertion.")
        else:
            # Create a new history deteksi instance and add it to the database
            new_record = HistoryDeteksi(
                id=record['id'],
                username=record['username'],
                tanggal=record['tanggal'],
                image_url=record['image_url'],
                terdeteksi_kulit=record['terdeteksi_kulit']
            )
            db.session.add(new_record)
            print(f"Record with id {record['id']} added successfully.")

    # Load user data from a JSON file
    with open('users.json', 'r') as file:
        user_data = json.load(file)

    # Insert or update each user record
    for record in user_data:
        # Check if the record with the given username already exists in the database
        existing_user = User.query.filter_by(username=record['username']).first()

        if existing_user:
            print(f"User with username {record['username']} already exists. Skipping insertion.")
        else:
            # Membuat objek hash dengan SHA-256
            hash_object = hashlib.sha256(record['password'].encode())

            # Mendapatkan hasil hash dalam format hexadecimal
            hashed_password = hash_object.hexdigest()
             # Create a new user instance and add it to the database
            new_user = User(
                id=record['id'],
                username=record['username'],
                role=record['role'],
                password=hashed_password
            )
            db.session.add(new_user)
            print(f"User with username {record['username']} added successfully.")


# Commit the changes to the database
db.session.commit()

print("Database update complete.")
