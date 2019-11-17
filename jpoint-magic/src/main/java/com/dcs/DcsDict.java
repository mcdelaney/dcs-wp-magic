package com.dcs;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.lang.reflect.Field;
import java.util.stream.IntStream;

class DcsDict {

    static Logger LOGGER = LoggerFactory.getLogger("ObjDict");

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
