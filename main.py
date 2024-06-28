from process import preparation,generate_response
from flask import Flask,render_template,request,redirect,url_for,jsonify,session
from skin_detection import predict_skin
import os, json, uuid, time
from PIL import Image
from io import BytesIO
import exifread
# download nltk
preparation()

#Start Chatbot
app = Flask(__name__)
list_products = [
    {
        "id": 1,
        "nama": "HYDRAPEEL",
        "harga": "Rp 3.000.000,-",
        "gambar":"/static/image/1.heic",
        "rating":"52,912",
        "review":"4,01",
        "discount":"36",
        "limited_discount":["discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank",
                           "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time transaction, syarat dan ketentuan berlaku"],
        "key_highlight":["Menggunakan Teknologi Terkini",
                        "tanpa menggunakan bahan kimia terlarang",
                        "ruangan nyaman dan ber AC",
                        "Testimoni banyak",
                        "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"],
        "spesification":"",
    }, {
        "id": 2,
        "nama": "DNA Salmon",
        "harga": "Rp 3.000.000,-",
        "gambar":"/static/image/4.jpg",
        "rating":"52,912",
        "review":"4,01",
        "discount":"",
        "limited_discount":["discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank",
                           "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time transaction, syarat dan ketentuan berlaku"],
        "key_highlight":["Menggunakan Teknologi Terkini",
                        "tanpa menggunakan bahan kimia terlarang",
                        "ruangan nyaman dan ber AC",
                        "Testimoni banyak",
                        "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"],
        "spesification":"",
    }, {
        "id": 3,
        "nama": "Chemical Peeling",
        "harga": "Rp 3.000.000,-",
        "gambar":"/static/image/6.webp",
        "rating":"52,912",
        "review":"4,01",
        "discount":"50",
        "limited_discount":["discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank",
                           "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time transaction, syarat dan ketentuan berlaku"],
        "key_highlight":["Menggunakan Teknologi Terkini",
                        "tanpa menggunakan bahan kimia terlarang",
                        "ruangan nyaman dan ber AC",
                        "Testimoni banyak",
                        "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"],
        "spesification":"bla bla bla",
    }, {
        "id": 4,
        "nama": "MICRONEEDLING",
        "harga": "Rp 3.000.000,-",
        "gambar":"/static/image/microneedling_2.png",
        "rating":"52,912",
        "review":"4,01",
        "discount":"36",
        "limited_discount":["discount 5% dan Unlimited Cashback menggunakan kartu kredit Axis Bank",
                           "discount 10% menggunakan HDFC Bank Mastercard Credit card untuk first time transaction, syarat dan ketentuan berlaku"],
        "key_highlight":["Menggunakan Teknologi Terkini",
                        "tanpa menggunakan bahan kimia terlarang",
                        "ruangan nyaman dan ber AC",
                        "Testimoni banyak",
                        "bergaransi 1 tahun apabila timbul efek samping yang tidak terduga"],
        "spesification":"bisa lihat di belakang kemasan",
    }
]
project_directory = os.path.abspath(os.path.dirname(__file__))
upload_folder = os.path.join(project_directory, 'static', 'upload')
app.config['UPLOAD_FOLDER'] = upload_folder 
app.config['SECRET_KEY'] = 'bukan rahasia'
@app.route("/home")
def home_view(): 
    return render_template("index.html")
@app.route("/")
def home(): 
    return render_template("skin_detection.html")
    # return render_template("index.html")
@app.route("/bot")
def chatbot(): 
    return render_template("chatbot.html")
@app.route("/products")
def products(): 
    return render_template("products.html",list_products=list_products)
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
def skin_detection(): 
    return redirect(url_for('home'))
    # return render_template("skin_detection.html")
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
@app.route("/get/normal")
def get_bot_response_normal(): 
    jenis_kulit = "normal"
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
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        random_name = uuid.uuid4().hex + ".jpg"
        destination = os.path.join(app.config['UPLOAD_FOLDER'], random_name)
        img.save(destination)
        hasil = predict_skin(destination)
        print(hasil)
        if hasil == False:
            if session['jenis_kulit']: 
                session.pop('jenis_kulit')
            return jsonify({"msg":"Gagal, Tidak Terdeteksi Wajah"})
        session['jenis_kulit'] = hasil
        return jsonify({"msg":"SUKSES","hasil":hasil,"img":random_name})
    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)})
if __name__ == "__main__" : 
    app.run(debug = True)