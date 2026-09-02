import os
import numpy as np
from PIL import Image

from facenet_pytorch import MTCNN

class FaceDetection:
    def __init__(self):
        self.mtcnn          = MTCNN(image_size=240, margin=0, min_face_size=20) # initializing mtcnn for face detection

    def face_detection_func(self, input_image, test_image_path):
        # Step-1: Read the image
        # img     = np.array(input_image)
        # img     = Image.fromarray(img)

        key = os.path.splitext(os.path.basename(test_image_path))[0].split(".")[0]

        # Step:2 Face detection
        face, prob = self.mtcnn(input_image, return_prob=True, save_path=None)

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
            return None