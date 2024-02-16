import json
import random
import nltk
import string
import numpy as np
import pickle
import tensorflow as tf
from nltk.stem import WordNetLemmatizer
from tensorflow import keras
from tensorflow.keras.preprocessing.sequence import pad_sequences

global responses, lemmatizer, tokenizer, le, model, input_shape
input_shape = 10

# import dataset answer
def load_response():
    global responses
    responses = {}
    
    with open('dataset_swakala/swakala_chatbot.json', encoding="utf8") as content:
        data = json.load(content)
    for intent in data['intents']:
        responses[intent['tag']]=intent['responses']    
    print(content)  
    
# import model dan download nltk file
def preparation():
    load_response()
    global lemmatizer, tokenizer, le, model
    tokenizer = pickle.load(open('model_chatbot/tokenizers.pkl', 'rb'))
    le = pickle.load(open('model_chatbot/le.pkl', 'rb'))
    model = keras.models.load_model('model_chatbot/chat_model.h5')
    lemmatizer = WordNetLemmatizer()
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

# def lemmatization(text):
#     word_list = nltk.word_tokenize(text)
#     print(word_list)
#     lemmatized_output = ' '.join([lemmatizer.lemmatize(w) for w in word_list])
#     print(lemmatized_output)
#     return lemmatized_output

# hapus tanda baca
def remove_punctuation(text):
    texts_p = []
    text = [letters.lower() for letters in text if letters not in string.punctuation]
    text = ''.join(text)
    texts_p.append(text)
    return texts_p

# mengubah text menjadi vector
def vectorization(texts_p):
    vector = tokenizer.texts_to_sequences(texts_p)
    vector = np.array(vector).reshape(-1)
    vector = pad_sequences([vector], input_shape)
    return vector

# klasifikasi pertanyaan user
def predict(vector):
    output = model.predict(vector)
    output = output.argmax()
    response_tag = le.inverse_transform([output])[0]
    print(response_tag)
    return response_tag

# menghasilkan jawaban berdasarkan pertanyaan user
def generate_response(text):
    texts_p = remove_punctuation(text)
    print(texts_p)
    vector = vectorization(texts_p)
    response_tag = predict(vector)
    test = vector[-1]
    
    print(test)
    if test[-1] == 0:
        return "Maaf, Saya Tidak Mengerti Apa Yang Anda Maksud"
    else:
        answer = random.choice(responses[response_tag])
        return answer
    
    