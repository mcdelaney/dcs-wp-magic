package com.dcs;

import com.google.api.core.ApiFuture;
import com.google.api.core.ApiFutures;
import com.google.api.gax.rpc.ApiException;
import com.google.cloud.ServiceOptions;
import com.google.cloud.pubsub.v1.Publisher;
import com.google.cloud.pubsub.v1.TopicAdminClient;
import com.google.gson.Gson;
import com.google.protobuf.ByteString;
import com.google.pubsub.v1.ProjectTopicName;
import com.google.pubsub.v1.PubsubMessage;
import io.grpc.StatusRuntimeException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;


class PubSubWriter {

    // use the default project id
    private static final String PROJECT_ID = ServiceOptions.getDefaultProjectId();
    private Logger LOGGER = LoggerFactory.getLogger(PubSubWriter.class);
    private List<ApiFuture<String>> futures = new ArrayList<>();
    private Gson gson = new Gson();
    private Publisher publisher = null;
    private String ENV = !System.getenv("ENV").equals("prod") ? "stg" : "prod";

    PubSubWriter(String topic) {
        // Create a publisher instance with default settings bound to the topic
        if (ENV.equals("stg")) {
            topic = topic + "_stg";
        }
        ProjectTopicName topicName = ProjectTopicName.of(PROJECT_ID, topic);
        try {
            try (TopicAdminClient topicAdminClient = TopicAdminClient.create()) {
                topicAdminClient.createTopic(topicName);
                LOGGER.info("Topic {}:{} created", topicName.getProject(), topicName.getTopic());
            } catch (StatusRuntimeException | ApiException e) {
                LOGGER.error(e.toString());
            }

            publisher = Publisher.newBuilder(topicName).build();
        } catch (IOException e) {
            LOGGER.error("Error: " + e.toString());
        }
    }

    void toPubSub(DCSObject dcs_obj) {
        String message = gson.toJson(dcs_obj.toHashMap());
        // convert message to bytes
        ByteString data = ByteString.copyFromUtf8(message);
        PubsubMessage pubsubMessage = PubsubMessage.newBuilder()
                .setData(data)
                .build();
        ApiFuture<String> future = publisher.publish(pubsubMessage);
        futures.add(future);
    }

    void checkPublishedMessages() {
        try {
            List<String> messageIds = ApiFutures.allAsList(futures).get();
            LOGGER.info("Collecting message dispositions...");
            for (String messageId : messageIds) {
                LOGGER.debug("Message published successfully: " + messageId);
            }
        } catch (ExecutionException | InterruptedException e) {
            LOGGER.error("Error: " + e.toString());

        }

    }

    void shutDownPublisher() {
        if (publisher != null) {
            // When finished with the publisher, shutdown to free up resources.
            publisher.shutdown();
        }
    }
}