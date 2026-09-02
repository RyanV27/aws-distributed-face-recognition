# Use Amazon Linux Python 3.10 Lambda base image
FROM public.ecr.aws/lambda/python:3.10

# Set working directory
WORKDIR /var/task 

# Install system dependencies required by OpenCV and Torch
RUN yum -y install \
    cmake \
    ca-certificates \
    libglvnd-glx libGLU libX11 libXrender libXext libSM \
 && yum clean all

# Install PyTorch (CPU-only) and Torchvision
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install torch==2.2.2+cpu torchvision==0.17.2+cpu \
    -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Copy and install Python dependencies
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Pre-download facenet-pytorch MTCNN model
# RUN python3 -c "from facenet_pytorch import MTCNN; MTCNN()"

# Create Torch cache directory
RUN mkdir -p /tmp/.cache
ENV TORCH_HOME=/tmp/.cache/torch
ENV XDG_CACHE_HOME=/tmp/.cache/torch

# Copy model weights and handler scripts
COPY resnetV1_video_weights_1.pt /var/task
COPY resnetV1.pt /var/task
COPY utils.py /var/task
# COPY fd_lambda.py /var/task
COPY fr_lambda.py /var/task

# Default command points to your handler
CMD ["fr_lambda.face_recognition_handler"]
