import json
import numpy as np
import random
import nltk
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import legacy
from sklearn.preprocessing import LabelEncoder

nltk.download('punkt')
nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()

# Load dataset
with open('model_chatbot/dataset.json') as file:
    data = json.load(file)

# Preprocessing
words = []
classes = []
documents = []
ignore_letters = ['?', '!', '.', ',']

for intent in data['intents']:
    for pattern in intent['patterns']:
        word_list = nltk.word_tokenize(pattern)
        words.extend(word_list)
        documents.append((word_list, intent['tag']))
        if intent['tag'] not in classes:
            classes.append(intent['tag'])

words = [lemmatizer.lemmatize(w.lower()) for w in words if w not in ignore_letters]
words = sorted(set(words))

classes = sorted(set(classes))

print(f'Words: {len(words)}')  # Tambahkan ini untuk melihat panjang words
print(f'Classes: {classes}')

training = []
output_empty = [0] * len(classes)

for document in documents:
    bag = []
    word_patterns = document[0]
    word_patterns = [lemmatizer.lemmatize(word.lower()) for word in word_patterns]
    for word in words:
        bag.append(1) if word in word_patterns else bag.append(0)
        
    output_row = list(output_empty)
    output_row[classes.index(document[1])] = 1
    training.append([bag, output_row])

random.shuffle(training)
training = np.array(training, dtype=object)

train_x = np.array(list(training[:, 0]))
train_y = np.array(list(training[:, 1]))

print(f'Train_x shape: {train_x.shape}')  # Tambahkan ini untuk melihat bentuk train_x
print(f'Train_y shape: {train_y.shape}')  # Tambahkan ini untuk melihat bentuk train_y

# Building the model
model = Sequential()
model.add(Dense(128, input_shape=(len(train_x[0]),), activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(len(train_y[0]), activation='softmax'))

sgd = legacy.SGD(learning_rate=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

# Training the model
hist = model.fit(x=train_x, y=train_y, epochs=200, batch_size=5, verbose=1)
model.save('model_chatbot/chat_model_new.h5', hist)
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Membagi dataset menjadi train dan test
train_x, test_x, train_y, test_y = train_test_split(train_x, train_y, test_size=0.2, random_state=42)

# Membangun dan melatih model seperti sebelumnya
model.fit(x=train_x, y=train_y, epochs=200, batch_size=5, verbose=1)

# Mengevaluasi model
loss, accuracy = model.evaluate(test_x, test_y, verbose=1)
print(f'Test Accuracy: {accuracy}')

# Memprediksi hasil dari test set dan mencetak classification report
predictions = model.predict(test_x)
predictions = np.argmax(predictions, axis=1)
true_classes = np.argmax(test_y, axis=1)

print(classification_report(true_classes, predictions, target_names=classes))

print("Model trained and saved as 'chat_model.h5'")
