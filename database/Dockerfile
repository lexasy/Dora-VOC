FROM python:3.10-bullseye

COPY . .
WORKDIR /

RUN apt-get update && apt-get upgrade -y
RUN pip install fastapi uvicorn

CMD ["python3", "-u", "main.py"]