package com.dcs;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.UUID;
import java.util.regex.Pattern;

class DCSRef extends DcsDict {
    String session_id = UUID.randomUUID().toString();
    String datasource;
    String author;
    String title;
    Double referencelatitude;
    Double referencelongitude;
    Instant referencetime = Instant.now();
    long start_time = new Date().getTime();
    Double last_offset = 0.0;
    int total_iters = 0;
    boolean has_refs = false;

    public void update_ref_value(String[] obj_split) {

        String[] values = obj_split[1].split(Pattern.quote("="));
        if (values[0].equals("ReferenceLatitude")) {
            this.referencelatitude = Double.valueOf(values[1]);
            this.has_refs = true;
            LOGGER.info("Ref Lat: " + this.referencelatitude);
        }
        if (values[0].equals("ReferenceLongitude")) {
            this.referencelongitude = Double.valueOf(values[1]);
            LOGGER.info("Ref Lon: " + this.referencelongitude);
        }
        if (values[0].equals("ReferenceTime")) {
            this.referencetime = Instant.parse(values[1]);
            LOGGER.info("Ref Time: " + this.referencetime);
        }
        if (values[0].equals("DataSource")) {
            this.datasource = values[1];
            LOGGER.info("DataSource: " + this.datasource);
        }
        if (values[0].equals("Title")) {
            this.title = values[1];
            LOGGER.info("Title: " + this.title);
        }
        if (values[0].equals("Author")) {
            this.author = values[1];
            LOGGER.info("Author: " + this.author);
        }

    }

    public void update_time_offset(String obj) {
        Double new_offset = Double.valueOf(obj.substring(1));
        long diff = Math.round((new_offset - this.last_offset) * 1000);
        this.last_offset = new_offset;
        this.referencetime = this.referencetime.plus(diff, ChronoUnit.MILLIS);
        float time_diff = (int) ((new Date().getTime() - this.start_time));
        float iter_per_sec = (this.total_iters / time_diff) * 1000;
        LOGGER.debug("Updating ref time with offset: " + new_offset + "...Lines per sec: " + iter_per_sec);
    }
}
