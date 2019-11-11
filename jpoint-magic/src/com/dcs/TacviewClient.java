package com.dcs;

import org.apache.logging.log4j.Level;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.lang.reflect.Field;
import java.net.Socket;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.regex.Pattern;
import java.util.stream.IntStream;


class DcsDict {
    static Logger LOGGER = LogManager.getLogger("ObjDict");

    public void put(String key, Object val) {
        try {
            Class cls = this.getClass();
            Field field = cls.getDeclaredField(key);
            field.setAccessible(true);
            field.set(this, val);

        } catch (NoSuchFieldException | IllegalAccessException e) {
            e.printStackTrace();
            LOGGER.error("Field not found: " + key);
        }
    }

    public void print() {
        Field[] fields = this.getClass().getFields();
        IntStream.range(0, fields.length).forEach(i -> {
            try {
                LOGGER.debug(fields[i].toString() + ": " + fields[i].get(this));
            } catch (IllegalAccessException e) {
                e.printStackTrace();
            }
        });
    }
}

class DCSObject extends DcsDict {
    public String id;
    public Instant first_seen;
    public Instant last_seen;
    public String session_id;
    public String group;
    public String coalition;
    public String country;
    public String color;
    public String type;
    public String name;
    public String pilot;
    public int alive = 1;
    public Float lat;
    public Float lon;
    public Float alt;
    public Float roll;
    public Float pitch;
    public Float yaw;
    public Float u_coord;
    public Float v_coord;
    public Float heading;
}


class DCSRef extends DcsDict {
    String session_id = UUID.randomUUID().toString();
    String datasource;
    String author;
    String title;
    Float referencelatitude;
    Float referencelongitude;
    Instant referencetime = Instant.now();
    long start_time = new Date().getTime();
    Double last_offset = 0.0;
    int total_iters = 0;
    boolean has_refs = false;

    public void update_time_offset(String obj) {
        Double new_offset = Double.valueOf(obj.substring(1));
        long diff = Math.round((new_offset - this.last_offset) * 1000);
        this.last_offset = new_offset;
        this.time = this.time.plus(diff, ChronoUnit.MILLIS);
        float time_diff = (int) ((new Date().getTime() - this.start_time));
        float iter_per_sec = (this.total_iters / time_diff) * 1000;
        LOGGER.info("Updating ref time with offset: " + new_offset + "...Lines per sec: " + iter_per_sec);
    }
}


public class TacviewClient {
    private static Logger LOGGER = LogManager.getLogger("Tacview");
    private static String[] coord_keys = new String[]{"lon", "lat", "alt", "roll", "pitch", "yaw", "u_coord",
            "v_coord", "heading"};

    HashMap<String, DCSObject> tac_objects = new HashMap();
    DCSRef ref = new DCSRef();

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
        int max_iter = 100;

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
                        String[] values = obj_split[1].split(Pattern.quote("="));
                        if (values[0].equals("ReferenceLatitude")) {
                            ref.referencelatitude = Float.valueOf(values[1]);
                            ref.has_refs = true;
                            LOGGER.info("Ref Lat: " + ref.referencelatitude);
                        }
                        if (values[0].equals("ReferenceLongitude")) {
                            ref.referencelongitude= Float.valueOf(values[1]);
                            LOGGER.info("Ref Lon: " + ref.referencelongitude);
                        }
                        if (values[0].equals("ReferenceTime")) {
                            ref.referencetime= Instant.parse(values[1]);
                            LOGGER.info("Ref Time: " + ref.referencetime);
                        }
                        if (values[0].equals("DataSource")) {
                            ref.datasource = values[1];
                            LOGGER.info("DataSource: " + ref.datasource);
                        }
                        if (values[0].equals("Title")) {
                            ref.title = values[1];
                            LOGGER.info("Title: " + ref.title);
                        }
                        if (values[0].equals("Author")) {
                            ref.author = values[1];
                            LOGGER.info("Author: " + ref.author);
                        }
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
            obj_dict.put("last_seen", ref.time);
            return obj_dict;
        }

        DCSObject obj_dict = new DCSObject();
        obj_dict.put("id", key);
        obj_dict.put("session_id", ref.session_id);
        obj_dict.put("last_seen", ref.time);
        tac_objects.put(key, obj_dict);
        return obj_dict;
    }

    private void line_to_dict(String obj) {
        String[] obj_split = obj.split(",");

        if (obj_split[0].equals("0")) {
            return;
        }

        if (obj_split[0].substring(0, 1) == "-") {
            DCSObject obj_dict = tac_objects.get(obj_split[0].substring(1));
            obj_dict.put("alive", 0);
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
                            if (coordinate_elem[e].contains(String[] ["lat", "lon"])) {
                                obj_dict.put(coord_keys[e], Float.valueOf(coordinate_elem[e]));
                            }else{
                                obj_dict.put(coord_keys[e], Float.valueOf(coordinate_elem[e]));
                            }

                        }
                    }
                } else {
                    obj_dict.put(val[0].toLowerCase(), val[1]);
                }
            }
        }
        if (LOGGER.getLevel() == Level.DEBUG) {
            obj_dict.print();
        }
    }
}
