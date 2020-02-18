"""Model definitions for database."""
from pathlib import Path

import peewee as pw

from dcs.common import config

# DB = PooledSqliteDatabase(None,
#                           check_same_thread=False,
#                           max_connections=10,
#                           pragmas={
#                               'journal_mode': 'wal',
#                               'synchronous': 'OFF',
#                               'cache_size': -1024 * 1000
#                           })

DB = pw.SqliteDatabase(None,
                         pragmas={
                            #  'locking_mode': 'EXCLUSIVE',
                             'journal_mode': 'off',
                            #  'journal_mode': 'wal',
                             'synchronous': 'OFF',
                             'cache_size': -1024 * 4000
                         })


class BaseModel(pw.Model):
    """Base model with DB defined from which all others inherit."""
    class Meta:  # pylint: disable=too-few-public-methods
        """Set global database."""
        database = DB


class Object(BaseModel):
    """DCS Object."""
    id = pw.IntegerField(primary_key=True)
    session_id = pw.IntegerField()
    name = pw.CharField(null=True)
    color = pw.CharField(null=True, index=True)
    country = pw.CharField(null=True)
    grp = pw.CharField(null=True)
    pilot = pw.CharField(null=True)
    platform = pw.CharField(null=True)
    type = pw.CharField(null=True)
    alive = pw.IntegerField(default=1, index=True)
    first_seen = pw.DateTimeField()
    last_seen = pw.DateTimeField(index=True)
    time_offset = pw.FloatField()
    coalition = pw.CharField(null=True)
    lat = pw.FloatField()
    lon = pw.FloatField()
    alt = pw.FloatField(default=1)
    roll = pw.FloatField(null=True)
    pitch = pw.FloatField(null=True)
    yaw = pw.FloatField(null=True)
    u_coord = pw.FloatField(null=True)
    v_coord = pw.FloatField(null=True)
    heading = pw.FloatField(null=True)
    updates = pw.IntegerField(default=1)
    velocity_kts = pw.FloatField(null=True)

    impactor = pw.CharField(null=True)
    impactor_dist = pw.FloatField(null=True)

    parent = pw.CharField(null=True)
    parent_dist = pw.FloatField(null=True)

    debug = pw.CharField(null=True)


class Event(BaseModel):
    """Event History."""
    id = pw.IntegerField()
    session_id = pw.IntegerField()
    last_seen = pw.DateTimeField()
    time_offset = pw.FloatField()
    alive = pw.IntegerField(default=1)
    lat = pw.FloatField(null=True)
    lon = pw.FloatField(null=True)
    alt = pw.FloatField(null=True)

    roll = pw.FloatField(null=True)
    pitch = pw.FloatField(null=True)
    yaw = pw.FloatField(null=True)
    u_coord = pw.FloatField(null=True)
    v_coord = pw.FloatField(null=True)
    heading = pw.FloatField(null=True)
    # dist_m = pw.FloatField(null=True)
    velocity_kts = pw.FloatField(null=True)
    secs_from_last = pw.FloatField(null=True)
    updates = pw.IntegerField(null=False)


class Session(BaseModel):
    """Session Reference Data."""
    session_id = pw.AutoField()
    session_uuid = pw.CharField()
    start_time = pw.DateTimeField()
    datasource = pw.CharField(default=None)
    author = pw.CharField(default=None)
    title = pw.CharField(default=None)
    lat = pw.FloatField()
    lon = pw.FloatField()
    time = pw.DateTimeField()
    time_offset = pw.FloatField()


class TestTable(BaseModel):
    debug = pw.CharField()


def init_db(drop=True):
    """Initialize the database and execute create table statements."""
    db_path = Path(config.DB_LOC)
    if db_path.exists():
        db_path.unlink()
    elif not db_path.parent.exists():
        db_path.parent.mkdir()
    DB.init(config.DB_LOC)

    DB.connect()
    if drop:
        DB.drop_tables([Object, Event, Session, TestTable])
    DB.create_tables([Object, Event, Session, TestTable])
