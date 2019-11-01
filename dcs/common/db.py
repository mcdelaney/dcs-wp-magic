"""Model definitions for database."""
from pathlib import Path

import peewee as pw
from google.cloud import pubsub_v1


from dcs.common  import config



DB = pw.SqliteDatabase(None,
                       pragmas={'journal_mode': 'wal',
                                'cache_size': -64 * 1000})


class BaseModel(pw.Model):
    """Base model with DB defined from which all others inherit."""

    class Meta:  # pylint: disable=too-few-public-methods
        """Set global database."""
        database = DB


class Object(BaseModel):
    """DCS Object."""
    id = pw.CharField(primary_key=True, index=True)
    session_id = pw.UUIDField()
    name = pw.CharField(null=True)
    color = pw.CharField(null=True)
    country = pw.CharField(null=True)
    grp = pw.CharField(null=True)
    pilot = pw.CharField(null=True)
    platform = pw.CharField(null=True)
    type = pw.CharField(null=True)
    alive = pw.IntegerField(default=1)
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
    debug = pw.CharField(null=True)


class Event(BaseModel):
    """Event History."""
    id = pw.AutoField()
    session_id = pw.UUIDField()
    object = pw.ForeignKeyField(Object, 'id', unique=False)
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


def init_db(replace_db=True):
    """Initialize the database and execute create table statements."""
    db_path = Path(config.DB_LOC)
    if not db_path.parent.exists():
        db_path.parent.mkdir()

    if replace_db:
        if db_path.exists():
            db_path.unlink()
    DB.init(config.DB_LOC)
    DB.create_tables([Object, Event])
    return DB


class Publisher: # pylint: disable=too-few-public-methods
    """Pubsub writer."""

    def __init__(self):
        self.publisher = pubsub_v1.PublisherClient()
        self.objects = self.publisher.topic_path(
            config.PROJECT_ID, 'tacview_objects')
        self.events = self.publisher.topic_path(
            config.PROJECT_ID, 'tacview_events')
