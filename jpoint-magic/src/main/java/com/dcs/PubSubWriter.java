package com.dcs;

import com.google.api.core.ApiFuture;
import com.google.api.core.ApiFutures;
import com.google.api.core.ApiFutureCallback;
import com.google.api.gax.rpc.ApiException;
import com.google.api.gax.core.ExecutorProvider;
import com.google.cloud.ServiceOptions;
import com.google.cloud.pubsub.v1.Publisher;
import com.google.cloud.pubsub.v1.TopicAdminClient;
import com.google.gson.*;
import com.google.gson.GsonBuilder;
import com.google.protobuf.ByteString;
import com.google.pubsub.v1.ProjectTopicName;
import com.google.pubsub.v1.PubsubMessage;
import io.grpc.StatusRuntimeException;
import org.slf4j.Logger;
import java.util.concurrent.Executors;
import com.google.common.util.concurrent.MoreExecutors;;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.lang.reflect.Type;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;

//
//
//class InstantSerializer implements JsonSerializer<Instant> {
//    public JsonElement serialize(Instant src, Type typeOfSrc, JsonSerializationContext context) {
//        return new JsonPrimitive(src.toString());
//    }
//}
//
//
//class PubSubWriter {
//    // use the default project id
//    int total_pubs = 0;
//    private String PROJECT_ID = ServiceOptions.getDefaultProjectId();
//    private Logger LOGGER = LoggerFactory.getLogger(PubSubWriter.class);
//    private List<ApiFuture<String>> futures = new ArrayList<>();
//    private Gson gson = new GsonBuilder().registerTypeAdapter(Instant.class, new InstantSerializer()).create();
//    private ProjectTopicName topicName;
//    private Publisher publisher;
//    private String ENV = !System.getenv("ENV").equals("prod") ? "stg" : "prod";
//
//    void setTopic(String topic) {
//        // Create a publisher instance with default settings bound to the topic
//        if (ENV.equals("stg")) {
//            topic = topic + "_stg";
//        }
//        this.topicName = ProjectTopicName.of(PROJECT_ID, topic);
//
//        try (TopicAdminClient topicAdminClient = TopicAdminClient.create()) {
//            topicAdminClient.createTopic(this.topicName);
//            LOGGER.info("Topic {}:{} created", this.topicName.getProject(), this.topicName.getTopic());
//        } catch (IOException | StatusRuntimeException | ApiException e) {
//            LOGGER.error(e.toString());
//        }
////        return this;
//    }
//
//    void createPublisher() {
//        // Create a publisher instance with default settings bound to the topic
//        try {
//            this.publisher = Publisher.newBuilder(this.topicName).build();
//        } catch (Exception e) {
//            LOGGER.error("Error: " + e.toString());
//        }
//    }
//
////    public Publisher getSingleThreadedPublisher(ProjectTopicName topicName) throws Exception {
////        // [START pubsub_publisher_concurrency_control]
////        // create a publisher with a single threaded executor
////        ExecutorProvider executorProvider =
////                InstantiatingExecutorProvider.newBuilder().setExecutorThreadCount(1).build();
////        Publisher publisher =
////                Publisher.newBuilder(topicName).setExecutorProvider(executorProvider).build();
////        // [END pubsub_publisher_concurrency_control]
////        return publisher;
////    }
//
//    void toPubSub(DCSObject dcs_obj) {
//        String message = this.gson.toJson(dcs_obj.toHashMap());
//        this.writeString(message);
//        this.publisher.publishAllOutstanding();
//
////        this.checkPublishedMessages();
//    }
//
//    void checkPublishedMessages() {
//        try {
//            publisher.publishAllOutstanding();
//            LOGGER.info("Total publications attempted: {}", total_pubs);
//            LOGGER.info("Collecting dispositions for {} messages...", futures.size());
//            List<String> messageIds = ApiFutures.allAsList(this.futures).get();
//            for (String messageId : messageIds) {
//                LOGGER.debug("Message published successfully: " + messageId);
//            }
//        } catch (ExecutionException | InterruptedException e) {
//            LOGGER.error("Error: " + e.toString());
//        }
//    }
//
//    void shutDownPublisher() {
//        LOGGER.info("Shutting down publisher...");
//        if (this.publisher != null) {
//            // When finished with the publisher, shutdown to free up resources.
//            try{
//                this.publisher.shutdown();
//                this.publisher.awaitTermination(10, TimeUnit.SECONDS);
//            }catch (InterruptedException e){
//                LOGGER.error("Error shutting down!");
//            }
//        }
//        LOGGER.info("Shutdown complete...");
//    }
//
//    void toPubSub(DCSRef dcs_obj) {
//        String message = this.gson.toJson(dcs_obj.toHashMap());
//        this.writeString(message);
//        // convert message to bytes
//    }
//
//    void writeString(String message){
//        ByteString data = ByteString.copyFromUtf8(message);
//        PubsubMessage pubsubMessage = PubsubMessage.newBuilder()
//                .setData(data)
//                .build();
//        ApiFuture<String> messageIdFuture = publisher.publish(pubsubMessage);
//        ApiFutures.addCallback(
//                messageIdFuture,
//                new ApiFutureCallback<>() {
//                    public void onSuccess(String messageId) {
//                        total_pubs ++;
//                        LOGGER.info("Published with message id: {} number {}", messageId, total_pubs);
//                    }
//
//                    public void onFailure(Throwable t) {
//                        LOGGER.error("Failed to publish: {}", t.toString());
//                    }
//                },
//                MoreExecutors.directExecutor());
//        this.futures.add(messageIdFuture);
////        this.total_pubs++;
//    }
//}
