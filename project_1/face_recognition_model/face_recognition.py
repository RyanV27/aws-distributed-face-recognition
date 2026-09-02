__copyright__   = "Copyright 2025, VISA Lab"
__license__     = "MIT"

import os
import csv
import sys
import torch
from PIL import Image
from torchvision import datasets
from torch.utils.data import DataLoader

from .facenet_pytorch import MTCNN, InceptionResnetV1

def face_match(img, data_path, mtcnn, resnet): # img_path= location of photo, data_path= location of data.pt
    # getting embedding matrix of the given img
    # img = Image.open(img_path)
    face, prob = mtcnn(img, return_prob=True) # returns cropped face and probability
    emb = resnet(face.unsqueeze(0)).detach() # detech is to make required gradient false

    saved_data = torch.load(data_path) # loading data.pt file
    embedding_list = saved_data[0] # getting embedding data
    name_list = saved_data[1] # getting list of names
    dist_list = [] # list of matched distances, minimum distance is used to identify the person

    for idx, emb_db in enumerate(embedding_list):
        dist = torch.dist(emb, emb_db).item()
        dist_list.append(dist)

    idx_min = dist_list.index(min(dist_list))
    return (name_list[idx_min], min(dist_list))

# test_image = sys.argv[1]
# result = face_match(test_image, 'data.pt')
# print(result[0])
