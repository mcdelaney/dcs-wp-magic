package com.dcs;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.Socket;
import java.time.Duration;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.regex.Pattern;


public class TacviewClient {

    private static String[] impact_types = new String[]{"Weapon+Missile", "Weapon+Bomb", "Projectile+Shell"};
    private static String[] parent_types = new String[]{"Weapon+Missile", "Projectile+Shell", "Misc+Decoy+Flare",
            "Misc+Decoy+Chaff", "Misc+Container", "Misc+Shrapnel", "Ground+Light+Human+Air+Parachutist"};
    private Logger LOGGER = LoggerFactory.getLogger(TacviewClient.class);
    private boolean debug = false;
    private List<String> handshake_params = Arrays.asList(
            "XtraLib.Stream.0",
            "Tacview.RealTimeTelemetry.0",
            "tacview_reader",
            "0");
    private String handshake = String.join("\n", handshake_params);
    private HashMap<String, DCSObject> tac_objects = new HashMap<>();
    private DCSRef ref = new DCSRef();
    private int total_parents = 0;
    private int total_impactors = 0;
    private int total_iters = 0;
    private int total_writes = 0;


    public static void main(String[] args) {
        try {
            String host = "127.0.0.1";
            int port = 5555;
            int max_iter = -1;
            boolean pubsub_send = false;

            if (args.length >= 3 && args[0].equals("host"))
                host = args[1];

            if (args.length >= 3 && args[2].equals("port"))
                port = Integer.parseInt(args[3]);

            if (args.length >= 5 && args[4].equals("max_iter"))
                max_iter = Integer.parseInt(args[5]);

            if (args.length >= 7 && args[6].equals("pubsub_send"))
                pubsub_send = Boolean.parseBoolean(args[7]);

            TacviewClient tacview = new TacviewClient();
            tacview.run(host, port, max_iter, pubsub_send);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void run(String host, Integer port, Integer max_iter, Boolean pubsub_send) throws Exception {
        LOGGER.info("Starting tacview collector...");
        LOGGER.info("Connecting to host: " + host);
        LOGGER.info("Connecting on port: " + port);
        LOGGER.info("Maximum iterations to run: " + max_iter);

        PubSub2 object_writer = new PubSub2();
        object_writer.ensureTopicExists("tacview_objects");
        object_writer.createPublisher();

        try {
            Socket socket = new Socket(host, port);
            PrintWriter out = new PrintWriter(socket.getOutputStream(), true);
            BufferedReader input_stream = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            LOGGER.info("Connected...sending handshake...");
            out.print(handshake + "\0"); // send to server
            out.flush();

            input_stream
                    .lines()
                    .takeWhile(v -> (v != null && (total_iters < max_iter)))
                    .forEach(value -> {
                        if (!ref.has_refs) {
                            String[] obj_split = value.split(Pattern.quote(","));
                            if (obj_split[0].equals("0")) {
                                ref.update_ref_value(obj_split);
                            }
                        } else {
                            if (value.substring(0, 1).equals("#")) {
                                ref.update_time_offset(value);
                            } else {
                                DCSObject rec = parseMessageToMapOrUpdate(value);
                                total_iters++;
                                if (pubsub_send && rec != null && !rec.exported) {
                                    object_writer.write(rec);
                                    rec.exported = true;
                                    total_writes++;
                                    LOGGER.info("total: {}", total_writes);
                                }
                            }
                        }
                    });

            object_writer.checkAll();
//            tac_objects.entrySet().
//                    stream().
//                    filter( rec -> (!rec.getValue().exported))
//                    .forEach(rec -> object_writer.write(rec.getValue()));
//
//            object_writer.shutdownPublisher();
//            object_writer.checkPublishedMessages();
//            object_writer.shutDownPublisher();
//
//            session_writer.checkPublishedMessages();
//            session_writer.shutDownPublisher();
//            event_writer.checkPublishedMessages();
//            event_writer.shutDownPublisher();

            out.close();
            input_stream.close();
            socket.close();
            getJobStats();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void getJobStats() {
        Instant end_time = Instant.now();
        Duration time_diff = Duration.between(ref.start_time, end_time);
        long seconds_diff = time_diff.toMillis();
        float iter_per_sec = (total_iters / seconds_diff) * 1000;

        LOGGER.info("Total lines read: " + total_iters);
        LOGGER.info("Lines per second: " + iter_per_sec);
        LOGGER.info("Total keys: " + tac_objects.size());
        LOGGER.info("Total parents: " + total_parents);
        LOGGER.info("Total Impactors: " + total_impactors);
    }

    private DCSObject getOrCreateDCSObject(String key) {
        if (tac_objects.containsKey(key)) {
            DCSObject obj_dict = tac_objects.get(key);
            obj_dict.last_seen = ref.referencetime;
            obj_dict.updates++;
            return obj_dict;
        }

        DCSObject obj_dict = new DCSObject();
        obj_dict.id = key;
        obj_dict.session_id = ref.session_id;
        obj_dict.last_seen = ref.referencetime;
        obj_dict.first_seen = ref.referencetime;
        tac_objects.put(key, obj_dict);
        return obj_dict;
    }

    private boolean filter_types(DCSObject rec, String compare_type) {
        if (compare_type.equals("parent")) {
            return (!Arrays.asList(parent_types).contains(rec.type));
        } else if (compare_type.equals("impactor")) {
            return (Arrays.asList(impact_types).contains(rec.type));
        } else {
            return false;
        }
    }

    private DistanceComparison checkForClosest(DCSObject current_rec, String compare_type) {
        Instant recent_rec_offset = ref.referencetime.plus(1, ChronoUnit.MINUTES);

        if ((compare_type.equals("parent") &&
                (current_rec.updates > 1 ||
                        current_rec.color == null ||
                        Arrays.stream(parent_types).noneMatch(current_rec.type::equals)))) {
            return null;
        }

        String[] accept_colors;
        if (compare_type.equals("parent")) {
            accept_colors = (current_rec.color.equals("Violet")) ? new String[]{"Red", "Blue"} : new String[]{current_rec.color};
        } else {
            accept_colors = (current_rec.color.equals("Blue")) ? new String[]{"Red"} : new String[]{"Blue"};
        }

        @SuppressWarnings("ComparatorCombinators") Optional<DistanceComparison> possible_comps =
                tac_objects.entrySet()
                        .stream()
                        .parallel()
                        .map(Map.Entry::getValue)
                        .filter(rec -> filter_types(rec, compare_type))
                        .filter(rec -> Arrays.asList(accept_colors).contains(rec.color))
                        .filter(rec -> !rec.type.equals(current_rec.type))
                        .filter(rec -> ((rec.alive == 1) | (rec.last_seen.compareTo(recent_rec_offset) > 0)))
                        .map(rec -> DistanceCalculator.compute_distance(rec, current_rec)).min((l1, l2) -> l1.dist.compareTo(l2.dist));

        if (possible_comps.isPresent()) {
            DistanceComparison closest = possible_comps.get();
            LOGGER.debug("{} lookup for {}-{} -- {}-{}: {}",
                    compare_type, current_rec.type, current_rec.id, closest.id, closest.type, closest.dist);
            if (closest.dist < 100) {
                return closest;
            }
            LOGGER.debug("Rejecting closest {} match for {}-{}: {} {}!",
                    compare_type, current_rec.id, current_rec.type, closest.type, closest.dist);
        }
        LOGGER.debug("Zero possible {} matches for {}-{}", compare_type, current_rec.id, current_rec.type);
        return null;
    }

    private DCSObject parseMessageToMapOrUpdate(String obj) {
        String[] obj_split = obj.trim().split(Pattern.quote(","));
        if (obj_split[0].equals("0")) {
            return null;
        }

        if (obj_split[0].substring(0, 1).equals("-")) {
            DCSObject obj_dict = tac_objects.get(obj_split[0].substring(1));
            obj_dict.alive = 0;
            return null;
        }

        String id_val = obj_split[0];
        DCSObject obj_dict = getOrCreateDCSObject(id_val);
        obj_dict.from_string(obj_split, ref);

        DistanceComparison distance = checkForClosest(obj_dict, "parent");
        DCSObject parent;
        if (distance != null) {
            total_parents++;
            obj_dict.parent = distance.id;
            obj_dict.parent_dist = distance.dist;
            parent = getOrCreateDCSObject(obj_dict.parent);
            if (obj_dict.type.equals("Misc+Shrapnel")) {
                DistanceComparison closest = checkForClosest(parent, "impactor");
                if (closest!= null) {
                    total_impactors++;
                    parent.addImpact(closest);
                }
            }
        }
        if (this.debug) {
            obj_dict.print();
        }
        return obj_dict;
    }
}
