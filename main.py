from process import preparation,generate_response
from flask import Flask,render_template,request,redirect,url_for,jsonify
from skin_detection import predict_skin
import os, json, uuid, time
from PIL import Image
from io import BytesIO
# download nltk
preparation()

#Start Chatbot
app = Flask(__name__)
list_products = [
    {
        "id": 1,
        "nama": "Redmi Note 8",
        "harga": "$4000"
    }, {
        "id": 2,
        "nama": "Samsung Galaxy",
        "harga": "$5000"
    }, {
        "id": 3,
        "nama": "iPhone 11",
        "harga": "$15000"
    }, {
        "id": 4,
        "nama": "Mi Redmi 8",
        "harga": "$3000"
    }, {
        "id": 5,
        "nama": "Mi Redmi 9",
        "harga": "$4000"
    }, {
        "id": 6,
        "nama": "Redmi Note 8",
        "harga": "$4000"
    }, {
        "id": 7,
        "nama": "Samsung Galaxy",
        "harga": "$5000"
    }, {
        "id": 8,
        "nama": "iPhone 11",
        "harga": "$15000"
    }
]
project_directory = os.path.abspath(os.path.dirname(__file__))
upload_folder = os.path.join(project_directory, 'static', 'upload')
app.config['UPLOAD_FOLDER'] = upload_folder 
@app.route("/")
def home(): return render_template("index.html")
@app.route("/bot")
def chatbot(): return render_template("chatbot.html")
@app.route("/products")
def products(): return render_template("products.html",list_products=list_products)
@app.route("/products_detail/<int:id>")
def products_detail(id):
    product = next((product for product in list_products if product["id"] == id), None)
    if product:
        print(product)
        return render_template("product_detail.html",product = product)
    else:
        print("Product not found")
        return jsonify({"error": "Product not found"}), 404
@app.route("/skin_detection")
def skin_detection(): return render_template("skin_detection.html")
@app.route("/get")
def get_bot_response(): 
    user_input = str(request.args.get('msg'))
    print(user_input)
    result = generate_response(user_input)
    return result
@app.route("/get/berminyak")
def get_bot_response_berminyak(): 
    jenis_kulit = "berminyak"
    print(jenis_kulit)
    user_input = str(request.args.get('msg'))
    print(user_input)
    result = generate_response(user_input)
    result = str(result)
    return result
@app.route("/get/kering")
def get_bot_response_kering(): 
    jenis_kulit = "kering"
    print(jenis_kulit)
    user_input = str(request.args.get('msg'))
    print(user_input)
    result = generate_response(user_input)
    result = str(result)
    return result
@app.route("/skin_detection")
def skin_detect(): return render_template("skin_detection.html")
@app.route("/skin_detection_submit",methods=["POST"])
def skin_detection_submit(): 
    file = request.files['gambar']
    try:
        img = Image.open(file)
        random_name = uuid.uuid4().hex + ".jpg"
        destination = os.path.join(app.config['UPLOAD_FOLDER'], random_name)
        img.save(destination)
        hasil = predict_skin(destination)
        print(hasil)
        return jsonify({"msg":"SUKSES","hasil":hasil,"img":random_name})
    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)})
if __name__ == "__main__" : app.run(debug = True)