"""Script to create bigquery tables for event stream."""
from google.cloud import bigquery # pylint: disable=no-name-in-module


def main():
    """Do the job."""
    client = bigquery.Client()

    events_schema = [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("object", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("alive", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("last_seen", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("lat", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("long", "FLOAT", mode="NULLABLE"),
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
        events_tbl_id = "dcs-analytics-257714.tacview.events"
        table = bigquery.Table(events_tbl_id, schema=events_schema)
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
        bigquery.SchemaField("long", "FLOAT", mode="NULLABLE"),
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
        bigquery.SchemaField("parent", "STRING", mode="NULLABLE")
    ]

    try:
        objects_tbl_id = "dcs-analytics-257714.tacview.objects"
        table = bigquery.Table(objects_tbl_id, schema=objects_schema)
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
        bigquery.SchemaField("lat", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("long", "FLOAT", mode="REQUIRED"),

    ]
    try:
        sessions_tbl_id = "dcs-analytics-257714.tacview.sessions"
        table = bigquery.Table(sessions_tbl_id, schema=sessions_schema)
        table = client.create_table(table)
    except Exception as err:
        print(err)
        print("error creating sessions!")


if __name__ == "__main__":
    main()
