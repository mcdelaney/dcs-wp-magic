import logging
import sqlite3
from . import get_logger

log = get_logger(logging.getLogger(__name__))
log.setLevel(logging.INFO)

COLS = ["id",
        "name",
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

def dict_to_db_string(obj_dict):
    ent = []
    for c in COLS:
        if type(obj_dict[c]) is bool:
            ent.append(f"{str(int(obj_dict[c]))}")
        else:
            ent.append(f"{str(obj_dict[c])}")
    return ent
    # return ','.join(ent)


def update_enemy_field(conn, id, field, value):
    if type(value) is bool:
        value = str(int(value))
    cur = conn.cursor()
    cur.execute(f"UPDATE enemies SET {field} = '{value}' WHERE id = '{id}'")
    return conn.commit()


def insert_new_rec(conn, obj_dict):
    string = dict_to_db_string(obj_dict)
    cur = conn.cursor()
    cur.execute(f"INSERT INTO enemies VALUES ({INSERT_STR})", string)
    return conn.commit()


def create_connection():
    conn = sqlite3.connect("/tmp/dcs.db",
                           detect_types=sqlite3.PARSE_DECLTYPES,
                           isolation_level=None)

    # Set journal mode to WAL.
    conn.execute('pragma journal_mode=wal')
    sqlite3.register_adapter(bool, int)
    sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
    return conn


def truncate_enemies(conn):
    log.info("Truncating enemies table...")
    cur = conn.cursor()
    cur.execute("DELETE FROM enemies")
    conn.commit()
    return


def create_db(conn):
     # PRIMARY KEY
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS enemies")
    conn.commit()
    cur.execute('''
              CREATE TABLE enemies
                (id text,
                 name text,
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
    return conn
