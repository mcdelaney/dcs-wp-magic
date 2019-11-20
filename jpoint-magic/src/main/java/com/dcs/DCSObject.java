package com.dcs;

import java.time.Instant;
import java.util.ArrayList;
import java.util.regex.Pattern;


class CoordKeys {
    String[] keys = new String[]{"lon", "lat", "alt", "roll", "pitch", "yaw", "u_coord",
            "v_coord", "heading"};
}



class DCSObject extends DcsDict {
    Boolean exported = false;
    String bigquery_table = "objects";
    String topic = "tacview_objects";
    public String id;
    public Instant first_seen;
    public Instant last_seen;
    public String session_id;
    public String grp;
    public String coalition;
    public String country;
    public String color;
    public String type;
    public String platform;
    public String name;
    public String pilot;
    public int alive = 1;
    public Double lat;
    public Double lon;
    public Double alt = 1.0;
    public Double roll;
    public Double pitch;
    public Double yaw;
    public Double u_coord;
    public Double v_coord;
    public Double heading;
    public int updates = 1;
    public String parent;
    public Double parent_dist;
    public ArrayList<Impactor> impacts = new ArrayList<>();


    class Impactor{
        String id;
        Double dist;
    }

    void addImpact(DistanceComparison impact){
        Impactor new_impact = new Impactor();
        new_impact.id = impact.id;
        new_impact.dist = impact.dist;
        this.impacts.add(new_impact);
    }

    void from_string(String[] obj_split, DCSRef ref) {
        CoordKeys coords = new CoordKeys();
        for (int i = 1; i < obj_split.length; i++) {
            String[] val = obj_split[i].split(Pattern.quote("="));
            if (val.length == 2) {
                if (val[0].equals("T")) {
                    String[] coordinate_elem = val[1].substring(1).split(Pattern.quote("|"));
                    for (int e = 0; e < Math.min(coords.keys.length, coordinate_elem.length); e++) {
                        if (!(coordinate_elem[e] == null || coordinate_elem[e].isEmpty())) {
                            if (coords.keys[e].equals("lat")) {
                                Double c_val = Double.valueOf(coordinate_elem[e]) + ref.referencelatitude;
                                this.put(coords.keys[e], c_val);
                            } else if (coords.keys[e].equals("lon")) {
                                this.put(coords.keys[e], Double.valueOf(coordinate_elem[e]));
                                Double c_val = Double.valueOf(coordinate_elem[e]) + ref.referencelongitude;
                                this.put(coords.keys[e], c_val);
                            } else {
                                this.put(coords.keys[e], Double.valueOf(coordinate_elem[e]));
                            }
                        }
                    }
                } else {
                    this.put(val[0].toLowerCase(), val[1]);
                }
            }
        }
    }
}
