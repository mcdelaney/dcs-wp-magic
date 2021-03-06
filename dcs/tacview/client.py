"""
Tacview client methods.

Results are parsed into usable format, and then written to a postgres database.
"""
from io import BytesIO
import asyncio
from asyncio.log import logging
from datetime import datetime
from functools import lru_cache
from math import sqrt, cos, sin, radians
from pathlib import Path
from typing import Optional, Any, Dict, List, Tuple
import time
import struct

import pandas as pd
import psycopg2 as pg
import sqlalchemy as sa
from dcs.common.db import Object, Event, Impact, PG_URL
import asyncpg

DB = None
CLIENT = 'someone_somewhere'
PASSWORD = '0'
STREAM_PROTOCOL = "XtraLib.Stream.0"
TACVIEW_PROTOCOL = 'Tacview.RealTimeTelemetry.0'
HANDSHAKE_TERMINATOR = "\0"

HANDSHAKE = ('\n'.join([STREAM_PROTOCOL, TACVIEW_PROTOCOL, CLIENT, PASSWORD]) +
             HANDSHAKE_TERMINATOR).encode('utf-8')

COORD_KEYS = ('lon', 'lat', 'alt', 'roll', 'pitch', 'yaw', 'u_coord',
              'v_coord', 'heading')
COORD_KEY_LEN = len(COORD_KEYS)

REF_TIME_FMT = '%Y-%m-%dT%H:%M:%S.%fZ'
HOST = '147.135.8.169'  # Hoggit Gaw
PORT = 42674
DEBUG = False

LOG = logging.getLogger('tacview_client')
LOG.setLevel(logging.INFO)
logFormatter = logging.Formatter(
    "%(asctime)s [%(name)s] [%(levelname)-5.5s]  %(message)s")
file_path = Path(f"log/{LOG.name}.log")
if not file_path.parent.exists():
    file_path.parent.mkdir()
fileHandler = logging.FileHandler(file_path, 'w')
fileHandler.setFormatter(logFormatter)
LOG.addHandler(fileHandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
LOG.addHandler(consoleHandler)
LOG.propagate = False


class Ref:  # pylint: disable=too-many-instance-attributes
    """Hold and extract Reference values used as offsets."""
    def __init__(self):
        self.session_id: Optional[int] = None
        self.lat: Optional[float] = None
        self.lon: Optional[float] = None
        self.title: Optional[str] = None
        self.datasource: Optional[str] = None
        self.author: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.time_offset: float = 0.0
        self.all_refs: bool = False
        self.time_since_last: float = 0.0
        self.diff_since_last: float = 0.0
        self.obj_store: Dict[int, ObjectRec] = {}
        self.all_refs: bool = False
        self.written: bool = False
        self.time_since_last_events: float = 0.0

    def update_time(self, offset):
        """Update the refence time attribute with a new offset."""
        offset = float(offset[1:])
        self.diff_since_last = offset - self.time_offset
        self.time_since_last += self.diff_since_last
        self.time_since_last_events += self.diff_since_last
        self.time_offset = offset

    def update_db(self):
        self.time_since_last = 0.0

    def write_events_db(self):
        self.time_since_last_events = 0.0

    async def parse_ref_obj(self, line):
        """
        Attempt to extract ReferenceLatitude, ReferenceLongitude or
        ReferenceTime from a line object.
        """
        try:
            val = line.split(b',')[-1].split(b'=')

            if val[0] == b'ReferenceLatitude':
                LOG.debug('Ref latitude found...')
                self.lat = float(val[1])

            elif val[0] == b'ReferenceLongitude':
                LOG.debug('Ref longitude found...')
                self.lon = float(val[1])

            elif val[0] == b'DataSource':
                LOG.debug('Ref datasource found...')
                self.datasource = val[1].decode('UTF-8')

            elif val[0] == b'Title':
                LOG.debug('Ref Title found...')
                self.title = val[1].decode('UTF-8')

            elif val[0] == b'Author':
                LOG.debug('Ref Author found...')
                self.author = val[1].decode('UTF-8')

            elif val[0] == b'RecordingTime':
                LOG.debug('Ref time found...')
                self.start_time = datetime.strptime(val[1].decode('UTF-8'),
                                              REF_TIME_FMT)

            self.all_refs = all(f
                                for f in [self.lat and self.lon and self.start_time])
            if self.all_refs and not self.written:
                LOG.info("All Refs found...writing session data to db...")
                sess_ser = self.ser()
                sql = f"""INSERT into session ({','.join(sess_ser.keys())})
                        VALUES({','.join(["$"+str(i+1) for i, _ in enumerate(sess_ser.keys())])})
                        RETURNING session_id
                """
                self.session_id = await DB.fetchval(sql, *sess_ser.values())
                self.written = True
                LOG.info("Session session data saved...")
        except IndexError:
            pass

    def ser(self):
        """Serialize relevant Session fields for export."""
        return {
            'lat': self.lat,
            'lon': self.lon,
            'title': self.title,
            'datasource': self.datasource,
            'author': self.author,
            'start_time': self.start_time
        }


# @dataclass
class ObjectRec:
    __slots__ = [
        'id', 'first_seen', 'last_seen', 'session_id', 'alive', 'Name',
        'Color', 'Country', 'grp', 'Pilot', 'Type', 'Coalition', 'lat', 'lon',
        'alt', 'roll', 'pitch', 'yaw', 'u_coord', 'v_coord', 'heading',
        'impacted', 'impacted_dist', 'parent', 'parent_dist', 'updates',
        'velocity_kts', 'secs_since_last_seen', 'written', 'cart_coords'
    ]

    def __init__(
            self,
            id_: int = None,
            first_seen: Optional[float] = None,
            last_seen: Optional[float] = None,
            session_id: Optional[int] = None):
        self.id = id_
        self.first_seen = first_seen
        self.last_seen = last_seen
        self.session_id = session_id

        self.alive: int = 1
        self.Name: Optional[str] = None
        self.Color: Optional[str] = None
        self.Country: Optional[str] = None
        self.grp: Optional[str] = None
        self.Pilot: Optional[str] = None
        self.Type: Optional[str] = None
        self.Coalition: Optional[str] = None
        self.lat: Optional[float] = None
        self.lon: Optional[float] = None
        self.alt: Optional[float] = 1  # Ships will have null alt
        self.roll: Optional[float] = 0.0
        self.pitch: Optional[float] = 0.0
        self.yaw: Optional[float] = 0.0
        self.u_coord: Optional[float] = None
        self.v_coord: Optional[float] = None
        self.heading: Optional[float] = 0.0
        self.impacted: Optional[int] = None
        self.impacted_dist: Optional[float] = None
        self.parent: Optional[int] = None
        self.parent_dist: Optional[float] = None
        self.updates: int = 1
        self.velocity_kts: float = 0.0
        self.secs_since_last_seen: Optional[float] = None
        self.written: bool = False
        self.cart_coords: Optional[Tuple] = None

    def update_val(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def update_last_seen(self, value: float) -> None:
        self.secs_since_last_seen = value - self.last_seen
        self.last_seen = value

    def compute_velocity(self, time_since_last_frame: float) -> None:
        """Calculate velocity given the distance from the last point."""
        new_cart_coords = get_cartesian_coord(self.lat, self.lon, self.alt)
        # new_cart_coords = tuple((self.v_coord, self.u_coord, self.alt))
        if self.cart_coords is not None and self.secs_since_last_seen and self.secs_since_last_seen > 0:
            true_dist = compute_dist(new_cart_coords, self.cart_coords)
            self.velocity_kts = (true_dist /
                                 self.secs_since_last_seen) / 1.94384
        self.cart_coords = new_cart_coords

    def should_have_parent(self):
        tval = self.Type.lower()
        return any([
            t in tval
            for t in ['weapon', 'projectile',
                      'decoy',
                      'container',
                      'flare']
        ])


def get_cartesian_coord(lat, lon, h):
    """Convert coords from geodesic to cartesian."""
    a = 6378137.0
    rf = 298.257223563
    lat_rad = radians(lat)
    lon_rad = radians(lon)
    N = sqrt(a / (1 - (1 - (1 - 1 / rf) ** 2) * (sin(lat_rad)) ** 2))
    X = (N + h) * cos(lat_rad) * cos(lon_rad)
    Y = (N + h) * cos(lat_rad) * sin(lon_rad)
    Z = ((1 - 1 / rf) ** 2 * N + h) * sin(lat_rad)
    return X, Y, Z


def compute_dist(p_1, p_2):
    """Compute cartesian distance between points."""
    return sqrt((p_2[0] - p_1[0])**2 + (p_2[1] - p_1[1])**2 +
                (p_2[2] - p_1[2])**2)


async def determine_contact(rec, ref: Ref, type='parent'):
    """Determine the parent of missiles, rockets, and bombs."""
    if type not in ['parent', 'impacted']:
        raise ValueError("Type must be impacted or parent!")

    LOG.debug(f"Determing {type} for object id: %s -- %s-%s...", rec.id,
              rec.Name, rec.Type)
    offset_min = rec.last_seen - 2.5

    if type == "parent":
        accpt_colors = ['Blue', 'Red'
                        ] if rec.Color == 'Violet' else [rec.Color]

        # query_filter = (
        #     ~(Object.type.startswith('Decoy'))
        #     & ~(Object.c.type.startswith('Misc'))
        #     & ~(Object.c.type.startswith('Projectile'))
        #     & ~(Object.c.type.startswith('Weapon'))
        #     &
        #     ~(Object.c.type.startswith("Ground+Light+Human+Air+Parachutist")))
        query_filter = " (type not like ('%Decoy%')"\
            " AND type not like ('%Misc%')"\
            " AND type not like ('%Weapon%')"\
            " AND type not like ('%Projectile%')"\
            " AND type not like ('%Ground+Light+Human+Air+Parachutist%'))"

    elif type == 'impacted':
        accpt_colors = ['Red'] if rec.Color == 'Blue' else ['Red']
        # query_filter = (Object.c.type.startswith('Air+'))
        query_filter = " type like ('%Air+%')"

    else:
        raise NotImplementedError

    color_query = f""" color in ('{"','".join(accpt_colors)}')"""
    id_query = f" id != {rec.id} "
    query = f""" SELECT id FROM object
    WHERE {query_filter} AND {color_query} AND {id_query}
    """

    nearby_objs = await DB.fetch(query)

    closest = []
    for nearby in nearby_objs:
        near = ref.obj_store[nearby[0]]
        if ((near.last_seen <= offset_min
             and not (near.Type.startswith('Ground') and near.alive == 1))
                and (abs(near.alt - rec.alt) < 2000)
                and (abs(near.lat - rec.lat) <= 0.0005)
                and (abs(near.lon - rec.lon) <= 0.0005)):
            continue

        prox = compute_dist(rec.cart_coords, near.cart_coords)
        LOG.debug("Distance to object %s - %s is %s...", near.Name, near.Type,
                  str(prox))
        if not closest or (prox < closest[1]):
            closest = [near.id, prox, near.Name, near.Pilot, near.Type]

    if not closest:
        return None

    if closest[1] > 1000:
        LOG.warning(
            f"Rejecting closest {type} for {rec.id}-{rec.Name}-{rec.Type}: "
            "%s %sm...%d checked!",  closest[4],
            str(closest[1]), len(nearby_objs))

        return None

    return closest


async def line_to_obj(raw_line: bytearray, ref: Ref) -> Optional[ObjectRec]:
    """Parse a textline from tacview into an ObjectRec."""
    # secondary_update = None
    if raw_line[0:1] == b"0":
        return None

    if raw_line[0:1] == b'-':
        rec = ref.obj_store[int(raw_line[1:], 16)]
        rec.alive = 0
        await mark_dead(rec.id)

        if 'Weapon' in rec.Type:
            impacted = await determine_contact(rec, type='impacted', ref=ref)
            if impacted:
                rec.impacted = impacted[0]
                rec.impacted_dist = impacted[1]
                sql = create_impact_stmt()
                vals = (ref.session_id, rec.parent, rec.impacted, rec.id,
                        ref.time_offset, rec.impacted_dist)
                await DB.execute(sql, *vals)
        return rec

    comma = raw_line.find(b',')
    rec_id = int(raw_line[0:comma], 16)
    try:
        rec = ref.obj_store[rec_id]
        rec.update_last_seen(ref.time_offset)
        rec.updates += 1

    except KeyError:
        # Object not yet seen...create new record...
        rec = ObjectRec(id_=rec_id,
                        session_id=ref.session_id,
                        first_seen=ref.time_offset,
                        last_seen=ref.time_offset)
        ref.obj_store[rec_id] = rec

    while True:
        last_comma = comma + 1
        comma = raw_line.find(b',', last_comma)
        if comma == -1:
            break

        chunk = raw_line[last_comma:comma]
        eq_loc = chunk.find(b"=")
        key = chunk[0:eq_loc]
        val = chunk[eq_loc + 1:]

        if key == b"T":
            i = 0
            pipe_pos_end = -1
            while i < COORD_KEY_LEN:
                pipe_pos_start = pipe_pos_end + 1
                pipe_pos_end = chunk[eq_loc + 1:].find(b'|', pipe_pos_start)
                if pipe_pos_start == -1:
                    break

                coord = chunk[eq_loc + 1:][pipe_pos_start:pipe_pos_end]
                if coord != b'':
                    c_key = COORD_KEYS[i]
                    if c_key == "lat":
                        rec.lat = float(coord) + ref.lat
                    elif c_key == "lon":
                        rec.lon = float(coord) + ref.lon
                    else:
                        rec.update_val(c_key, float(coord))
                i += 1
        else:
            rec.update_val(
                key.decode('UTF-8') if key != b'Group' else 'grp', val.decode('UTF-8'))

    rec.compute_velocity(ref.time_since_last)

    if rec.updates == 1 and rec.should_have_parent():
        parent_info = await determine_contact(rec, type='parent', ref=ref)
        if parent_info:
            rec.parent = parent_info[0]
            rec.parent_dist = parent_info[1]

    return rec


@lru_cache()
def create_object_stmt():
    return f"""INSERT into object ({','.join(Object.c.keys())})
        VALUES({','.join(["$"+str(i+1) for i, _ in enumerate(Object.c.keys())])})"""


@lru_cache()
def create_impact_stmt():
    return f"""INSERT into impact ({','.join(Impact.c.keys())})
        VALUES({','.join(["$"+str(i+1) for i, _ in enumerate(Impact.c.keys())])})"""


async def mark_dead(obj_id) -> None:
    """Mark a single record as dead."""
    await DB.execute(f"""
        UPDATE object SET alive = 0 WHERE id = {obj_id};
    """)

    # """
    # WITH src AS (
    #     UPDATE serial_rate
    #     SET rate = 22.53, serial_key = '0002'
    #     WHERE serial_key = '002' AND id = '01'
    #     RETURNING *
    #     )
    # UPDATE serial_table dst
    # SET serial_key = src.serial_key
    # FROM src
    # -- WHERE dst.id = src.id AND dst.serial_key  = '002'
    # WHERE dst.id = '01' AND dst.serial_key  = '002';
    # """


async def create_single(obj):
    """Insert a single newly create record to database."""
    vals = (obj.id, obj.session_id,
            obj.Name,
            obj.Color,
            obj.Country,
            obj.grp,
            obj.Pilot,
            obj.Type,
            obj.alive,
            obj.Coalition,
            obj.first_seen, obj.last_seen, obj.lat, obj.lon, obj.alt, obj.roll,
            obj.pitch, obj.yaw, obj.u_coord, obj.v_coord, obj.heading,
            obj.updates, obj.velocity_kts, obj.impacted, obj.impacted_dist,
            obj.parent, obj.parent_dist)

    sql = create_object_stmt()
    await DB.execute(sql, *vals)
    obj.written = True


class ServerExitException(Exception):
    """Throw this exception when there is a socket read timeout."""


class MaxIterationsException(Exception):
    """Throw this exception when max iters < total_iters."""


class AsyncSocketReader:
    """Read from Tacview socket."""
    def __init__(self, host, port, debug=False):
        self.host = host
        self.port = port
        self.reader: Optional[asyncio.StreamReader] = None
        self.ref = Ref()
        self.writer: Optional[asyncio.StreamWriter] = None
        self.sink = "log/raw_sink.txt"
        self.data = bytearray()
        self.debug = debug
        self.msg = None
        if self.debug:
            open(self.sink, 'w').close()

    async def open_connection(self):
        """
        Initialize the socket connection and write handshake data.
        If connection fails, wait 3 seconds and retry.
        """
        while True:
            try:
                LOG.info(f'Opening connection to {self.host}:{self.port}...')
                self.reader, self.writer = await asyncio.open_connection(
                    self.host, self.port)
                LOG.info('Connection opened...sending handshake...')
                self.writer.write(HANDSHAKE)
                await self.reader.readline()

                LOG.info('Connection opened...creating db and reading refs...')
                while not self.ref.all_refs:
                    obj = await self.read_stream()
                    if obj[0:2] == b"0,":
                        await self.ref.parse_ref_obj(obj)
                        continue
                break
            except ConnectionError:
                LOG.error('Connection attempt failed....retry in 3 sec...')
                await asyncio.sleep(3)

    async def read_stream(self):
        """Read lines from socket stream."""
        data = bytearray(await self.reader.readuntil(b"\n"))
        return data[:-1]

    async def close(self):
        """Close the socket connection and reset ref object."""
        self.writer.close()
        await self.writer.wait_closed()
        self.reader = None
        self.writer = None
        self.ref = Ref()


class BinCopyWriter:
    """Manage efficient insertion of bulk data to postgres."""
    db_event_time: float = 0.0
    event_times: List = []
    insert: BytesIO
    copy_header = struct.pack('>11sii', b'PGCOPY\n\377\r\n\0', 0, 0)
    copy_trailer =  struct.pack('>h', -1)
    cmd = """
            CREATE UNLOGGED TABLE IF NOT EXISTS event_temp
                (LIKE event INCLUDING DEFAULTS);

            COPY public.event_temp FROM STDIN WITH BINARY;

            CREATE INDEX tmp_idx on event_temp (id);

            INSERT INTO event
            SELECT * FROM event_temp;

            INSERT INTO object (
                id, session_id, last_seen, alive, lat, lon, alt, roll, pitch,
                yaw, u_coord, v_coord, heading, velocity_kts, updates
            )
            SELECT id, session_id, last_seen, alive, lat, lon, alt, roll,
                pitch, yaw, u_coord, v_coord, heading, velocity_kts, updates
            FROM (
                SELECT *,
                    row_number() OVER (
                        PARTITION BY id
                        ORDER BY updates DESC) as row_number
                FROM event_temp
            ) evt
            WHERE row_number = 1
            ON CONFLICT (id)
            DO UPDATE SET session_id=EXCLUDED.session_id,
                last_seen=EXCLUDED.last_seen, alive=EXCLUDED.alive,
                lat=EXCLUDED.lat, lon=EXCLUDED.lon, alt=EXCLUDED.alt,
                roll=EXCLUDED.roll, pitch=EXCLUDED.pitch, yaw=EXCLUDED.yaw,
                u_coord=EXCLUDED.u_coord, v_coord=EXCLUDED.v_coord,
                heading=EXCLUDED.heading, velocity_kts=EXCLUDED.velocity_kts,
                updates=EXCLUDED.updates;

            DROP INDEX tmp_idx;

            DROP TABLE event_temp;
        """

    def __init__(self, columns, dsn: str, min_insert_size: int = -1):
        self.dsn = dsn
        self.min_insert_size = min_insert_size
        self.fmt_str: str = ''
        self.ins_vals = None
        self.ncol = len(columns)
        self.build_fmt_string(columns)
        self.create_byte_buffer()
        self.insert_count = 0

    def build_fmt_string(self, columns):
        types = {
            "INTEGER": ('ii', 4),
            "FLOAT": ('id', 8),
            "DOUBLE": ('id', 8),
            "NUMERIC": ('id', 8)
        }

        fmt_str = ['>h']
        self.ins_vals = [0] * ((self.ncol*2)+1)
        self.ins_vals[0] = self.ncol

        i = 1
        for col in columns.values():
            fmt, sz = types[str(col.type)]
            self.ins_vals[i] = sz
            fmt_str.append(fmt)
            i += 2
        self.fmt_str = ''.join(fmt_str)

    def create_byte_buffer(self) -> None:
        self.insert = BytesIO()
        self.insert.write(self.copy_header)
        self.insert_count = 0

    def add_data(self, obj: ObjectRec) -> None:
        """Take an ObjectRec, pack it to bytes, then write to byte buffer."""
        data = (15,
                4, obj.id,
                4, obj.session_id,
                8, obj.last_seen,
                4, obj.alive,
                8, obj.lat,
                8, obj.lon,
                8, obj.alt,
                8, obj.roll,
                8, obj.pitch,
                8, obj.yaw,
                8, obj.u_coord,
                8, obj.v_coord,
                8, obj.heading,
                8, obj.velocity_kts,
                4, obj.updates)

        packed = struct.pack(self.fmt_str, *data)
        self.insert.write(packed)
        self.insert_count += 1

    def insert_data(self) -> None:
        """If data is in buffer, execute binary copy and update."""
        if self.min_insert_size > self.insert_count:
            LOG.debug("Not enough data for insert....")
            return
        LOG.debug(f'Inserting {self.insert_count} records...')
        self.insert.write(self.copy_trailer)
        self.insert.seek(0)
        conn = pg.connect(self.dsn)
        with conn.cursor() as cur:
            cur.copy_expert(self.cmd, self.insert)
        conn.commit()
        conn.close()
        self.insert.close()
        self.create_byte_buffer()

    def cleanup(self) -> None:
        """Shut down and ensure all data is written."""
        self.min_insert_size = -1 # ensure everything gets flushed
        self.insert_data()
        self.db_event_time = sum(self.event_times)


async def consumer(host=HOST,
                   port=PORT,
                   max_iters=None,
                   only_proc=False,
                   loop=None,
                   bulk=False) -> None:
    """Main method to consume stream."""
    LOG.info("Starting consumer with settings: "
             "debug: %s --  iters %s -- bulk-mode: %s", DEBUG, max_iters, bulk)
    global DB
    DB = await asyncpg.connect(PG_URL)
    tasks_complete = int(1)  # I know this is wrong.  It just makes division easier.
    sock = AsyncSocketReader(host, port)
    copy_writer = BinCopyWriter(Event.c, PG_URL, 10)
    await sock.open_connection()
    init_time = time.time()
    last_log = float(0.0)
    line_proc_time = float(0.0)

    while True:
        try:
            obj = await sock.read_stream()
            if obj[0:1] == b"#":
                sock.ref.update_time(obj)
                if not bulk:
                    copy_writer.insert_data()

                runtime = time.time() - init_time
                log_check = runtime - last_log
                if log_check > 5 or obj == b"#0":
                    secs_ahead = sock.ref.time_offset - (
                        (time.time() - init_time))
                    ln_sec = round(tasks_complete / runtime, 2)
                    LOG.info(
                        f"Runtime: {round(runtime, 2)} - Sec ahead: {round(secs_ahead, 2)}..."
                        f"Lines/sec: {ln_sec} - Total: {tasks_complete}")
                    last_log = runtime

            else:
                t1 = time.time()
                obj = await line_to_obj(obj, sock.ref)

                if obj:
                    line_proc_time += (time.time() - t1)
                    if not obj.written:
                        await create_single(obj)

                    copy_writer.add_data(obj)

                tasks_complete += 1

            if max_iters and max_iters <= tasks_complete:
                LOG.info(f"Max iters reached: {max_iters}...returning...")
                raise MaxIterationsException

        except (KeyboardInterrupt, MaxIterationsException,
                ServerExitException, asyncio.IncompleteReadError):
            copy_writer.cleanup()
            await sock.close()
            total_time = time.time() - init_time
            LOG.info('Total iters : %s', str(tasks_complete))
            LOG.info('Total seconds running : %.2f', total_time)
            LOG.info('Pct Event Write Time: %.2f',
                     copy_writer.db_event_time / total_time)
            LOG.info('Pct Line Proc Time: %.2f', line_proc_time / total_time)
            LOG.info('Lines/second: %.4f', tasks_complete / total_time)
            total = {}
            for obj in sock.ref.obj_store.values():
                if obj.should_have_parent() and not obj.parent:
                    try:
                        total[obj.Type] += 1
                    except KeyError:
                        total[obj.Type] = 1
            for key, value in total.items():
                LOG.info(f"total without parent but should {key}: {value}")

            LOG.info('Exiting tacview-client!')
            return

        except Exception as err:
            LOG.error("Unhandled Exception!"
                      "Writing remaining updates to db and exiting!")
            LOG.error(err)
            raise err


def check_results():
    conn = sa.create_engine(PG_URL)
    obj = pd.read_sql(
            """SELECT COUNT(*) objects, COUNT(parent) parents,
            (SELECT COUNT(*) FROM impact) impacts,
            MAX(updates) max_upate, SUM(updates) total_updates,
            (SELECT COUNT(*) events FROM event) as total_events,
            SUM(alive) total_alive
            FROM object""", conn)
    print(obj)

def main(host, port, debug=False, max_iters=None, only_proc=False, bulk=False):
    """Start event loop to consume stream."""
    loop = asyncio.get_event_loop()
    asyncio.run(consumer(host, port, max_iters, only_proc, loop, bulk))
