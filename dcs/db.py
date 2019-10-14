import logging
from pathlib import Path
import sqlite3
from . import get_logger

log = get_logger(logging.getLogger(__name__))
log.setLevel(logging.INFO)

COLS = ["id",
        "name",
        "color",
        'country',
        "grp",
        'pilot',
        "platform",
        "type",
        "alive",
        "lastseen",
        "coalition",
        "lat",
        "long",
        "alt"]

INSERT_STR = ','.join(["?" for _ in COLS])

def dict_to_db_string(obj_dict, cols=COLS):
    values = []
    columns = []
    for key, val in obj_dict.items():
        if key in cols:
            columns.append(key)
            if type(val) is bool:
                values.append(f"{str(int(val))}")
            else:
                values.append(f"{str(val)}")
    return columns, values


def update_enemy_field(conn, obj):
    updates = []
    for key, val in obj.items():
        if key in COLS:
            updates.append(f"{key} = '{val}'")

    updates = ' , '.join(updates)
    where_clause = "id = '%s'"  % obj.pop('id')
    cur = conn.cursor()
    cur.execute(f"UPDATE enemies SET {updates} WHERE {where_clause}")

    insert_new_rec(conn, obj, cols=['id', 'lat', 'long', 'alt', 'alive'],
                   table="events")
    return conn.commit()


def insert_new_rec(conn, obj_dict, cols=COLS, table='enemies'):
    columns, values = dict_to_db_string(obj_dict, cols)
    val_string =','.join(["?" for _ in columns])
    cur = conn.cursor()
    cur.execute(f"INSERT INTO {table} ({','.join(columns)})\
                 VALUES ({val_string})", values)
    return conn.commit()


def create_connection(replace_db=False):
    db_path = Path('data/dcs.db')
    if replace_db:
        if db_path.exists():
            db_path.replace("data/dcs_arch.db")

    conn = sqlite3.connect(str(db_path),
                           detect_types=sqlite3.PARSE_DECLTYPES,
                           isolation_level=None)
    conn.execute('pragma journal_mode=wal') # Set journal mode to WAL.
    sqlite3.register_adapter(bool, int)
    sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
    conn.row_factory = sqlite3.Row
    return conn


def create_db(conn):
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS enemies")
    cur.execute("DROP TABLE IF EXISTS events")
    conn.commit()
    cur.execute('''
              CREATE TABLE enemies
                (id text PRIMARY KEY,
                 name text,
                 color text,
                 country text,
                 grp text,
                 pilot text,
                 platform text,
                 type text,
                 alive BOOLEAN,
                 lastseen int,
                 coalition text,
                 lat float,
                 long float,
                 alt float
                 )
              ''')
    conn.commit()
    cur.execute('''
                  CREATE TABLE events
                    (id text,
                     lat float,
                     long float,
                     alt float,
                     alive BOOLEAN DEFAULT 1
                     )
                  ''')
    conn.commit()
    return conn
