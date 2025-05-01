import os
import csv
import sys
import torch
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
from torchvision import datasets
from torch.utils.data import DataLoader

mtcnn = MTCNN(image_size=240, margin=0, min_face_size=20) 
resnet = InceptionResnetV1(pretrained='vggface2').eval()
test_image = sys.argv[1]

def face_match(img_path, data_path): 
    img = Image.open(img_path)
    face, prob = mtcnn(img, return_prob=True) 
    emb = resnet(face.unsqueeze(0)).detach()

    saved_data = torch.load('data.pt') 
    embedding_list = saved_data[0]
    name_list = saved_data[1]
    dist_list = []

    for idx, emb_db in enumerate(embedding_list):
        dist = torch.dist(emb, emb_db).item()
        dist_list.append(dist)

    idx_min = dist_list.index(min(dist_list))
    return (name_list[idx_min], min(dist_list))

result = face_match(test_image, 'data.pt')
print(result[0])
