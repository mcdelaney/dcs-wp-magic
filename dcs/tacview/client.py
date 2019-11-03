"""
Tacview client methods.

Results are parsed into usable format, and then written to a local sqlite
database.
"""
import asyncio
from asyncio.log import logging
from datetime import datetime, timedelta, date
import math
from uuid import uuid1
import json

import peewee as pw
from playhouse.shortcuts import model_to_dict
from geopy.distance import geodesic
from geopy import distance
from geopy.point import Point


from dcs.common.db import init_db, Object, Event, Session, Publisher, DB
from dcs.common import get_logger
from dcs.common import config


DEBUG = False
EVENTS = True
LOG = get_logger(logging.getLogger('tacview_client'), False)
LOG.setLevel(logging.DEBUG if DEBUG else logging.INFO)

STREAM_PROTOCOL = "XtraLib.Stream.0"
TACVIEW_PROTOCOL = 'Tacview.RealTimeTelemetry.0'
HANDSHAKE_TERMINATOR = "\0"

HANDSHAKE = '\n'.join([STREAM_PROTOCOL,
                       TACVIEW_PROTOCOL,
                       config.CLIENT,
                       config.PASSWORD]) + HANDSHAKE_TERMINATOR
HANDSHAKE = HANDSHAKE.encode('utf-8')
REF_TIME_FMT = '%Y-%m-%dT%H:%M:%SZ'


def determine_parent(rec):
    """Determine the parent of missiles, rockets, and bombs."""
    # LOG.info("Determing parent for object id: %s -- %s-%s...",
    #          rec.id, rec.name, rec.type)
    offset_min = rec.last_seen - timedelta(seconds=2)
    offset_max = rec.last_seen + timedelta(seconds=1)
    current_point = Point(rec.lat, rec.long, rec.alt)

    nearby_objs = (Object.select().
                   where(Object.alive == 1 and
                         Object.id != rec.id and
                         Object.last_seen >= offset_min and
                         Object.last_seen <= offset_max))
    if rec.color != "Violet":
        nearby_objs = nearby_objs.where(Object.color == rec.color)

    if not nearby_objs:
        LOG.warning(f"No nearby objects found for weapon {rec.name}")

    dists = []
    for nearby in nearby_objs:
        if nearby.id == rec.id:
            continue
        near_pt = Point(nearby.lat, nearby.long, nearby.alt)
        prox = distance.distance(current_point, near_pt).m
        dists.append([nearby.id, prox])
        LOG.debug("Distance to object %s is %s...", nearby.name, str(prox))
    dists.sort(key=lambda x: x[1])
    parent = dists[0]
    if parent[1] > 10:
        LOG.warning("Closest parent candidate is %sm...rejecting!",
                    str(parent[1]))
        return
    LOG.info('Parent of %s found: %s at %sm...\n', rec.id, parent[0], parent[1])
    return parent


def serialize_data(data):
    if isinstance(data, pw.Model):
        data = model_to_dict(data)
    return json.dumps(data, default=json_serial).encode('utf-8')


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))


def line_to_dict(line, ref):
    """Process a line into a dictionary."""
    line = line.split(',')
    if line[0][0] == '-':
        LOG.debug("Record %s is now dead...updating...", id)
        obj_dict = {'id': line[0][1:].strip(),
                    'alive': 0,
                    'last_seen': ref.time,
                    'session_id': ref.session_id
                    }
        return obj_dict

    obj_dict = {k.lower(): v for k, v in [l.split('=', 1) for l in line[1:]]}
    obj_dict['id'] = line[0]
    obj_dict['last_seen'] = ref.time
    obj_dict['session_id'] = ref.session_id
    if 'group' in obj_dict.keys():
        obj_dict['grp'] = obj_dict.pop('group')

    try:
        coord = obj_dict.pop('t')
    except KeyError as err:
        LOG.error(line, obj_dict)
        LOG.exception(err)
        raise err

    coord = coord.split('|')

    for i, k in enumerate(config.COORD_KEYS):
        try:
            obj_dict[k] = float(coord[i])
            if k in ['lat', 'long']:
                obj_dict[k] = obj_dict[k] + getattr(ref, k)
        except (ValueError, TypeError, IndexError) as err:
            pass
    return obj_dict


def process_line(obj_dict, pubsub=None):
    """Parse a single line from tacview stream."""

    rec = Object.get_or_none(id=obj_dict['id'])
    prev_coord = None
    prev_ts = None
    if rec:
        prev_ts = rec.last_seen
        prev_coord = [rec.lat, rec.long, rec.alt]
        # Update existing record
        rec.updates = rec.updates + 1
        LOG.debug("Record %s found ...will updated...", obj_dict['id'])
        for k in config.COORD_KEYS + ['alive', 'last_seen']:
            try:
                setattr(rec, k, obj_dict[k])
            except KeyError:
                pass
        rec.last_seen = obj_dict['last_seen']
        rec.save()
    else:
        # Create new record
        LOG.debug("Record not found...creating....")
        rec = Object.create(**obj_dict, first_seen=obj_dict['last_seen'])
        if any([t in rec.type.lower() for t in ['weapon', 'projectile', 'shrapnel']]):
            parent_info = determine_parent(rec)
            if parent_info:
                rec.parent = parent_info[0]
                rec.parent_dist = parent_info[1]
                rec.save()

        if DEBUG:
            rec.debug = obj_dict
            rec.save()

        if pubsub:
            # Only send first update to pubsub.
            pubsub.writer.publish(pubsub.objects, data=serialize_data(rec))

    if EVENTS:
        true_dist = None
        secs_from_last = None
        velocity = None
        if prev_coord:
            secs_from_last = (rec.last_seen - prev_ts).total_seconds()
            true_dist = geodesic((rec.lat, rec.long),
                                 (prev_coord[0], prev_coord[1])).meters

            if 'alt' in obj_dict.keys():
                h_dist = rec.alt - prev_coord[2]
                true_dist = math.sqrt(true_dist**2 + h_dist**2)

            if secs_from_last > 0:
                velocity = true_dist/secs_from_last

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

        event.save()
        if pubsub:
            pubsub_rec = model_to_dict(event)
            obj_id = pubsub_rec.pop('object')
            pubsub_rec['object'] = obj_id['id']
            pubsub.writer.publish(pubsub.events,
                                  data=serialize_data(pubsub_rec))
        LOG.debug("Event row created successfully...")


class Ref:
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
                'start_time': self.start_time
                }


class ServerExitException(Exception):
    """Throw this exception when there is a socket read timeout."""
    pass


class SocketReader:
    """Read from Tacview socket."""
    handshake = HANDSHAKE

    def __init__(self, host, port, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        self.reader = None
        self.writer = None
        self.last_recv = None
        self.sink = "log/raw_sink.txt"
        if debug:
            open(self.sink, 'w').close()

    async def open_connection(self):
        """Initialize the socket connection and write handshake data."""
        while True:
            try:
                LOG.info(f'Attempting connection at {self.host}:{self.port}...')
                self.reader, self.writer = await asyncio.open_connection(
                    self.host, self.port)
                LOG.info('Socket connection opened...sending handshake...')
                self.writer.write(self.handshake)
                await self.reader.readline()
                LOG.info('Connection opened successfully...')
                break
            except ConnectionError:
                LOG.error('Connection attempt failed....will retry in 3 sec...')
                await asyncio.sleep(3)

    async def read_stream(self):
        """Read lines from socket stream."""
        data = await asyncio.wait_for(self.reader.readline(), timeout=5.0)
        msg = data.decode().strip()
        if self.debug:
            with open(self.sink, 'a+') as fp_:
                fp_.write(msg + '\n')
        return msg

    async def close(self):
        """Close the socket connection."""
        self.writer.close()
        await self.writer.wait_closed()


async def consumer(host=config.HOST, port=config.PORT, mode='local'):
    """Main method to consume stream."""
    conn = init_db()
    if mode == "remote":
        pubsub = Publisher()
    else:
        pubsub = None
    sock = SocketReader(host, port, DEBUG)
    await sock.open_connection()
    ref = Ref()
    iter_counter = 0
    while True:
        try:
            obj = await sock.read_stream()
            try:
                if obj == '' or obj[0:2] == '\\':
                    continue
            except IndexError:
                pass

            try:
                if obj[0:2] == "0," or not ref.all_refs:
                    ref.parse_ref_obj(obj)

                    if ref.all_refs and not ref.written:
                        LOG.info("Writing session data to db...")
                        sess_ser = ref.ser()
                        Session.create(**sess_ser)
                        if pubsub:
                            pubsub.writer.publish(pubsub.sessions,
                                                  data=serialize_data(sess_ser))
                        ref.written = True
                        LOG.info("Session session data saved...")
                    continue
            except IndexError:
                pass

            if obj[0] == "#":
                ref.update_time(obj[1:])
                continue

            obj_dict = line_to_dict(obj, ref)
            process_line(obj_dict, pubsub)
            iter_counter += 1
        except (asyncio.TimeoutError, ConnectionError) as err:
            LOG.error('Closing socket due to exception...')
            LOG.exception(err)
            await sock.close()
            conn.close()
            init_db()
            await sock.open_connection()


def main(host, port, mode='local'):
    """Start event loop to consume stream."""
    asyncio.run(consumer(host, port, mode))
