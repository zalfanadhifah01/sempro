
from models import db, User, Product, HistoryDeteksi, Booking
existing_product = Product.query.all()
print(existing_product)
