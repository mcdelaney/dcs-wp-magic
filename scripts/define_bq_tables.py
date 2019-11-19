#!/usr/bin/env python3
"""Script to create bigquery tables for event stream."""
import argparse
from google.cloud import bigquery # pylint: disable=no-name-in-module


def main(dataset, replace=False):
    """Do the job."""
    client = bigquery.Client()

    events_schema = [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("object", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("alive", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("last_seen", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("lat", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("lon", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("alt", "float", mode="NULLABLE"),
        bigquery.SchemaField("roll", "float", mode="NULLABLE"),
        bigquery.SchemaField("pitch", "float", mode="NULLABLE"),
        bigquery.SchemaField("yaw", "float", mode="NULLABLE"),
        bigquery.SchemaField("u_coord", "float", mode="NULLABLE"),
        bigquery.SchemaField("v_coord", "float", mode="NULLABLE"),
        bigquery.SchemaField("heading", "float", mode="NULLABLE"),
        bigquery.SchemaField("dist_m", "float", mode="NULLABLE"),
        bigquery.SchemaField("velocity_ms", "float", mode="NULLABLE"),
        bigquery.SchemaField("secs_from_last", "float", mode="NULLABLE"),
        bigquery.SchemaField("update_num", "INTEGER", mode="NULLABLE")
    ]
    try:
        events_tbl_id = f"dcs-analytics-257714.{dataset}.events"
        table = bigquery.Table(events_tbl_id, schema=events_schema)

        if replace:
            print(f"Deleting table {events_tbl_id}")
            client.delete_table(table, not_found_ok=True)

        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="last_seen",  # name of column to use for partitioning
            expiration_ms=None,
        )

        table = client.create_table(table)
    except Exception as err:
        print(err)
        print("error creating events!")


    objects_schema = [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("color", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("country", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("grp", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("pilot", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("platform", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("type", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("coalition", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("first_seen", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("alive", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("last_seen", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("lat", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("lon", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("alt", "float", mode="NULLABLE"),
        bigquery.SchemaField("roll", "float", mode="NULLABLE"),
        bigquery.SchemaField("pitch", "float", mode="NULLABLE"),
        bigquery.SchemaField("yaw", "float", mode="NULLABLE"),
        bigquery.SchemaField("u_coord", "float", mode="NULLABLE"),
        bigquery.SchemaField("v_coord", "float", mode="NULLABLE"),
        bigquery.SchemaField("heading", "float", mode="NULLABLE"),
        bigquery.SchemaField("dist_m", "float", mode="NULLABLE"),
        bigquery.SchemaField("velocity_ms", "float", mode="NULLABLE"),
        bigquery.SchemaField("secs_from_last", "float", mode="NULLABLE"),
        bigquery.SchemaField("updates", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("parent", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("parent_dist", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("impacts", "RECORD", mode="REPEATED",
                             fields=[
                                 bigquery.SchemaField("id", "String", mode="NULLABLE"),
                                 bigquery.SchemaField("dist", "FLOAT", mode="NULLABLE"),
                             ])
    ]

    try:
        objects_tbl_id = f"dcs-analytics-257714.{dataset}.objects"
        table = bigquery.Table(objects_tbl_id, schema=objects_schema)
        if replace:
            print(f"Deleting table {objects_tbl_id}")
            client.delete_table(table, not_found_ok=True)

        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="first_seen",  # name of column to use for partitioning
            expiration_ms=None,
        )
        table = client.create_table(table)
    except Exception as err:
        print(err)
        print("error creating objects!")


    sessions_schema = [
        bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("author", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("datasource", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("start_time", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("referencelongitude", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("referencelatitude", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("referencetime", "TIMESTAMP", mode="REQUIRED"),
    ]

    try:
        sessions_tbl_id = f"dcs-analytics-257714.{dataset}.sessions"
        table = bigquery.Table(sessions_tbl_id, schema=sessions_schema)
        if replace:
            print(f"Deleting table {sessions_tbl_id}")
            client.delete_table(table, not_found_ok=True)

        table = client.create_table(table)
    except Exception as err:
        print(err)
        print("error creating sessions!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="stg", type=str)
    parser.add_argument("--replace", default=False, type=bool)
    args = parser.parse_args()
    main(args.dataset, args.replace)
