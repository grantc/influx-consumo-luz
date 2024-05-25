FROM python:3.9.7-slim-bullseye

COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

COPY . /opt/i-de

WORKDIR /opt/i-de

RUN useradd shelly

USER shelly

CMD python shelly.py