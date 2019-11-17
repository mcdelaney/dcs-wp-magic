package com.dcs;

//import org.apache.logging.log4j.Level;
//import org.apache.logging.log4j.LogManager;
//import org.apache.logging.log4j.Logger;

import com.google.cloud.bigquery.BigQuery;
import com.google.cloud.bigquery.BigQueryOptions;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.Socket;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.regex.Pattern;


public class TacviewClient {
    private static String[] coord_keys = new String[]{"lon", "lat", "alt", "roll", "pitch", "yaw", "u_coord",
            "v_coord", "heading"};
    private static String[] parent_types = new String[]{"Weapon+Missile", "Projectile+Shell", "Misc+Decoy+Flare",
            "Misc+Decoy+Chaff", "Misc+Container", "Misc+Shrapnel", "Ground+Light+Human+Air+Parachutist"};
    private static String[] impact_types = new String[]{"Weapon+Missile", "Projectile+Shell"};
    Logger LOGGER = LoggerFactory.getLogger("Tacview");
    boolean debug = false;
    BigQuery bigquery = BigQueryOptions.getDefaultInstance().getService();

    HashMap<String, DCSObject> tac_objects = new HashMap();
    DCSRef ref = new DCSRef();

    DistanceCalculator dist_calc = new DistanceCalculator();
    int total_parents = 0;
    int total_impactors = 0;

    public static void main(String[] args) {
        try {
            TacviewClient tacview = new TacviewClient();
            tacview.run(args);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void run(String[] args) throws Exception {
        LOGGER.info("Starting tacview collector...");
        String host = "127.0.0.1";

        int port = 5555;
        int max_iter = 10000;

        if (args.length >= 3 && args[0].equals("host"))
            host = args[1];

        if (args.length >= 3 && args[2].equals("port"))
            port = Integer.parseInt(args[3]);

        if (args.length >= 5 && args[4].equals("max_iter"))
            max_iter = Integer.parseInt(args[5]);

        LOGGER.info("Connecting to host: " + host);
        LOGGER.info("Connecting on port: " + port);
        LOGGER.info("Maximum iterations to run: " + max_iter);

        List<String> handshake_params = Arrays.asList(
                "XtraLib.Stream.0",
                "Tacview.RealTimeTelemetry.0",
                "tacview_reader",
                "0"
        );
        String handshake = String.join("\n", handshake_params);
        Socket socket;
        PrintWriter out;
        BufferedReader in;
        BufferedReader read = new BufferedReader(new InputStreamReader(System.in));
        try {
            socket = new Socket(host, port);
            out = new PrintWriter(socket.getOutputStream(), true);
            in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            LOGGER.info("Connected...sending handshake...");
            out.print(handshake + "\0"); // send to server
            out.flush();

            String obj;
            while ((max_iter == 0 || ref.total_iters < max_iter) & ((obj = in.readLine()) != null)) {
                ref.total_iters++;
                if (ref.has_refs) {
                    if (obj.substring(0, 1).equals("#")) {
                        ref.update_time_offset(obj);

                    } else {
                        line_to_dict(obj);
                    }
                } else {
                    String[] obj_split = obj.split(Pattern.quote(","));
                    if (obj_split[0].equals("0")) {
                        ref.update_ref_value(obj_split);
                    }
                }

            }

            long end_time = new Date().getTime();
            float time_diff = (int) ((end_time - ref.start_time));
            float iter_per_sec = (ref.total_iters / time_diff) * 1000;

            LOGGER.info("Total lines read:: " + ref.total_iters);
            LOGGER.info("Time diff: " + time_diff);
            LOGGER.info("Lines per second: " + iter_per_sec);
            LOGGER.info("Total keys: " + tac_objects.size());
            LOGGER.info("Total parents: " + total_parents);
            LOGGER.info("Total Impactors: " + total_impactors);

            out.close();
            in.close();
            read.close();
            socket.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private DCSObject get_or_create(String key) {
        if (tac_objects.containsKey(key)) {
            DCSObject obj_dict = tac_objects.get(key);
            obj_dict.last_seen = ref.referencetime;
            obj_dict.update_num++;
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

    private DistanceComparison check_for_parent(DCSObject current_rec) {

        Instant recent_rec_offset = ref.referencetime.plus(1, ChronoUnit.MINUTES);

        if (current_rec.update_num > 1 || current_rec.color == null || !Arrays.stream(parent_types).anyMatch(current_rec.type::equals)) {
            return null;
        }

        String[] accept_colors = (current_rec.color.equals("Violet")) ? new String[]{"Red", "Blue"} : new String[]{current_rec.color};
        Optional<DistanceComparison> possible_parents = tac_objects.entrySet()
                .stream()
                .parallel()
                .map(Map.Entry::getValue)
                .filter(rec -> (!Arrays.asList(parent_types).contains(rec.type)))
                .filter(rec -> Arrays.asList(accept_colors).contains(rec.color))
                .filter(rec -> !rec.type.equals(current_rec.type))
                .filter(rec -> (rec.alive == 1 | rec.last_seen.compareTo(recent_rec_offset) > 0))
                .map(rec -> DistanceCalculator.compute_distance(rec, current_rec))
                .sorted((l1, l2) -> Double.compare(l1.dist, l2.dist))
                .findFirst();

        if (possible_parents.isPresent()) {
            DistanceComparison closest = possible_parents.get();
            LOGGER.debug("Parent lookup for {}-{} -- {}-{}: {}", current_rec.type, current_rec.id, closest.id, closest.type, closest.dist);
            if (closest.dist < 100) {
                return closest;
            } else {
                LOGGER.warn("Rejecting closest parent match for {}-{}: {} {}!", current_rec.id, current_rec.type, closest.type, closest.dist);
            }
        }

        return null;
    }

    private DistanceComparison check_for_impactor(DCSObject current_rec) {

        Instant recent_rec_offset = ref.referencetime.plus(1, ChronoUnit.MINUTES);

//        if (!current_rec.type.equals("Misc+Shrapnel")) {
//            return null;
//        }

        String[] accept_colors = (current_rec.color.equals("Blue")) ? new String[]{"Red"} : new String[]{"Blue"};
        Optional<DistanceComparison> possible_impactors = tac_objects.entrySet()
                .stream()
                .parallel()
                .map(Map.Entry::getValue)
                .filter(rec -> Arrays.asList(impact_types).contains(rec.type))
                .filter(rec -> Arrays.asList(accept_colors).contains(rec.color))
                .filter(rec -> !rec.type.equals(current_rec.type))
                .filter(rec -> (rec.alive == 1 | rec.last_seen.compareTo(recent_rec_offset) > 0))
                .map(rec -> DistanceCalculator.compute_distance(rec, current_rec))
                .sorted((l1, l2) -> l1.dist.compareTo(l2.dist))
                .findFirst();

        if (possible_impactors.isPresent()) {
            DistanceComparison closest = possible_impactors.get();
            if (closest.dist < 100) {
                LOGGER.debug("Impactor lookup for {}-{} -- {}-{}: {}", current_rec.type, current_rec.id, closest.id,
                        closest.type, closest.dist);
                return closest;
            } else {
                LOGGER.warn("Rejecting closest impactor match for {}-{}: {} {}!", current_rec.id, current_rec.type, closest.type, closest.dist);
            }
        }
        return null;
    }

    private void line_to_dict(String obj) {
        String[] obj_split = obj.split(",");

        if (obj_split[0].equals("0")) {
            return;
        }

        if (obj_split[0].substring(0, 1) == "-") {
            DCSObject obj_dict = tac_objects.get(obj_split[0].substring(1));
            obj_dict.alive = 0;
            return;
        }

        String id_val = obj_split[0];
        DCSObject obj_dict = get_or_create(id_val);

        for (int i = 1; i < obj_split.length; i++) {
            String[] val = obj_split[i].split(Pattern.quote("="));
            if (val.length == 2) {
                if (val[0].equals("T")) {
                    String[] coordinate_elem = val[1].substring(1).split(Pattern.quote("|"));
                    for (int e = 0; e < Math.min(coord_keys.length, coordinate_elem.length); e++) {
                        if (!(coordinate_elem[e] == null || coordinate_elem[e].isEmpty())) {
                            if (coord_keys[e].equals("lat")) {
                                Double c_val = Double.valueOf(coordinate_elem[e]) + ref.referencelatitude;
                                obj_dict.put(coord_keys[e], c_val);
                            } else if (coord_keys[e].equals("lon")) {
                                obj_dict.put(coord_keys[e], Double.valueOf(coordinate_elem[e]));
                                Double c_val = Double.valueOf(coordinate_elem[e]) + ref.referencelongitude;
                                obj_dict.put(coord_keys[e], c_val);
                            } else {
                                obj_dict.put(coord_keys[e], Double.valueOf(coordinate_elem[e]));
                            }
                        }
                    }
                } else {
                    obj_dict.put(val[0].toLowerCase(), val[1]);
                }
            }
        }

        DistanceComparison distance = check_for_parent(obj_dict);
        if (distance != null) {
            total_parents++;
            obj_dict.parent = distance.id;
            obj_dict.parent_dist = distance.dist;
            DCSObject parent = tac_objects.get(obj_dict.parent);
            if (obj_dict.type.equals("Misc+Shrapnel")) {
                DistanceComparison impactor_dist = check_for_impactor(obj_dict);
                if (impactor_dist != null) {
                    total_impactors++;
                    parent.parent = impactor_dist.id;
                    parent.parent_dist = impactor_dist.dist;
                }
            }
        }
        if (this.debug) {
            obj_dict.print();
        }
    }
}
