import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
from copy import deepcopy
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
import torch
import torch.nn as nn
from PIL import Image
from facenet_pytorch import MTCNN
# Initialize MTCNN
mtcnn = MTCNN(keep_all=False, device='cuda' if torch.cuda.is_available() else 'cpu')
label_index = {"dry": 0, "normal": 1, "oily": 2}
index_label = {0: "kering", 1: "normal", 2: "berminyak"}
LR = 0.1
STEP = 15
GAMMA = 0.1
OUT_CLASSES = 3
IMG_SIZE = 224
resnet = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
num_ftrs = resnet.fc.in_features
resnet.fc = nn.Linear(num_ftrs, OUT_CLASSES)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(device)
model = deepcopy(resnet)
model = model.to(device)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.SGD(model.parameters(), lr=LR)
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=STEP, gamma=GAMMA)
# Load the checkpoint
checkpoint = torch.load('./model_detection/best_model_checkpoint.pth', map_location=torch.device('cpu'))
# Load the model state
model.load_state_dict(checkpoint['model_state_dict'])
# Load the optimizer state
optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
# Load the scheduler state
scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
# Load additional information
best_acc = checkpoint['best_acc']
train_loss = checkpoint['train_loss']
train_acc = checkpoint['train_acc']
val_loss = checkpoint['val_loss']
val_acc = checkpoint['val_acc']
print(f"Model and training history loaded successfully")
print(f"Best validation accuracy: {best_acc}")
transform = transforms.Compose([transforms.ToPILImage(),
                               transforms.ToTensor(),
                               transforms.Resize((IMG_SIZE, IMG_SIZE)),
                               transforms.Normalize(mean=[0.485, 0.456, 0.406],
                     std=[0.229, 0.224, 0.225])])
def predict_skin(x):
    img = Image.open(x).convert("RGB")
    # Detect face
    boxes, _ = mtcnn.detect(img)
    if boxes is not None:
        box = boxes[0]
        img = img.crop(box)
        # detect skin
        img = transform(np.array(img))
        img = img.view(1, 3, 224, 224)
        model.eval()
        with torch.no_grad():
            if torch.cuda.is_available():
                img = img.cuda()
            
            out = model(img)
            index = out.argmax(1).item()
            hasil = index_label[index]
            print(hasil)
            return hasil
    else:
        return False