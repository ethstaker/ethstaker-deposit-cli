# This image is from python:3.12-slim-bookworm
FROM python@sha256:45803c375b95ea33f482e53a461eca8f247617667d703660a06ccf5eb3d05326

WORKDIR /app

COPY requirements.txt ./

COPY ethstaker_deposit ./ethstaker_deposit

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3", "-m", "ethstaker_deposit" ]
