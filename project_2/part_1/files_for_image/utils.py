import os
import torch
import numpy as np
import torchvision.transforms as T
from facenet_pytorch import MTCNN
# from facenet_pytorch import InceptionResnetV1
from PIL import Image

class FaceDetection:
    def __init__(self):
        self.mtcnn          = MTCNN(image_size=240, margin=0, min_face_size=20) # initializing mtcnn for face detection

    def face_detection_func(self, input_image, test_image_path):
        # Step-1: Read the image
        img     = np.array(input_image)
        img     = Image.fromarray(img)

        key = os.path.splitext(os.path.basename(test_image_path))[0].split(".")[0]

        # Step:2 Face detection
        face, prob = self.mtcnn(img, return_prob=True, save_path=None)

        if face != None:

            face_img = face - face.min()  
            face_img = face_img / face_img.max()  
            face_img = (face_img * 255).byte().permute(1, 2, 0).numpy()  

            # Convert numpy array to PIL Image
            face_pil        = Image.fromarray(face_img, mode="RGB")

            # Save face image
            return face_pil

        else:
            print(f"No face is detected")
            return
        
class FaceRecognition:
    def __init__(self):
        self.model_path = "./resnetV1.pt"
        # self.model_wt_path = "./resnetV1_video_weights_1.pt"
        self.to_tensor = T.ToTensor()

        if os.path.exists(self.model_path):
            print(f"{self.model_path} exists!")
            print(f"Loading ResnetV1 trace from {self.model_path}.")
            self.resnet = torch.jit.load(self.model_path) # this uses the model trace. resnetV1.pt
        else:
            print(f"{self.model_path} does not exist!")
            print(f"Loading pretrained ResnetV1.")
            # self.resnet = InceptionResnetV1(pretrained='vggface2').eval()

    def image_to_tensor(self, face_pil_img):
        face_tensor = self.to_tensor(face_pil_img) 
        return face_tensor
    
    def save_model_trace(self, face_pil_img):
        face_tensor = self.image_to_tensor(face_pil_img)
        
        # Trace the model with an example input
        traced_model = torch.jit.trace(self.resnet, face_tensor.unsqueeze(0))

        # Save TorchScript model
        traced_model.save(self.model_path)

    def face_recognition_func(self, face_pil_img, model_wt_path):
        face_tensor = self.image_to_tensor(face_pil_img)

        if os.path.exists(model_wt_path):
            saved_data = torch.load(model_wt_path)  # loading resnetV1_video_weights.pt
        else:
            print(f"{model_wt_path} does not exist.")
            return None

        if face_tensor != None:
            emb             = self.resnet(face_tensor.unsqueeze(0)).detach()  # detech is to make required gradient false
            embedding_list  = saved_data[0]  # getting embedding data
            name_list       = saved_data[1]  # getting list of names
            dist_list       = []  # list of matched distances, minimum distance is used to identify the person

            for idx, emb_db in enumerate(embedding_list):
                dist = torch.dist(emb, emb_db).item()
                dist_list.append(dist)

            idx_min = dist_list.index(min(dist_list))
            return name_list[idx_min]
        else:
            print(f"No face is detected")
            return