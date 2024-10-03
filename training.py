import numpy as np
import json
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

# Membaca dataset
with open('model_chatbot/dataset.json') as file:
    data = json.load(file)

# List untuk data
patterns = []
tags = []
responses = {}

# Parsing dataset
for intent in data['intents']:
    for pattern in intent['patterns']:
        patterns.append(pattern)
        tags.append(intent['tag'])
    
    # Simpan responses untuk tiap tag
    responses[intent['tag']] = intent['responses']

# Encode labels (tags)
label_encoder = LabelEncoder()
labels = label_encoder.fit_transform(tags)

# Tokenizing (mengubah teks menjadi numerik)
tokenizer = tf.keras.preprocessing.text.Tokenizer(num_words=1000, oov_token="<OOV>")
tokenizer.fit_on_texts(patterns)
sequences = tokenizer.texts_to_sequences(patterns)
padded_sequences = tf.keras.preprocessing.sequence.pad_sequences(sequences, padding='post')

# One-hot encoding labels
num_classes = len(set(tags))
labels_one_hot = tf.keras.utils.to_categorical(labels, num_classes=num_classes)

# Memisahkan data untuk training dan testing
X_train, X_test, y_train, y_test = train_test_split(padded_sequences, labels_one_hot, test_size=0.2, random_state=42)

# Membangun model
model = Sequential()
model.add(Dense(128, input_shape=(X_train.shape[1],), activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(num_classes, activation='softmax'))

# Compile model
model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

# Training model
epochs = 200
history = model.fit(X_train, y_train, epochs=epochs, batch_size=8, validation_data=(X_test, y_test))

# Simpan model dan tokenizer
model.save('model_chatbot/chatbot_model.h5')

with open('model_chatbot/tokenizer.pickle', 'wb') as handle:
    import pickle
    pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)

# Simpan label encoder
with open('model_chatbot/label_encoder.pickle', 'wb') as handle:
    pickle.dump(label_encoder, handle, protocol=pickle.HIGHEST_PROTOCOL)
