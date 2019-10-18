"""Tacview client methods."""
import asyncio
from asyncio.log import logging
from datetime import datetime
import sqlite3

from . import db
from . import get_logger
from . import config

DEBUG = False
LOG = get_logger(logging.getLogger(__name__))
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


def parse_line(obj, ref, last_seen):
    """Parse a single line from tacview stream."""
    LOG.debug(obj)
    line = obj.strip()

    if line[0] == '-':
        # If leading dash, object is dead and should be marked alive=False
        return {'id': line.split('-')[1].strip(), 'alive': False}

    split_line = line.split(',')
    obj_id = split_line.pop(0)
    try:
        obj_dict = {k.lower(): v for k, v in [l.split('=', 1) for l in split_line]}
    except ValueError:
        return
    obj_dict['id'] = obj_id
    try:
        coord = obj_dict.pop('t')
        coord = coord.split('|')[0:3]
        for key, val in zip(['long', 'lat', 'alt'], coord):
            if val == '':
                obj_dict[key] = ''
            else:
                obj_dict[key] = float(val) + getattr(ref, key)
    except KeyError:
        LOG.debug("Key: t not in dict keys for line %s", obj)
        return

    if 'id' in obj_dict.keys() and len(list(obj_dict.keys())) == 4:
        # This means that the object is an update entry.
        return obj_dict

    try:
        obj_dict['grp'] = obj_dict.pop('group')
    except KeyError:
        if 'name' in obj_dict.keys():
            obj_dict['grp'] = obj_dict['name'] + '-' + obj_dict['id']

    for val in ['pilot', 'platform']:
        if val not in obj_dict.keys():
            if 'name' in obj_dict.keys():
                obj_dict[val] = obj_dict['name']

    obj_dict['alive'] = True
    obj_dict['lastseen'] = last_seen
    return obj_dict


class Ref:
    """Hold and extract Reference values used as offsets."""

    def __init__(self):
        self.lat = None
        self.long = None
        self.alt = 0
        self.time = None

    def all_set(self):
        """Return true if all ref attributes are set."""
        return self.lat and self.long and self.time

    def parse_ref_obj(self, line):
        """
        Attempt to extract ReferenceLatitude, ReferenceLongitude or ReferenceTime
        from a line object.
        """
        try:
            val = line.split(',')[-1].split('=')
            LOG.debug('Checking for latitude...')
            if val[0] == 'ReferenceLatitude':
                LOG.debug('Ref latitude found...')
                self.lat = float(val[1])
                return
            LOG.debug('Checking for longitude...')
            if val[0] == 'ReferenceLongitude':
                LOG.debug('Ref longitude found...')
                self.long = float(val[1])
                return
            LOG.debug('Checking for ref time...')
            if val[0] == 'ReferenceTime':
                LOG.debug('Ref time found...')
                self.time = datetime.strptime(val[1], REF_TIME_FMT)
                return
        except IndexError:
            pass


class SocketReader:
    """Read from Tacview socket."""
    host = config.HOST
    port = config.PORT
    handshake = HANDSHAKE

    def __init__(self, debug=False):
        self.ref = Ref()
        self.debug = debug
        self.reader = None
        self.writer = None
        self.last_recv = None

    async def open_connection(self):
        """Initialize the socket connection and write handshake data."""
        while True:
            try:
                self.reader, self.writer = await asyncio.open_connection(
                    self.host, self.port)
                LOG.info('Socket connection opened...sending handshake...')
                self.writer.write(self.handshake)
                self.ref = Ref()
                LOG.info('Connection opened successfully...')
                break
            except ConnectionError as err:
                LOG.error(err)
                LOG.error('Socket connection failed....will retry in 5 seconds...')
                await asyncio.sleep(3)

    async def read_stream(self):
        """Read lines from socket stream."""
        data = await self.reader.readline()
        msg = data.decode().strip()
        if msg:
            self.last_recv = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return msg

    async def close(self):
        """Close the socket connection."""
        self.writer.close()
        await self.writer.wait_closed()


async def run_server():
    """Main method to execute stream listener."""
    log = get_logger(logging.getLogger("tacview_client"))
    log.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    objects = []
    last_seen = 0
    conn = db.create_connection(replace_db=True)
    db.create_db(conn)
    sock = SocketReader(debug=DEBUG)
    await sock.open_connection()
    while True:
        try:
            obj = await sock.read_stream()
            if obj == '' or obj[0:2] == '\\' or obj[0] == '#':
                continue

            if not sock.ref.all_set():
                sock.ref.parse_ref_obj(obj)
                continue

            obj_dict = parse_line(obj, sock.ref, last_seen)
            if obj_dict is None:
                continue

            # Check if object id exists already. If so, update location in db.
            if obj_dict['id'] in objects:
                log.debug('Updating object %s...', obj_dict['id'])
                db.update_enemy_field(conn, obj_dict)
            else:
                log.debug("Adding: %s-%s...", obj_dict['id'], obj_dict['type'])
                objects.append(obj_dict['id'])
                try:
                    db.insert_new_rec(conn, obj_dict)
                    db.insert_new_rec(conn, obj_dict,
                                      cols=['id', 'lat', 'long', 'alt', 'alive'],
                                      table='events')
                except sqlite3.Error as err:
                    log.error("Could not insert object into db! %s",
                              obj_dict)
                    log.execption(err)

        except ConnectionError as err:
            log.error('Closing socket due to exception...')
            log.exception(err)
            await sock.close()
            conn.close()
            conn = db.create_connection(replace_db=True)
            db.create_db(conn)
            await sock.open_connection()
