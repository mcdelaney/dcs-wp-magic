import sys
import socket
from pprint import pprint
from pathlib import Path
import datetime as dt
import json
import time
import logging
import tempfile

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


STREAM_PROTOCOL = "XtraLib.Stream.0"
TACVIEW_PROTOCOL = 'Tacview.RealTimeTelemetry.0'
HANDSHAKE_TERMINATOR = "\0"
PASSWORD = '0'
CLIENT = 'someone_somewhere'
HANDSHAKE = '\n'.join([STREAM_PROTOCOL,
                       TACVIEW_PROTOCOL,
                       CLIENT,
                       PASSWORD]) + HANDSHAKE_TERMINATOR
HANDSHAKE = HANDSHAKE.encode('utf-8')
HOST = '127.0.0.1'
PORT = 42674
OBJ_SINK_PATH = Path('data/tacview_sink.json')
OBJ_SINK_PATH_RAW = Path('data/tacview_sink_raw.txt')
REF_TIME_FMT = '%Y-%m-%dT%H:%M:%SZ'
COORD_KEYS = ["lat", "long", "alt", "roll", "flat_coord", "agl", "hdg", "ias"]


def parse_line(line, ref_lat, ref_lon, ref_time):
    try:
        line = line.strip()
        if line[0] == "#":
            log.debug("Line starts with #. Should be frame offset...skipping...")
        split_line = line.split(',')
        obj_dict = {k:v for k, v in [l.split('=') for l in split_line[1:]]}
        obj_dict['Id'] = split_line[0]
        coord = obj_dict.pop('T')
        coord = coord.split('|')
        for i, c in enumerate(COORD_KEYS):
            try:
                if i == 0:
                    obj_dict[c] = float(coord[i]) + ref_lat
                elif i == 1:
                    obj_dict[c] = float(coord[i]) + ref_lon
                else:
                    obj_dict[c] = float(coord[i])
            except (IndexError, ValueError, TypeError):
                obj_dict[c] = ''

        if 'Pilot' not in list(obj_dict.keys()):
            obj_dict['Pilot'] = ''

        return obj_dict
    except (KeyError, ValueError, TypeError) as e:
        return


def parse_ref_obj(line, key):
    try:
        val = line.split(',')[-1].split('=')
        if val[0] == key:
            kv = val[1]
            if val[0] in ['ReferenceLatitude', 'ReferenceLongitude']:
                return float(kv)
            else:
                return dt.datetime.strptime(kv, REF_TIME_FMT)
            return val[1]
    except IndexError as e:
        log.error(e)
        return


def open_connection():
    con = False
    while not con:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))
            log.info('Socket connection opened...sending handshake...')
            sock.sendall(HANDSHAKE)
            con = True
        except:
            log.info('Socket connection failed....will retry')
            time.sleep(5)
    return sock


def main():
    open(OBJ_SINK_PATH, 'w').close()
    objects = {}
    ref_lat = None
    ref_lon = None
    ref_time = None
    msg = ''
    raw_sink = open(OBJ_SINK_PATH_RAW, 'w')
    sock = open_connection()
    while True:
        try:
            data = sock.recv(256).decode()
            msg += data
            raw_sink.write(data)
            if msg[-1] != '\n':
                continue
            msg_s = msg.split('\n')
            objs = msg_s[:len(msg_s)-1]
            msg = msg_s[-1]
            for obj in objs:
                if obj[0] == '-':
                    try:
                        obj_id = obj.split('-')[1].strip()
                        log.debug(f'Dropping object {obj_id}')
                        objects.pop(obj_id)
                        continue
                    except KeyError:
                        log.debug(f'Could not find object key {obj_id}!')

                if not ref_lat:
                    log.debug('Checking for ref lat...')
                    ref_lat = parse_ref_obj(obj, "ReferenceLatitude")

                if not ref_lon:
                    log.debug('Checking for ref lon...')
                    ref_lon = parse_ref_obj(obj, "ReferenceLongitude")

                if not ref_time:
                    log.debug('Checking for ref time...')
                    ref_time = parse_ref_obj(obj, "ReferenceTime")

                if not ref_lat or not ref_lon or not ref_time:
                    continue

                if obj[0] == '#' and ref_time:
                    secs = float(obj.split('#')[-1])
                    log.debug(f'Found time offset val...updating ref_time by {secs}...')
                    set_time = ref_time + dt.timedelta(seconds=secs)
                    last_seen = int((dt.datetime.now() - set_time).total_seconds()//60)
                    log.debug(f'Last seen minutes updating to {last_seen}')
                    continue

                try:
                    obj_dict = parse_line(obj, ref_lat, ref_lon, ref_time)
                    if obj_dict['Id'] in objects.keys():
                        log.debug('Updating existing object...')
                        for k, v in obj_dict.items():
                            objects[obj_dict['Id']][k] = v
                    else:
                        log.debug('Adding new object...')
                        objects[obj_dict['Id']] = obj_dict
                except Exception as e:
                    log.error([e, obj, obj_dict])

                obj_json = json.dumps(objects)
                with open(OBJ_SINK_PATH, 'w') as obj_sink:
                    obj_sink.write(obj_json)

        except Exception as e:
            log.error(e)
            sock = open_connection()

    raw_sink.close()


if __name__=="__main__":
    main()
