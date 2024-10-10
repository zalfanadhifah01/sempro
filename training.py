import json
import numpy as np
import random
import nltk
import pickle
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import legacy
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.utils.multiclass import unique_labels

# Download NLTK data
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

# Lemmatization and cleaning
words = [lemmatizer.lemmatize(w.lower()) for w in words if w not in ignore_letters]
words = sorted(set(words))

# Initialize and fit LabelEncoder
label_encoder = LabelEncoder()
encoded_classes = label_encoder.fit_transform(classes)

print(f'Words: {len(words)}')
print(f'Classes: {classes}')

# Prepare training data
training = []
output_empty = [0] * len(classes)

for document in documents:
    bag = []
    word_patterns = document[0]
    word_patterns = [lemmatizer.lemmatize(word.lower()) for word in word_patterns]
    for word in words:
        bag.append(1) if word in word_patterns else bag.append(0)
        
    output_row = list(output_empty)
    output_row[encoded_classes[classes.index(document[1])]] = 1
    training.append([bag, output_row])

random.shuffle(training)
training = np.array(training, dtype=object)

train_x = np.array(list(training[:, 0]))
train_y = np.array(list(training[:, 1]))

print(f'Train_x shape: {train_x.shape}')
print(f'Train_y shape: {train_y.shape}')

# Split the data into training and testing sets
train_x, test_x, train_y, test_y = train_test_split(train_x, train_y, test_size=0.2, random_state=42)

# Building the model
model = Sequential()
model.add(Dense(128, input_shape=(len(train_x[0]),), activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(len(train_y[0]), activation='softmax'))

# Optimizer
sgd = legacy.SGD(learning_rate=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

# EarlyStopping and ModelCheckpoint with HDF5 format
early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
checkpoint = ModelCheckpoint('model_chatbot/best_model_coba.h5', monitor='val_loss', save_best_only=True, save_format='h5')

# Compute class weights
class_weights = compute_class_weight('balanced', classes=np.unique(np.argmax(train_y, axis=1)), y=np.argmax(train_y, axis=1))
class_weights = {i: class_weights[i] for i in range(len(class_weights))}

# Train the model
hist = model.fit(train_x, train_y, epochs=200, batch_size=5, validation_data=(test_x, test_y), class_weight=class_weights, verbose=1, callbacks=[early_stop, checkpoint])

# Evaluate the model
loss, accuracy = model.evaluate(test_x, test_y, verbose=1)
print(f'Test Accuracy: {accuracy}')

# Predict and print classification report
predictions = model.predict(test_x)
predictions = np.argmax(predictions, axis=1)
true_classes = np.argmax(test_y, axis=1)

# Avoid label mismatch issues in the classification report
labels_in_test = unique_labels(true_classes, predictions)
print(classification_report(true_classes, predictions, target_names=[classes[i] for i in labels_in_test], labels=labels_in_test, zero_division=1))

# Save the trained model in HDF5 format
model.save('model_chatbot/chat_model_coba.h5')

# Save the tokenizer (words) and label encoder
with open('model_chatbot/tokenizer_coba.pickle', 'wb') as handle:
    pickle.dump(words, handle, protocol=pickle.HIGHEST_PROTOCOL)

with open('model_chatbot/label_encoder_coba.pickle', 'wb') as handle:
    pickle.dump(label_encoder, handle, protocol=pickle.HIGHEST_PROTOCOL)

print("Model, tokenizer, and label encoder saved.")
