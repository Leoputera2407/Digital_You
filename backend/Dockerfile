FROM python:3.11-slim-bullseye

RUN apt-get update \
    && apt-get install -y git cmake pkg-config libprotobuf-c-dev protobuf-compiler \ 
       libprotobuf-dev libgoogle-perftools-dev libpq-dev build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt

WORKDIR /app
COPY ./digital_twin /app/digital_twin


ENV PYTHONPATH /app
CMD ["/bin/sh", "-c", "uvicorn digital_twin.main:app --host 0.0.0.0 --port 8080"]