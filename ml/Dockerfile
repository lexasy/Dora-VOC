FROM python:3.10-bullseye

COPY . /ml

WORKDIR /ml

RUN apt-get update && apt-get install x264 libavcodec-extra ffmpeg libsm6 libxext6 -y

RUN pip install opencv-python bagpy pika ffmpeg-python

CMD ["python3", "-u", "doravoc_mlmodule.py"]