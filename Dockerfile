# This image is from python:3.12-slim-bookworm
FROM python@sha256:a31cbb4db18c6f09e3300fa85b77f6d56702501fcb9bdb8792ec702a39ba6200

WORKDIR /app

COPY requirements.txt ./

COPY ethstaker_deposit ./ethstaker_deposit

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3", "-m", "ethstaker_deposit" ]
