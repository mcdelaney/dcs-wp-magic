"""
Tacview client methods.

Results are parsed into usable format, and then written to a local sqlite
database.
"""
import asyncio
from asyncio.log import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, date
import json
from math import cos, sin, sqrt
from uuid import uuid1
import time

import peewee as pw
from playhouse.shortcuts import model_to_dict

from dcs.common.db import init_db, Object, Event, Session, Publisher
from dcs.common import get_logger
from dcs.common import config


DEBUG = False
PUB_SUB = None
EVENTS = True

LOG = get_logger(logging.getLogger('tacview_client'), False)
LOG.setLevel(logging.DEBUG if DEBUG else logging.INFO)

HANDSHAKE = '\n'.join(["XtraLib.Stream.0",
                       'Tacview.RealTimeTelemetry.0',
                       "tacview_reader",
                       config.PASSWORD,
                       ]) + "\0"
HANDSHAKE = HANDSHAKE.encode('utf-8')
REF_TIME_FMT = '%Y-%m-%dT%H:%M:%SZ'

COORD_KEYS = ['long', 'lat', 'alt', 'roll', 'pitch', 'yaw', 'u_coord',
              'v_coord', 'heading']


@dataclass
class ObjectRec:
    id: str
    first_seen: datetime
    alive: int
    session_id: str
    last_seen: datetime
    updates: int = 1

    name: str = None
    color: str = None
    country: str = None
    grp: str = None
    pilot: str = None
    platform: str = None
    type: str = None

    coalition: str = None
    lat: float = None
    long: float = None
    alt: float = None
    roll: float = None
    pitch: float = None
    yaw: float = None
    u_coord: float = None
    v_coord: float = None
    heading: float = None

    impactor: str = None
    impactor_dist: float = None
    parent: str = None
    parent_dist: float = None


def get_cartesian_coord(lat, long, alt):
    """Convert coords from geodesic to cartesian."""
    x = alt * cos(lat) * sin(long)
    y = alt * sin(lat)
    z = alt * cos(lat) * cos(long)
    return x, y, z


def compute_dist(p_1, p_2):
    """Compute cartesian distance between points."""
    return sqrt((p_2[0]-p_1[0])**2 + (p_2[1]-p_1[1])**2 + (p_2[2]-p_1[2])**2)


async def determine_contact(rec, type='parent'):
    """Determine the parent of missiles, rockets, and bombs."""
    if type not in ['parent', 'impactor']:
        raise ValueError("Type must be impactor or parent!")

    LOG.debug("Determing parent for object id: %s -- %s-%s...",
              rec.id, rec.name, rec.type)
    offset_min = rec.last_seen - timedelta(seconds=1)
    current_point = get_cartesian_coord(rec.lat, rec.long, rec.alt)

    if type == "parent":
        accpt_colors = ['Blue', 'Red'] if rec.color == 'Violet' else [rec.color]
        filter = (~(Object.type.startswith('Decoy')) &
                  ~(Object.type == 'Misc+Shrapnel') &
                  ~(Object.type.startswith('Projectile'))
                  )
    else:
        accpt_colors = ['Red'] if rec.color == 'Blue' else ['Red']
        filter = ((Object.type.startswith('Projectile')) |
                   (Object.type.startswith('Weapon')))

    nearby_objs = (Object.select(Object.id, Object.alt, Object.lat,
                                 Object.long, Object.name, Object.pilot,
                                 Object.type).
                   where((~Object.id == rec.id)
                         & (~Object.type == rec.type)
                         & ((Object.alive == 1) | (Object.last_seen >= offset_min))
                         & (Object.color in accpt_colors)
                         & (Object.alt.between(rec.alt-1000, rec.alt+1000))
                         & (Object.lat.between(rec.lat-0.01, rec.lat+0.01))
                         & (Object.long.between(rec.long-0.01, rec.long+0.01))
                         & filter
                         ))
    init_matches = len(nearby_objs)
    parent = []
    for nearby in nearby_objs:
        near_pt = get_cartesian_coord(nearby.lat, nearby.long, nearby.alt)
        prox = compute_dist(current_point, near_pt)
        LOG.debug("Distance to object %s is %s...", nearby.name, str(prox))
        if not parent or (prox < parent[1]):
            parent = [nearby.id, prox, nearby.name, nearby.pilot, nearby.type]

    if not parent:
        LOG.warning("Zero possible %s matches found for %s %s, but there were %d at first...",
                    type, rec.id, rec.type, init_matches)
        return None

    if parent[1] > 100:
        LOG.warning("Rejecting closest parent for %s-%s-%s: %s %sm...%d checked!",
                    rec.id, rec.name, rec.type, parent[4], str(parent[1]),
                    len(nearby_objs))
        return None

    LOG.debug('%s of %s %s found: %s - %s at %sm...%d considered...',
             type, rec.type, rec.id, parent[4], parent[0], parent[1],
             len(nearby_objs))
    return parent


def serialize_data(data):
    """Serialize an object for export to pubsub, handling timestamps."""
    if isinstance(data, pw.Model):
        data = model_to_dict(data)
    return json.dumps(data, default=json_serial).encode('utf-8')


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


async def line_to_dict(line, ref):
    """Process a line into a dictionary."""
    line = line.split(',')
    if line[0] == "0":
        return
    obj_dict = {'last_seen': ref.time, 'session_id': ref.session_id}

    if line[0][0] == '-':
        LOG.debug("Record %s is now dead...updating...", id)
        obj_dict['alive'] = 0
        obj_dict['id'] = line[0][1:].strip()
        # server.delete(obj_dict['id'])
        return obj_dict

    obj_dict['id'] = line[0]

    for chunk in line[1:]:
        key, val = chunk.split('=', 1)
        obj_dict[key.lower()] = val

    if 'group' in obj_dict.keys():
        obj_dict['grp'] = obj_dict.pop('group')

    if 't' in obj_dict.keys():
        coord = obj_dict.pop('t')
    elif line[0] == '0' and 'AuthenticationKey' in line[1]:
        LOG.info('Ref value found in line: %s...', ','.join(line))
        return
    else:
        LOG.error("No location key in line!")
        LOG.error(line, obj_dict)
        return

    coord = coord.split('|')

    i = 0
    for key in COORD_KEYS:
        if i > len(coord)-1:
            break
        if coord[i] != '':
            obj_dict[key] = float(coord[i])
        i += 1

    if 'lat' in obj_dict.keys():
        obj_dict['lat'] = obj_dict['lat'] + ref.lat

    if 'long' in obj_dict.keys():
        obj_dict['long'] = obj_dict['long'] + ref.long
    return obj_dict


async def process_line(obj_dict, db):
    """Parse a single line from tacview stream."""
    rec = Object.get_or_none(id=obj_dict['id'])
    prev_coord = None
    prev_ts = None

    if rec:
        prev_ts = rec.last_seen
        rec.updates += 1
        prev_coord = get_cartesian_coord(rec.lat, rec.long, rec.alt)
        # Update existing record

        LOG.debug("Record %s found ...will updated...", obj_dict['id'])
        for key, val in obj_dict.items():
        # for k in COORD_KEYS + ['alive', 'last_seen']:
            try:
                setattr(rec, key, val)
            except KeyError:
                pass
        rec.last_seen = obj_dict['last_seen']
        rec.save()
    else:
        # Create new record
        LOG.debug("Record not found...creating....")
        rec = Object.create(**obj_dict, first_seen=obj_dict['last_seen'])

        if any([t in rec.type.lower() for t in ['weapon', 'projectile',
                                                'decoy', 'container',
                                                'parachutist', 'shrapnel']]):
            parent_info = await determine_contact(rec, type='parent')
            if parent_info:
                rec.parent = parent_info[0]
                rec.parent_dist = parent_info[1]
                rec.save()

            if parent_info and 'shrapnel' in rec.type.lower():
                parent = Object.get(id=parent_info[0])
                impactor = await determine_contact(rec, type='impactor')
                if impactor:
                    parent.impactor = impactor[0]
                    parent.impactor_dist = impactor[1]
                    parent.save()

        if PUB_SUB:
            # Only send first update to PUB_SUB.
            PUB_SUB.writer.publish(PUB_SUB.objects, data=serialize_data(rec))

    if not EVENTS:
        return

    true_dist = None
    secs_from_last = None
    prev_coord = False
    velocity = None
    if prev_coord:
        secs_from_last = (rec.last_seen - prev_ts).total_seconds()
        true_dist = compute_dist(get_cartesian_coord(rec.lat, rec.long, rec.alt),
                                 prev_coord)
        velocity =  true_dist / secs_from_last if secs_from_last > 0 else None

    LOG.debug("Creating event row for %s...", rec.id)
    event = Event.create(object=obj_dict['id'],
                         last_seen=rec.last_seen,
                         alt=rec.alt,
                         lat=rec.lat,
                         long=rec.long,
                         alive=rec.alive,
                         yaw=rec.yaw,
                         heading=rec.heading,
                         roll=rec.roll,
                         pitch=rec.pitch,
                         u_coord=rec.u_coord,
                         v_coord=rec.v_coord,
                         velocity_ms=velocity,
                         dist_m=true_dist,
                         session_id=rec.session_id,
                         secs_from_last=secs_from_last,
                         update_num=rec.updates)

    if PUB_SUB:
        PUB_SUB.writer.publish(PUB_SUB.events, data=serialize_data(event))
    LOG.debug("Event row created successfully...")


class Ref:  # pylint: disable=too-many-instance-attributes
    """Hold and extract Reference values used as offsets."""

    def __init__(self):
        self.lat = None
        self.long = None
        self.time = None
        self.title = None
        self.datasource = None
        self.author = None
        self.start_time = None
        self.last_time = 0.0
        self.all_refs = False
        self.session_id = str(uuid1())
        self.written = False

    def update_time(self, offset):
        """Update the refence time attribute with a new offset."""
        offset = float(offset.strip())
        LOG.debug("New time offset: %s...", offset)
        diff = offset - self.last_time
        LOG.debug("Incremening time offset by %s...", diff)
        self.time = self.time + timedelta(seconds=diff)
        sess = Session.select().limit(1)[0]
        sess.time = self.time
        sess.save()
        self.last_time = offset

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

            if val[0] == 'ReferenceLongitude':
                LOG.debug('Ref longitude found...')
                self.long = float(val[1])

            if val[0] == 'DataSource':
                LOG.debug('Ref datasource found...')
                self.datasource = val[1]

            if val[0] == 'Title':
                LOG.debug('Ref Title found...')
                self.title = val[1]

            if val[0] == 'Author':
                LOG.debug('Ref Author found...')
                self.author = val[1]

            if val[0] == 'ReferenceTime':
                LOG.debug('Ref time found...')
                self.time = datetime.strptime(val[1], REF_TIME_FMT)
                self.start_time = datetime.strptime(val[1], REF_TIME_FMT)

            self.all_refs = self.lat and self.long and self.time
            if self.all_refs and not self.written:
                LOG.info("All Refs found...writing session data to db...")
                sess_ser = self.ser()
                Session.create(**sess_ser)
                if PUB_SUB:
                    LOG.info('PubSub activated...pushing Session...')
                    PUB_SUB.writer.publish(PUB_SUB.sessions,
                                           data=serialize_data(sess_ser))
                self.written = True
                LOG.info("Session session data saved...")

        except IndexError:
            pass

    def ser(self):
        """Serialize relevant Session fields for export."""
        return {'session_id': self.session_id,
                'lat': self.lat,
                'long': self.long,
                'title': self.title,
                'datasource': self.datasource,
                'author': self.author,
                'start_time': self.start_time,
                'time': self.time
                }


class ServerExitException(Exception):
    """Throw this exception when there is a socket read timeout."""


class MaxItersException(Exception):
    """Throw this exception when iterations exceeds preset value."""


class SocketReader:
    """Read from Tacview socket."""

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader = None
        self.ref = Ref()
        self.writer = None
        self.sink = "log/raw_sink.txt"
        if DEBUG:
            open(self.sink, 'w').close()

    async def open_connection(self):
        """
        Initialize the socket connection and write handshake data.
        If connection fails, wait 3 seconds and retry.
        """
        while True:
            try:
                LOG.info('Attempting connection at %s:%s...',
                         self.host, self.port)
                self.reader, self.writer = await asyncio.open_connection(
                    self.host, self.port)
                LOG.info('Socket connection opened...sending handshake...')
                self.writer.write(HANDSHAKE)
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
        data = await asyncio.wait_for(self.reader.readline(), timeout=5.0)
        if not data:
            raise ServerExitException("No data in message!")
        msg = data.decode().strip()
        if DEBUG:
            with open(self.sink, 'a+') as fp_:
                fp_.write(msg + '\n')
        return msg

    async def close(self):
        """Close the socket connection and reset ref object."""
        self.writer.close()
        await self.writer.wait_closed()
        self.reader = None
        self.writer = None
        self.ref = Ref()


async def handle_line(obj, ref, db):
    """Wrapper for line processing methods called in thread."""
    obj = await line_to_dict(obj, ref)
    if obj:
        await process_line(obj, db)


async def consumer(host=config.HOST, port=config.PORT, max_iters=None,
                   only_proc=False):
    """Main method to consume stream."""
    LOG.info("Starting consumer with settings: events: %s -- "
             "pubsub: %s -- debug: %s --  iters %s",
             EVENTS, PUB_SUB, DEBUG, max_iters)
    tasks_complete = 1  # I know this is wrong.  It just makes division easier.
    conn = init_db()
    sock = SocketReader(host, port)

    await sock.open_connection()
    tasks = []
    init_time = time.time()
    ref = Session.select().limit(1)[0]
    last_log = 0

    while True:
        try:
            obj = await sock.read_stream()

            if obj[0] == "#":
                sock.ref.update_time(obj[1:])
                runtime = round(time.time() - init_time, 2)
                log_check = runtime - last_log
                if log_check > 5:
                    LOG.info("Running time: %s -- We are %.2f seconds ahead..."
                             "Lines/second: %.2f",
                             runtime, sock.ref.last_time - runtime,
                             tasks_complete/(time.time() - init_time))
                    last_log = runtime

                ref = Session.select().limit(1)[0]
                if tasks:
                    await asyncio.gather(*tasks)
                    tasks = []

            else:
                if only_proc:
                    tasks.append(asyncio.ensure_future(line_to_dict(obj, ref)))
                else:
                    tasks.append(
                        asyncio.ensure_future(handle_line(obj, ref, conn)))
                tasks_complete += 1

            if max_iters and max_iters <= tasks_complete:
                LOG.info("Max iters reached...collecting tasks and exiting...")
                raise MaxItersException
        except (asyncio.TimeoutError, ConnectionError, ConnectionResetError,
                ServerExitException) as err:
            if tasks:
                LOG.info("Gathering remaining tasks...")
                await asyncio.gather(*tasks)
            LOG.exception(err)
            await sock.close()
            conn = init_db()

        except (KeyboardInterrupt, MaxItersException):
            if tasks:
                LOG.info("Gathering remaining tasks...")
                await asyncio.gather(*tasks)

            total_time = time.time() - init_time
            await sock.close()
            LOG.info('Total iters : %s', str(tasks_complete))
            LOG.info('Total seconds running : %.2f', total_time)
            LOG.info('Lines/second: %.4f', tasks_complete/total_time)
            LOG.info('Exiting tacview-client!')
            break


def main(host, port, mode='local', debug=False, events=False, max_iters=None,
          only_proc=False):
    """Start event loop to consume stream."""
    # pylint: disable=global-statement,disable=too-many-arguments
    global DEBUG, EVENTS, PUB_SUB
    DEBUG = debug
    if DEBUG:
        LOG.setLevel(logging.DEBUG)

    EVENTS = events

    if mode == 'remote':
        PUB_SUB = Publisher()

    asyncio.run(consumer(host, port, max_iters, only_proc))
    import sqlite3
    import pandas as pd
    conn = sqlite3.connect("data/dcs.db",
                           detect_types=sqlite3.PARSE_DECLTYPES)
    print(pd.read_sql("select count(*) from event", conn))
    print(pd.read_sql("select count(*), count(parent), COUNT(impactor) from object", conn))
    conn.close()
