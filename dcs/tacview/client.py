"""
Tacview client methods.

Results are parsed into usable format, and then written to a local sqlite
database.
"""

import asyncio
from asyncio.log import logging
from datetime import datetime, timedelta
import math

import peewee
from geopy.distance import geodesic

from dcs.common import db
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


def line_to_dict(line, ref):
    """Process a line into a dictionary."""
    line = line.split(',')
    if line[0][0] == '-':
        LOG.debug("Record %s is now dead...updating...", id)
        obj_dict = {'id': line[0][1:].strip(),
                    'alive': 0,
                    'last_seen': ref.time
                    }
        return obj_dict

    obj_dict = {k.lower(): v for k, v in [l.split('=', 1) for l in line[1:]]}
    obj_dict['id'] = line[0]
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


def process_line(obj_dict, ref):
    """Parse a single line from tacview stream."""

    rec = db.Object.get_or_none(id=obj_dict['id'])
    prev_coord = None
    prev_ts = None
    if rec:
        prev_ts = rec.last_seen
        prev_coord = [rec.lat, rec.long, rec.alt]
        # Update existing record
        rec.updates = rec.updates + 1
        LOG.debug("Record %s found ...will updated...", obj_dict['id'])
        for k in config.COORD_KEYS:
            try:
                setattr(rec, k, obj_dict[k])
            except KeyError:
                pass
        rec.last_seen = ref.time
        rec.save()
    else:
        # Create new record
        LOG.debug("Record not found...creating....")
        rec = db.Object.create(**obj_dict, last_seen=ref.time,
                               first_seen=ref.time)
        if DEBUG:
            rec.debug = obj_dict
            rec.save()

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
        event = db.Event.create(object=obj_dict['id'],
                                last_seen=ref.time,
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
                                secs_from_last=secs_from_last,
                                update_num=rec.updates)
        event.save()
        LOG.debug("Event row created successfully...")
    return


class Ref:
    """Hold and extract Reference values used as offsets."""

    def __init__(self):
        self.lat = None
        self.long = None
        self.time = None
        self.last_time = 0.0
        self.all_refs = False

    def update_time(self, offset):
        """Update the refence time attribute with a new offset."""
        offset = float(offset.strip())
        LOG.debug(f"New time offset: {offset}...")
        diff = offset - self.last_time
        LOG.debug(f"Incremening time offset by {diff}...")
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

            if val[0] == 'ReferenceTime':
                LOG.debug('Ref time found...')
                self.time = datetime.strptime(val[1], REF_TIME_FMT)

            self.all_refs = self.lat and self.long and self.time
        except IndexError:
            pass


class SocketReader:
    """Read from Tacview socket."""
    handshake = HANDSHAKE

    def __init__(self, host, port, debug=False):
        self.ref = Ref()
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
                self.reader, self.writer = await asyncio.open_connection(
                    self.host, self.port)
                LOG.info('Socket connection opened...sending handshake...')
                self.writer.write(self.handshake)
                self.ref = Ref()
                LOG.info('Connection opened successfully...')
                break
            except ConnectionError as err:
                LOG.error(err)
                LOG.error('Connection attempt failed....will retry in 3 sec...')
                await asyncio.sleep(3)

    async def read_stream(self):
        """Read lines from socket stream."""
        data = await self.reader.readline()
        msg = data.decode().strip()
        if msg:
            self.last_recv = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.debug:
            with open(self.sink, 'a+') as fp_:
                fp_.write(msg + '\n')

        return msg

    async def close(self):
        """Close the socket connection."""
        self.writer.close()
        await self.writer.wait_closed()


async def consumer():
    """Main method to consume stream."""
    conn = db.init_db()
    sock = SocketReader(config.HOST, config.PORT, DEBUG)
    await sock.open_connection()
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
                if obj[0:2] == "0," or not sock.ref.all_refs:
                    sock.ref.parse_ref_obj(obj)
                    continue
            except IndexError:
                pass

            if obj[0] == "#":
                sock.ref.update_time(obj[1:])
                continue

            obj_dict = line_to_dict(obj, sock.ref)
            process_line(obj_dict, sock.ref)
            iter_counter += 1
        except ConnectionError as err:
            LOG.error('Closing socket due to exception...')
            LOG.exception(err)
            await sock.close()
            conn.close()
            db.init_db()
            await sock.open_connection()


def main():
    """Start event loop to consume stream."""
    asyncio.run(consumer())

#
# if __name__ == '__main__':
#     main()
