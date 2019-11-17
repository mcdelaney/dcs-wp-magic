package com.dcs;

import java.time.Instant;

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
    public Double lat;
    public Double lon;
    public Double alt = 1.0;
    public Double roll;
    public Double pitch;
    public Double yaw;
    public Double u_coord;
    public Double v_coord;
    public Double heading;
    public int update_num = 1;

    public String parent;
    public Double parent_dist;

    public String impactor;
    public Double impactor_dist;
}
