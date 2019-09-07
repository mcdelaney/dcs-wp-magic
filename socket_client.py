import sys
import socket
from pprint import pprint
from pathlib import Path
import datetime as dt
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


KEEP_KEYS = ['Pilot', 'Name', 'Type', 'Country', 'Coalition', 'Group',
             'LatLongAlt', 'Id', 'Platform', 'LastSeenMinsAgo']
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


def parse_line(line, ref_lat, ref_lon, ref_time):
    try:
        line = line.strip()
        if line[0] == "#":
            log.debug("Line starts with #. Should be frame offset...skipping...")
        split_line = line.split(',')
        obj_dict = {k:v for k, v in [l.split('=') for l in split_line[1:]]}
        coord = obj_dict['T'].split('|')[0:3]
        obj_dict['LatLongAlt'] = {'Lat': float(coord[0]) + ref_lat,
                                  'Long': float(coord[1]) + ref_lon,
                                  'Alt': float(coord[2])}
        obj_dict['Id'] = split_line[0]


        if 'Pilot' not in list(obj_dict.keys()):
            obj_dict['Pilot'] = obj_dict["Name"]
        if 'Platform' not in list(obj_dict.keys()):
            obj_dict['Platform'] = obj_dict["Name"]

        for k in list(obj_dict.keys()):
            if k not in KEEP_KEYS:
                obj_dict.pop(k)

        if len(obj_dict.keys()) < len(KEEP_KEYS):
            return None
        return obj_dict
    except (KeyError, ValueError):
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
    except IndexError:
        return None


if __name__=='__main__':
    open(OBJ_SINK_PATH, 'w').close()
    con = False
    while not con:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))
            log.info('Socket connection opened...')
            con = True
        except:
            log.info('Socket connection failed....will retry')
            time.sleep(5)

    objects = {}
    ref_lat = None
    ref_lon = None
    ref_time = None
    msg = ''
    # raw_sink = open(OBJ_SINK_PATH_RAW, 'w')
    try:
        print('sending handshake')
        sock.sendall(HANDSHAKE)
        result = ''
        i = 0

        while True:
            data = sock.recv(5024).decode()
            msg += data
            # raw_sink.write(data)
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

                line = obj.strip()
                split_line = line.split(',')
                obj_id = split_line[0]
                try:
                    obj_dict = {k:v for k, v in [l.split('=') for l in split_line[1:]]}
                    obj_dict['LastSeenMinsAgo'] = last_seen
                    if 'T' not in obj_dict.keys():
                        continue
                    coord = obj_dict['T'].split('|')[0:3]
                    coord = [float(c) if c != '' else '' for c in coord]
                    obj_dict['LatLongAlt'] = {
                        'Lat': coord[0] + ref_lat if coord[0] != '' else '',
                        'Long': coord[1] + ref_lon if coord[1] != '' else '',
                        'Alt': coord[2]}
                except Exception as e:
                    print([e, obj])
                    continue

                if obj_id in objects.keys():
                    log.debug('Updating existing object...')
                    for k, v in obj_dict['LatLongAlt'].items():
                        if v != '':
                            objects[obj_id]['LatLongAlt'][k] = v
                    continue
                try:
                    obj_dict['Id'] = split_line[0]
                    if 'Pilot' not in list(obj_dict.keys()):
                        obj_dict['Pilot'] = obj_dict["Name"]
                    if 'Platform' not in list(obj_dict.keys()):
                        obj_dict['Platform'] = obj_dict["Name"]
                except KeyError:
                    continue
                for k in list(obj_dict.keys()):
                    if k not in KEEP_KEYS:
                        obj_dict.pop(k)

                if len(obj_dict.keys()) < len(KEEP_KEYS):
                    continue

                objects[obj_dict['Id']] = obj_dict
                with open(OBJ_SINK_PATH, 'w') as obj_sink:
                    obj_sink.write(json.dumps(objects))
    finally:
        sys.stderr('closing socket')
        raw_sink.close()
