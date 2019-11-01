from google.cloud import bigquery

client = bigquery.Client()


events_schema = [
    bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("object", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("alive", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("last_seen", "timestamp", mode="NULLABLE"),
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
    table = client.create_table(table)
except Exception:
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
    bigquery.SchemaField("first_seen", "timestamp", mode="NULLABLE"),
    bigquery.SchemaField("alive", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("last_seen", "timestamp", mode="NULLABLE"),
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
    table = client.create_table(table)
except Exception:
    print("error creating objects!")
