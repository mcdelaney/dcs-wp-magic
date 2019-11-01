#!/usr/bin/env bash

docker build -t tacview_reader:latest .
docker tag tacview_reader:latest gcr.io/dcs-analytics-257714/tacview_reader:latest

gcloud auth print-access-token | docker login -u oauth2accesstoken --password-stdin https://gcr.io
docker push gcr.io/dcs-analytics-257714/tacview_reader:latest
