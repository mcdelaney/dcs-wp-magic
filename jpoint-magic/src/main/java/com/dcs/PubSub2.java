package com.dcs;


import com.google.api.core.ApiFuture;
import com.google.api.core.ApiFutureCallback;
import com.google.api.core.ApiFutures;
import com.google.api.gax.rpc.ApiException;
import com.google.cloud.ServiceOptions;
import com.google.cloud.pubsub.v1.Publisher;
import com.google.cloud.pubsub.v1.TopicAdminClient;
import com.google.common.util.concurrent.MoreExecutors;
import com.google.gson.*;
import com.google.protobuf.ByteString;
import com.google.pubsub.v1.ProjectTopicName;
import com.google.api.gax.batching.BatchingSettings;
import com.google.pubsub.v1.PubsubMessage;
import io.grpc.StatusRuntimeException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.lang.reflect.Type;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
//import java.time.Duration;
import org.threeten.bp.Duration;




class InstantSerializer implements JsonSerializer<Instant> {
    public JsonElement serialize(Instant src, Type typeOfSrc, JsonSerializationContext context) {
        return new JsonPrimitive(src.toString());
    }
}


class PubSub2 {
    // use the default project id
    private String PROJECT_ID = ServiceOptions.getDefaultProjectId();
    private static Logger LOGGER = LoggerFactory.getLogger(PubSub2.class);
    private Gson gson = new GsonBuilder().registerTypeAdapter(Instant.class, new InstantSerializer()).create();

    private String ENV = !System.getenv("ENV").equals("prod") ? "stg" : "prod";
    ProjectTopicName topicName;
    Publisher publisher;


//    List<ApiFuture<String>> futures = new ArrayList<>();

    void ensureTopicExists(String topic){
        if (ENV.equals("stg")) {
            topic = topic + "_stg";
        }
        topicName = ProjectTopicName.of(PROJECT_ID, topic);
    }

    void createPublisher(){
        try
        {
            BatchingSettings DEFAULT_BATCHING_SETTINGS =
                    BatchingSettings.newBuilder()
                            .setDelayThreshold(Duration.ofSeconds(1))
                            .setElementCountThreshold(50L)
                            .build();

            publisher = Publisher.newBuilder(topicName)
                    .setBatchingSettings(DEFAULT_BATCHING_SETTINGS)
                    .build();

        } catch(IOException e){
            LOGGER.error("IO Exception!");
        }

    }

    void write(DCSObject record) {
        // Create a publisher instance with default settings bound to the topic
        try {

            List<ApiFuture<String>> futures = new ArrayList<>();
            String message = gson.toJson(record.toHashMap());

            ByteString data = ByteString.copyFromUtf8(message);
            PubsubMessage pubsubMessage = PubsubMessage.newBuilder()
                    .setData(data)
                    .build();

            ApiFuture<String> messageIdFuture = publisher.publish(pubsubMessage);
            String temp = messageIdFuture.get();
            publisher.publishAllOutstanding();
            if (!messageIdFuture.isDone()){
                LOGGER.error("Message not done!");
            }else{
                LOGGER.info("Message IS done!");

            }

//            LOGGER.info(messageIdFuture.get());
//            futures.add(messageIdFuture);
//
//            List<String> messageIds = ApiFutures.allAsList(futures).get();
//            List<String> found = new ArrayList<>();
//
//
//
//            for (String messageId : messageIds) {
//                LOGGER.info("Message published successfully: " + messageId);
//                found.add(messageId);
//            }
//
//            futures.removeAll(found);

        } catch (StatusRuntimeException | ApiException | ExecutionException | InterruptedException e) {
            LOGGER.error(e.toString());
        }
    }
    void shutdownPublisher(){
        publisher.shutdown();
    }
}
