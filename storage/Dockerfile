FROM python:3.10-bullseye

COPY . /storage

WORKDIR /storage

RUN pip install fastapi uvicorn python-multipart

CMD ["python3", "storage.py"]