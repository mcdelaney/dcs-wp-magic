package com.dcs;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.Socket;
import java.util.*;
import java.util.regex.Pattern;
import java.util.stream.Stream;
import java.util.stream.Collectors;


public class TacviewClient
{
    private static Logger LOGGER = LogManager.getLogger("Tacview");
    private static String[] coord_keys = new String[]{"long", "lat", "alt", "roll", "pitch", "yaw", "u_coord",  "v_coord", "heading"};

    public static void main (String[] args)
    {
        try
        {
            TacviewClient tacview = new TacviewClient();
            tacview.run(args);
        }
        catch (Exception e)
        {
            e.printStackTrace ();
        }
    }

    private void run(String[] args) throws Exception
    {
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
        try
        {
            socket = new Socket(host, port);
            // socket = new Socket("147.135.8.169", 42674); # Gaw
            out = new PrintWriter(socket.getOutputStream(), true);
            in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            LOGGER.info("Connected");

            // textToServer = read.readLine();
            LOGGER.info("Sending '" + handshake + "'");
            out.print(handshake + "\0"); // send to server
            out.flush();

            long start_time = new Date().getTime();
            int total_iter = 0;
            boolean has_refs = false;

            String obj;
            while (total_iter < max_iter & ((obj = in.readLine()) != null))
            {
                total_iter++;
                if (has_refs){
                    line_to_dict(obj);
                }else{
                    if (obj.length() > 20 && obj.substring(0,20).equals("0,ReferenceLatitude=")) {
                        has_refs = true;
                    }
                }

            }

            long end_time = new Date().getTime();
            float time_diff = (int) ((end_time - start_time));
            float iter_per_sec = (total_iter/time_diff) * 1000;

            LOGGER.info("Total lines read:: " + total_iter);
            LOGGER.info("Time diff: " + time_diff);
            LOGGER.info("Lines per second:: " + iter_per_sec );

            out.close();
            in.close();
            read.close();
            socket.close();
        }
        catch (IOException e)
        {
            e.printStackTrace();
        }
    }

    private HashMap line_to_dict(String obj)
    {
        String[] obj_split = obj.split(",");
        HashMap<String, Object> obj_dict = new HashMap<>() {{
                put("last_seen", new Date().getTime());
                put("session_id", "Best Session");
                put("alive", 1);
                put("group", null);
                put("type", null);
                put("name", null);
                put("pilot", null);
                put("lat", null);
                put("long", null);
                put("alt", null);
                put("roll", null);
                put("pitch", null);
                put("yaw", null);
                put("u_coord", null);
                put("v_coord", null);
                put("heading", null);
            }};

        if (obj_split[0].substring(0, 1) == "-") {
            obj_dict.put("alive", 0);
            obj_dict.put("id", obj_split[0].substring(1));
            return obj_dict
        }else{
            obj_dict.put("id", obj_split[0]);
        }

//        for(String chunk: obj_split) {
        for (int i = 1; i < obj_split.length; i++){
            String[] val = obj_split[i].split(Pattern.quote("="));
            if (val.length == 2) {
                if (val[0].equals("T")) {
                    String[] coordinate_elem = val[1].substring(1).split(Pattern.quote("|"));
                    for (int e = 0; e < Math.min(coord_keys.length, coordinate_elem .length); e++) {
                        if(coordinate_elem [e] == null || coordinate_elem[e].isEmpty()){
                            obj_dict.put(coord_keys[e], null);
                        }else{
                            obj_dict.put(coord_keys[e], Float.valueOf(coordinate_elem[e]));
                        }
                    }
                }else{
                    obj_dict.put(val[0].toLowerCase(), val[1]);
                }
            }
        }
        obj_dict.forEach((key, val) -> LOGGER.debug(key + ": " + val));
        return obj_dict;
    }

}
