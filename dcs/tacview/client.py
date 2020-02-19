"""
Tacview client methods.

Results are parsed into usable format, and then written to a local sqlite
database.
"""
import asyncio
from asyncio.log import logging
from functools import partial
import concurrent.futures
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, date
import json
from math import cos, sin, sqrt
import numpy as np
import threading

from uuid import uuid1
from queue import Queue
import sqlite3
from typing import Optional, Any, Dict, Set, List

from dcs.common.db import init_db, Object, Session, DB, Event
from dcs.common import get_logger
from dcs.common import config


DEBUG = False
LOG = get_logger(logging.getLogger('tacview_client'), False)
LOG.setLevel(logging.DEBUG if DEBUG else logging.INFO)
TIME_SPLITTING_TIME = 0.0

class Ref:  # pylint: disable=too-many-instance-attributes
    """Hold and extract Reference values used as offsets."""
    time: datetime
    def __init__(self):
        self.session_id: Optional[int] = None
        self.lat: Optional[float] = None
        self.lon: Optional[float] = None
        self.title: Optional[str] = None
        self.datasource: Optional[str] = None
        self.author: Optional[str] = None
        self.time: Optional[datetime] = None
        self.start_time: Optional[datetime] = None
        self.last_time: float = 0.0
        self.time_offset: float = 0.0
        self.all_refs: bool = False
        self.session_uuid: str = str(uuid1())
        self.written: bool = False
        self.sess = None
        self.time_since_last: float = 0.0
        self.diff_since_last: float = 0.0
        self.obj_store: Dict = {}
        self.all_refs: bool = False
        self.time_since_last_events: float = 0.0

    def update_time(self, offset):
        """Update the refence time attribute with a new offset."""
        offset = float(offset[1:].strip())
        LOG.debug("New time offset: %s...", offset)
        self.diff_since_last = offset - self.last_time
        self.time_since_last += self.diff_since_last
        self.time_since_last_events += self.diff_since_last
        LOG.debug("Incrementing time offset by %s...", self.diff_since_last)
        self.time = self.time + timedelta(seconds=self.diff_since_last)
        self.time_offset = offset
        self.last_time = offset

    def update_db(self):
        self.time_since_last = 0.0

    def write_events_db(self):
        self.time_since_last_events = 0.0

    def parse_ref_obj(self, line):
        """
        Attempt to extract ReferenceLatitude, ReferenceLongitude or
        ReferenceTime from a line object.
        """
        try:
            val = line.split(',')[-1].split('=')

            if val[0] == 'ReferenceLatitude':
                LOG.debug('Ref latitude found...')
                self.lat = float(val[1])

            elif val[0] == 'ReferenceLongitude':
                LOG.debug('Ref longitude found...')
                self.lon = float(val[1])

            elif val[0] == 'DataSource':
                LOG.debug('Ref datasource found...')
                self.datasource = val[1]

            elif val[0] == 'Title':
                LOG.debug('Ref Title found...')
                self.title = val[1]

            elif val[0] == 'Author':
                LOG.debug('Ref Author found...')
                self.author = val[1]

            elif val[0] == 'ReferenceTime':
                LOG.debug('Ref time found...')
                self.time = datetime.strptime(val[1], config.REF_TIME_FMT)
                self.start_time = datetime.strptime(val[1], config.REF_TIME_FMT)

            self.all_refs = all(f for f in [self.lat and self.lon and self.time])
            if self.all_refs and not self.written:
                LOG.info("All Refs found...writing session data to db...")
                sess_ser = self.ser()
                self.sess = Session.create(**sess_ser)
                self.session_id = self.sess.session_id
                self.written = True
                LOG.info("Session session data saved...")
        except IndexError:
            pass

    def ser(self):
        """Serialize relevant Session fields for export."""
        return {
            'session_uuid': self.session_uuid,
            'lat': self.lat,
            'lon': self.lon,
            'title': self.title,
            'datasource': self.datasource,
            'author': self.author,
            'start_time': self.start_time,
            'time': self.time,
            'time_offset': self.time_offset
        }


@dataclass
class ObjectRec:
    id: int
    first_seen: datetime
    alive: int
    session_id: str
    last_seen: datetime
    name: Optional[str] = None
    color: Optional[str] = None
    country: Optional[str] = None
    grp: Optional[str] = None
    pilot: Optional[str] = None
    platform: Optional[str] = None
    type: Optional[str] = None
    coalition: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    alt: Optional[float] = 1
    roll: Optional[float] = None
    pitch: Optional[float] = None
    yaw: Optional[float] = None
    u_coord: Optional[float] = None
    v_coord: Optional[float] = None
    heading: Optional[float] = None
    impactor: Optional[str] = None
    impactor_dist: Optional[float] = None
    parent: Optional[str] = None
    parent_dist: Optional[float] = None
    updates: int = 1
    velocity_kts: Optional[float] = None

    time_offset: Optional[float] = None
    prev_coords: Optional[List] = None
    secs_since_last_seen: Optional[float] = None
    updated_vals: Optional[Set[str]] = None

    def update_val(self, key: str, value: Any) -> None:
        if key == "group":
            key = "grp"
        if key == "last_seen" and self.last_seen:
            self.secs_since_last_seen =  (value - self.last_seen).total_seconds()

        setattr(self, key, value)
        if not self.updated_vals:
            self.updated_vals = set()
        self.updated_vals.add(key)

    def reset_update_fields(self) -> None:
        self.updated_vals = set()

    def to_dict(self) -> Dict:
        return dict((key, value)
                    for (key, value) in self.__dict__.items()
                    if key not in ['updated_vals', 'prev_coords'])

    def compute_velocity(self, time_since_last_frame: float) -> None:
        """Calculate velocity given the distance from the last point."""
        cart_coords = get_cartesian_coord(self.lat, self.lon, self.alt)
        if self.prev_coords is not None and time_since_last_frame > 0:
            true_dist = compute_dist(cart_coords, self.prev_coords)
            self.velocity_kts = round((true_dist / time_since_last_frame)/1.94384, 4)
            self.updated_vals.add('velocity_kts')

        self.prev_coords = cart_coords


def get_cartesian_coord(lat, lon, alt):
    """Convert coords from geodesic to cartesian."""
    cos_lat = cos(lat)
    x = alt * cos_lat * sin(lon)
    y = alt * sin(lat)
    z = alt * cos_lat * cos(lon)
    resp = np.array([x, y, z])
    return resp


def compute_dist(p_1, p_2):
    """Compute cartesian distance between points."""
    return np.sqrt(np.sum(np.square((p_1 - p_2))))


def determine_contact(rec, type='parent'):
    """Determine the parent of missiles, rockets, and bombs."""
    if type not in ['parent', 'impactor']:
        raise ValueError("Type must be impactor or parent!")

    LOG.info("Determing parent for object id: %s -- %s-%s...", rec.id,
             rec.name, rec.type)
    offset_min = rec.last_seen - timedelta(seconds=1)
    current_point = get_cartesian_coord(rec.lat, rec.lon, rec.alt)

    if type == "parent":
        accpt_colors = ['Blue', 'Red'
                        ] if rec.color == 'Violet' else [rec.color]
        query_filter = (~(Object.type.startswith('Decoy'))
                  & ~(Object.type == 'Misc+Shrapnel')
                  & ~(Object.type.startswith('Projectile')))
    else:
        accpt_colors = ['Red'] if rec.color == 'Blue' else ['Red']
        query_filter = ((Object.type.startswith('Projectile')) |
                  (Object.type.startswith('Weapon')))

    nearby_objs = (Object.select(
        Object.id, Object.alt, Object.lat, Object.lon, Object.name,
        Object.pilot, Object.type).where(
            (~Object.id == rec.id)
            & (~Object.type == rec.type)
            & ((Object.alive == 1) | (Object.last_seen >= offset_min))
            & (Object.color in accpt_colors)
            & (Object.alt.between(rec.alt - 2000, rec.alt + 2000))
            & (Object.lat.between(rec.lat - 0.015, rec.lat + 0.015))
            & (Object.lon.between(rec.lon - 0.015, rec.lon + 0.015))
            & query_filter))
    init_matches = len(nearby_objs)
    parent = []
    for nearby in nearby_objs:
        near_pt = get_cartesian_coord(nearby.lat, nearby.lon, nearby.alt)
        prox = compute_dist(current_point, near_pt)
        LOG.info("Distance to object %s is %s...", nearby.name, str(prox))
        if not parent or (prox < parent[1]):
            parent = [nearby.id, prox, nearby.name, nearby.pilot, nearby.type]

    if not parent:
        LOG.warning(
            "Zero possible %s matches found for %s %s,"
            " but there were %d at first...", type, rec.id, rec.type,
            init_matches)
        return None

    if parent[1] > 250:
        LOG.warning(
            "Rejecting closest parent for %s-%s-%s: "
            "%s %sm...%d checked!", rec.id, rec.name, rec.type, parent[4],
            str(parent[1]), len(nearby_objs))
        return None

    LOG.info('%s of %s %s found: %s - %s at %sm...%d considered...',
             type, rec.type, rec.id, parent[4], parent[0], parent[1],
             len(nearby_objs))
    return parent


def line_to_obj(raw_line: str, ref: Ref) -> Optional[ObjectRec]:
    """Parse a textline from tacview into an ObjectRec."""
    if raw_line[0] == "0":
        return None
    # global TIME_SPLITTING_TIME
    line = raw_line.split(',')

    if line[0][0] == '-':
        rec = ref.obj_store[int(line[0][1:].strip(), 16)]
        rec.update_val('alive', 0)
        return rec

    # t1 = datetime.now()
    rec_id = int(line.pop(0), 16)
    try:
        rec = ref.obj_store[rec_id]
        rec.update_val('updates', rec.updates+1)
        rec.update_val('last_seen', ref.time)
        rec.update_val('time_offset', ref.time_offset)
    except KeyError:
        # Object not yet seen...create new record...
        rec = ObjectRec(id=rec_id,
                        alive=1,
                        session_id=ref.session_id,
                        first_seen=ref.time,
                        last_seen=ref.time,
                        time_offset=ref.time_offset)
        ref.obj_store[rec_id] = rec


    for chunk in line:
        key, val = chunk.split('=', 1)
        if key == "T":
            coord = val.split('|')
            i = 0
            for c_key in config.COORD_KEYS:
                if i > len(coord) - 1:
                    break
                if coord[i] != '':
                    if c_key == "lat":
                        rec.update_val(c_key, float(coord[i]) + ref.lat)
                    elif c_key == "lon":
                        rec.update_val(c_key, float(coord[i]) + ref.lon)
                    else:
                        rec.update_val(c_key, float(coord[i]))
                i += 1
        else:
            rec.update_val(key.lower(), val)
    rec.compute_velocity(ref.time_since_last)
    # TIME_SPLITTING_TIME += (datetime.now() - t1).total_seconds()
    return rec


def search_for_parent_and_impactor(rec):
    if not any([
            t in rec['type'].lower() for t in [
                'weapon', 'projectile', 'decoy', 'container',
                'parachutist', 'shrapnel'
            ]
        ]):
        return

    LOG.info("Looking up parent for record...")
    parent_info = determine_contact(rec, type='parent')
    if parent_info:
        LOG.info("Looking for parent...")
        rec.parent = parent_info[0]
        rec.parent_dist = parent_info[1]
        rec.save()

    if parent_info and 'shrapnel' in rec.type.lower():
        LOG.info("Looking for impactor...")
        impactor = determine_contact(rec, type='impactor')
        if impactor:
            rec.impactor = impactor[0]
            rec.impactor_dist = impactor[1]
            rec.save()


def update_records(que: Queue, counter: float = None) -> Optional[float]:
    """
    Given a list of ObjectRecords, execute create or update operations to
    sync with db.
    """
    if que.empty():
        return counter
    t1 = datetime.now()
    cur = DB.cursor()
    with DB.atomic():
        while not que.empty():
            obj = que.get_nowait()
            if obj == -1:
                break
            try:
                if obj.updated_vals:
                    vals = [None] * len(obj.updated_vals)
                    params = vals.copy()
                    for i, key in enumerate(obj.updated_vals):
                        params[i] = f"{key} = ?"
                        vals[i] = obj.__dict__[key]

                    query = "UPDATE object SET " + " , ".join(params) + f" WHERE id = {obj.id}"
                    cur.execute(query,vals)
                    obj.reset_update_fields()
            except Exception as err:
                LOG.error(query)
                LOG.error(f"Error on rec: {obj.to_dict()}...\n"
                            f"New fields: {obj.updated_vals}...")
                raise err

    counter += (datetime.now()-t1).total_seconds()
    return counter


def insert_records(que: Queue, table, counter: float = None) -> Optional[float]:
    """
    Given a list of Event dicts, execute insert rows.
    """
    if que.empty():
        return counter
    t1 = datetime.now()
    inserts = [None] * que.qsize()
    i = 0
    fields = table._meta.fields.keys()
    qs = ','.join(["?" for _ in range(len(fields))])
    while not que.empty():
        obj = que.get_nowait()
        if obj == -1:
            inserts.pop(-1) # since the last element in inserts is None
            break
        try:
            inserts[i] = tuple(obj[field] for field in fields)
            i += 1
        except Exception as err:
            LOG.error(f"Error on rec: {obj}...")
            raise err

    if inserts:
        try:
            curr = DB.cursor()
            curr.executemany(f"INSERT INTO {table._meta.name} VALUES ({qs})", inserts)
        except (ValueError, sqlite3.OperationalError) as err:
            LOG.error(inserts)
            LOG.error(f"Error writing {len(inserts)} to {table}!")
            raise err

    counter += (datetime.now()-t1).total_seconds()
    return counter


class ServerExitException(Exception):
    """Throw this exception when there is a socket read timeout."""


class MaxIterationsException(Exception):
    """Throw this exception when max iters < total_iters."""


class SocketReader:
    """Read from Tacview socket."""
    def __init__(self, host, port, debug=False):
        self.host = host
        self.port = port
        self.reader = None
        self.ref = Ref()
        self.writer = None
        self.sink = "log/raw_sink.txt"
        self.debug = debug
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
                self.writer.write(config.HANDSHAKE)
                await self.reader.readline()

                LOG.info('Connection opened...creating db and reading refs...')
                while not self.ref.all_refs:
                    obj = await self.read_stream()
                    if obj[0:2] == "0,":
                        self.ref.parse_ref_obj(obj)
                        continue
                break
            except ConnectionError:
                LOG.error('Connection attempt failed....retry in 3 sec...')
                await asyncio.sleep(3)

    async def read_stream(self):
        """Read lines from socket stream."""
        if not self.reader:
            await self.open_connection()
        data = await self.reader.readline()
        # data = await asyncio.wait_for(self.reader.readline(), timeout=5.0)
        if not data:
            raise ServerExitException("No data in message!")
        msg = data.decode()
        if self.debug:
            with open(self.sink, 'a+') as fp_:
                fp_.write(msg)
        return msg.strip()

    async def close(self):
        """Close the socket connection and reset ref object."""
        self.writer.close()
        await self.writer.wait_closed()
        self.reader = None
        self.writer = None
        self.ref = Ref()


def cleanup_obj_queues(update_queue, event_queue, create_queue,
                       db_update_time, db_event_time, db_create_time):
    update_queue.put(-1)
    create_queue.put(-1)
    event_queue.put(-1)
    db_create_time = insert_records(create_queue, Object, db_create_time)
    db_update_time = update_records(update_queue, db_update_time)
    db_event_time = insert_records(event_queue, Event, db_event_time)
    return db_update_time, db_event_time, db_create_time


async def consumer(host=config.HOST,
                   port=config.PORT,
                   max_iters=None,
                   only_proc=False,
                   loop=None) -> None:
    """Main method to consume stream."""
    LOG.info(
        "Starting consumer with settings: "
        "debug: %s --  iters %s", DEBUG, max_iters)
    tasks_complete = 1  # I know this is wrong.  It just makes division easier.
    init_db()
    sock = SocketReader(host, port)
    await sock.open_connection()
    init_time = datetime.now()
    last_log = 0
    update_queue = Queue(maxsize=-1)
    event_queue = Queue(maxsize=-1)
    create_queue = Queue(maxsize=-1)
    db_update_time = 0.0
    db_event_time = 0.0
    db_create_time = 0.0
    line_proc_time = 0.0

    while True:
        try:
            obj = await sock.read_stream()
            if obj[0] == "#":
                sock.ref.update_time(obj)
                db_create_time = insert_records(create_queue, Object, db_create_time)
                db_update_time = update_records(update_queue, db_update_time)
                db_event_time = insert_records(event_queue, Event, db_event_time)

                runtime = ((datetime.now() - init_time).total_seconds())
                log_check = runtime - last_log
                if log_check > 5 or obj=="#0":
                    secs_ahead = sock.ref.time_offset - ((datetime.now() - init_time).total_seconds())
                    ln_sec = tasks_complete / runtime
                    LOG.info(f"Runtime: {round(runtime, 2)} - Sec ahead: {round(secs_ahead, 2)}..."
                             f"Lines/sec: {round(ln_sec, 2)} - Total: {tasks_complete}")
                    last_log = runtime
            else:
                t1 = datetime.now()
                obj = line_to_obj(obj, sock.ref)
                if obj:
                    obj_dict = obj.to_dict()
                    line_proc_time += (datetime.now()-t1).total_seconds()
                    if obj.updates == 1:
                        create_queue.put_nowait(obj_dict)
                    else:
                        update_queue.put_nowait(obj)
                    event_queue.put_nowait(obj_dict)
                # line_proc_time += (datetime.now()-t1).total_seconds()
                tasks_complete += 1

            if max_iters and max_iters <= tasks_complete:
                LOG.info(f"Max iters reached: {max_iters}...returning...")
                raise MaxIterationsException

        except (KeyboardInterrupt, MaxIterationsException):
            db_update_time, db_event_time, db_create_time  = cleanup_obj_queues(
                update_queue, event_queue, create_queue,
                db_update_time, db_event_time, db_create_time)
            total_time = ((datetime.now() - init_time).total_seconds())
            await sock.close()
            LOG.info('Total iters : %s', str(tasks_complete))
            LOG.info('Total seconds running : %.2f', total_time)
            LOG.info('Pct Create Write Time: %.2f', db_create_time / total_time)
            LOG.info('Pct Event Write Time: %.2f', db_event_time / total_time)
            LOG.info('Pct Update Write Time: %.2f', db_update_time / total_time)
            LOG.info('Pct Line Proc Time: %.2f', line_proc_time / total_time)
            LOG.info('Pct Splitting Time: %.2f', TIME_SPLITTING_TIME / total_time)

            LOG.info('Lines/second: %.4f', tasks_complete / total_time)
            LOG.info('Exiting tacview-client!')
            return

        except Exception as err:
            LOG.error("Unhandled Exception!"
                      "Writing remaining updates to db and exiting!")
            cleanup_obj_queues(update_queue, event_queue, create_queue,
                               db_update_time, db_event_time,
                               db_create_time)
            raise err


def main(host,
         port,
         debug=False,
         max_iters=None,
         only_proc=False):
    """Start event loop to consume stream."""
    loop = asyncio.get_event_loop()
    asyncio.run(consumer(host, port, max_iters, only_proc, loop))
    import pandas as pd
    conn = sqlite3.connect("data/dcs.db", detect_types=sqlite3.PARSE_DECLTYPES)
    print(pd.read_sql("SELECT COUNT(*) events FROM event", conn))
    print(pd.read_sql("""SELECT COUNT(*) objects, COUNT(parent), COUNT(impactor),
                            MAX(updates)
                         FROM object""", conn))
    conn.close()
