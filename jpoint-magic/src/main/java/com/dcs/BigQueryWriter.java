package com.dcs;

import com.google.cloud.bigquery.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

class BigQueryWriter {
    private Logger LOGGER = LoggerFactory.getLogger(BigQueryWriter.class);
    private BigQuery client = BigQueryOptions.getDefaultInstance().getService();

    private String datasetName = (System.getenv("ENV") == null ||
            !System.getenv("ENV").equals("prod") ? "stg" : "tacview");

    void toBigquery(DCSObject dcs_obj) {
        LOGGER.debug("Writing record id {} to bigquery table {}...", dcs_obj.id, dcs_obj.bigquery_table);
        HashMap<String, Object> record = dcs_obj.toHashMap();
        TableId tableId = TableId.of(datasetName, dcs_obj.bigquery_table);
        InsertAllResponse response =
                this.client.insertAll(
                        InsertAllRequest.newBuilder(tableId)
                                .addRow(record)
                                .build());
        if (response.hasErrors()) {
            LOGGER.error("Error inserting records to bigquery!");
            for (Map.Entry<Long, List<BigQueryError>> entry : response.getInsertErrors().entrySet()) {
                LOGGER.error(entry.toString());
            }
        }
    }
}
