from process import preparation,generate_response
from flask import Flask,render_template,request,redirect,url_for

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
@app.route("/")
def home(): return render_template("index.html")
@app.route("/bot")
def chatbot(): return render_template("chatbot.html")
@app.route("/products")
def products(): return render_template("products.html",list_products=list_products)
@app.route("/products_detail/<id>")
def products_detail(id):
    product_detail = {} 
    for i in list_products:
        if i["id"] == id :
            product_detail.append(i)
        else:
            return redirect(url_for('products'))
    return render_template("product_detail.html",product_detail = product_detail)
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

if __name__ == "__main__" : app.run(debug = True)