FROM python:3.10-bullseye

COPY ./static ./static
COPY ./templates ./templates
COPY ./main.py .

WORKDIR /

RUN pip install fastapi requests typing python-multipart uvicorn pika Jinja2

CMD ["python3", "-u", "main.py"]