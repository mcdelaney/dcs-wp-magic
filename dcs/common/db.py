"""Model definitions for database."""
from pathlib import Path

import peewee as pw
from google.cloud import pubsub_v1


from dcs.common  import config


DB = pw.SqliteDatabase(None,
                       pragmas={'journal_mode': 'wal',
                                'cache_size': -1024 * 1000})


class BaseModel(pw.Model):
    """Base model with DB defined from which all others inherit."""

    class Meta:  # pylint: disable=too-few-public-methods
        """Set global database."""
        database = DB


class Object(BaseModel):
    """DCS Object."""
    id = pw.CharField(primary_key=True)
    session_id = pw.CharField()
    name = pw.CharField(null=True)
    color = pw.CharField(null=True, index=True)
    country = pw.CharField(null=True)
    grp = pw.CharField(null=True)
    pilot = pw.CharField(null=True)
    platform = pw.CharField(null=True)
    type = pw.CharField(null=True)
    alive = pw.IntegerField(default=1, index=True)
    first_seen = pw.DateTimeField()
    last_seen = pw.DateTimeField()
    coalition = pw.CharField(null=True)
    lat = pw.FloatField()
    long = pw.FloatField()
    alt = pw.FloatField(default=1)
    roll = pw.FloatField(null=True)
    pitch = pw.FloatField(null=True)
    yaw = pw.FloatField(null=True)
    u_coord = pw.FloatField(null=True)
    v_coord = pw.FloatField(null=True)
    heading = pw.FloatField(null=True)
    updates = pw.IntegerField(default=1)
    parent = pw.CharField(null=True)
    parent_dist = pw.FloatField(null=True)
    debug = pw.CharField(null=True)


class Event(BaseModel):
    """Event History."""
    id = pw.AutoField()
    session_id = pw.CharField()
    object = pw.CharField()
    alive = pw.IntegerField(default=1)
    last_seen = pw.DateTimeField()
    lat = pw.FloatField(null=True)
    long = pw.FloatField(null=True)
    alt = pw.FloatField(null=True)

    roll = pw.FloatField(null=True)
    pitch = pw.FloatField(null=True)
    yaw = pw.FloatField(null=True)
    u_coord = pw.FloatField(null=True)
    v_coord = pw.FloatField(null=True)
    heading = pw.FloatField(null=True)
    dist_m = pw.FloatField(null=True)
    velocity_ms = pw.FloatField(null=True)
    secs_from_last = pw.FloatField(null=True)
    update_num = pw.IntegerField(null=False)


class Session(BaseModel):
    """Session Reference Data."""
    session_id = pw.CharField()
    start_time = pw.DateTimeField()
    datasource = pw.CharField()
    author = pw.CharField()
    title = pw.CharField()
    lat = pw.FloatField()
    long = pw.FloatField()
    time = pw.DateTimeField()


def init_db():
    """Initialize the database and execute create table statements."""
    db_path = Path(config.DB_LOC)
    DB.init(config.DB_LOC)
    if not db_path.parent.exists():
        db_path.parent.mkdir()
    DB.connect()
    DB.drop_tables([Object, Event, Session])
    DB.create_tables([Object, Event, Session])
    return DB


class Publisher: # pylint: disable=too-few-public-methods
    """Pubsub writer."""

    def __init__(self):
        # pylint: disable=no-member
        self.writer = pubsub_v1.PublisherClient()
        self.objects = self.writer.topic_path(
            config.PROJECT_ID, 'tacview_objects')
        self.events = self.writer.topic_path(
            config.PROJECT_ID, 'tacview_events')
        self.sessions = self.writer.topic_path(
            config.PROJECT_ID, 'tacview_sessions')
