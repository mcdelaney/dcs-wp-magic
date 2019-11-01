FROM jfloff/alpine-python:3.7

WORKDIR /tmp/install/
COPY requirements.txt /tmp/install/
RUN pip install --no-cache-dir -r /tmp/install/requirements.txt && \
  rm -rf /tmp/install/*

RUN mkdir -p /var/dcs/ && \
  mkdir /var/dcs/log/ && \
  mkdir /var/dcs/data/

WORKDIR /var/dcs/
COPY dcs dcs
COPY run_tacview.py .

ENTRYPOINT ["python", "run_tacview.py"]
