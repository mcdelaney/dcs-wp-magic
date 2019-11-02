#!/bin/bash

gcloud dataflow jobs run pubsub_sessions \
    --gcs-location gs://dataflow-templates/latest/PubSub_to_BigQuery \
    --parameters \
inputTopic=projects/dcs-analytics-257714/topics/tacview_sessions,\
outputTableSpec=dcs-analytics-257714:tacview.sessions
