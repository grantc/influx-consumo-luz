FROM python:3.9.7-slim-bullseye

COPY . /opt/i-de

RUN pip install -r /opt/i-de/requirements.txt

WORKDIR /opt/i-de

CMD python shelly.py