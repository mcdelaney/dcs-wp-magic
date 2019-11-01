FROM jfloff/alpine-python:3.7

WORKDIR /tmp/install/
COPY requirements.txt /tmp/install/
RUN pip install --no-cache-dir -r /tmp/install/requirements.txt && \
  rm -rf /tmp/install/*
