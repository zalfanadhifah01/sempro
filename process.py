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
from tensorflow.keras.preprocessing.text import Tokenizer

from keras.models import load_model
# Import statements

global responses, lemmatizer, tokenizer, le, model, input_shape
input_shape = 11

# Load response dataset
def load_response():
    global responses
    responses = {}
    with open('model_chatbot/dataset.json') as file:
        data = json.load(file)
    for intent in data['intents']:
        responses[intent['tag']] = intent['responses']    

# Preparation function
def preparation():
    load_response()
    global lemmatizer, tokenizer, le, model
    with open('model_chatbot/tokenizers.pkl', 'rb') as f:
        tokenizer = pickle.load(f)
    le = pickle.load(open('model_chatbot/le.pkl', 'rb'))
    model = load_model('model_chatbot/chat_model.h5')
    lemmatizer = WordNetLemmatizer()
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

# Function to remove punctuation
def remove_punctuation(text):
    return ''.join([char.lower() for char in text if char not in string.punctuation])

# Function to convert text to vector
def vectorization(text):
    text = remove_punctuation(text)
    vector = tokenizer.texts_to_sequences([text])
    vector = np.array(vector).reshape(-1)
    vector = pad_sequences([vector], maxlen=input_shape)
    return vector

# Function to predict response tag
def predict(vector):
    output = model.predict(vector)
    output = output.argmax()
    response_tag = le.inverse_transform([output])[0]
    return response_tag

# Function to generate response
def generate_response(text):
    vector = vectorization(text)
    response_tag = predict(vector)
    
    if response_tag not in responses:
        return "Sorry, I didn't understand."
    
    answer = random.choice(responses[response_tag])
    return answer
