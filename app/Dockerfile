FROM python:3.11.3-buster

LABEL author="Ali Hadipour <a.hadipour64@gmail.com>"

# os and opencv libraries
RUN apt-get update -y \
  && apt install libgl1-mesa-glx -y \
  && apt-get install 'ffmpeg' 'libsm6' 'libxext6'  -y \
  && python -m pip install --no-cache-dir --upgrade pip

# fixed python libraries for pytorch models
RUN pip install --no-cache-dir torch==2.0.1+cpu torchvision==0.15.2+cpu \
  -f https://download.pytorch.org/whl/torch_stable.html
RUN pip install --no-cache-dir numpy==1.25.0
RUN pip install --no-cache-dir opencv-python>=4.5.4.58
RUN pip install --no-cache-dir scikit-learn==1.3.0
RUN pip install --no-cache-dir matplotlib==3.4.3
RUN pip install --no-cache-dir pandas==1.3.4
RUN pip install --no-cache-dir pillow==9.5.0
RUN pip install --no-cache-dir seaborn==0.11.2
RUN pip install --no-cache-dir scipy==1.11.1
RUN pip install --no-cache-dir ultralytics==8.0.147
RUN pip install --no-cache-dir albumentations==1.1.0
RUN pip install --no-cache-dir fastapi==0.99.1
RUN pip install --no-cache-dir uvicorn[standard]==0.22.0
RUN rm -rf /root/.cache/pip


COPY . /app
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt
