
from process import preparation, generate_response
from flask import Flask, render_template, request

# download nltk
preparation()

#Start Chatbot
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/bot")
def chatbot():
    return render_template("chatbot.html")

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
    result= "halo anda memlih jenis kulit berminyak \n berikut jawaban pertanyaan anda :"+result
    return result
@app.route("/get/kering")
def get_bot_response_kering():
    jenis_kulit = "kering"
    print(jenis_kulit)
    user_input = str(request.args.get('msg'))
    print(user_input)
    result = generate_response(user_input)
    result = "halo anda memlih jenis kulit kering \n berikut jawaban pertanyaan anda :"+result
    return result

if __name__ == "__main__":
    app.run(debug=True)

