import sys
import socket
from pprint import pprint
from pathlib import Path
from datetime import datetime, timedelta
import json
import time
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

DEBUG = True
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


def parse_line(obj, ref_lat, ref_lon, last_seen):
    line = obj.strip()
    split_line = line.split(',')
    obj_id = split_line[0]
    try:
        obj_dict = {k:v for k, v in [l.split('=') for l in split_line[1:]]}
        obj_dict['Id'] = obj_id
        obj_dict['LastSeenMinsAgo'] = last_seen
        if 'T' not in obj_dict.keys():
            return
        coord = obj_dict['T'].split('|')[0:3]
        coord = [float(c) if c != '' else '' for c in coord]
        obj_dict['LatLongAlt'] = {
            'Lat': coord[1] + ref_lat if coord[1] != '' else '',
            'Long': coord[0] + ref_lon if coord[0] != '' else '',
            'Alt': coord[2]}
        return obj_dict
    except Exception as e:
        log.error(e)


def parse_ref_obj(line, key):
    try:
        val = line.split(',')[-1].split('=')
        if val[0] == key:
            kv = val[1]
            if val[0] in ['ReferenceLatitude', 'ReferenceLongitude']:
                return float(kv)
            else:
                return datetime.strptime(kv, REF_TIME_FMT)
            return val[1]
    except IndexError:
        return None


def open_connection():
    con = False
    while not con:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))
            log.info('Socket connection opened...sending handshake...')
            sock.sendall(HANDSHAKE)
            con = True
        except Exception as e:
            log.error(e)
            log.error('Socket connection failed....will retry')
            time.sleep(5)
    log.info("Socket connection opened...")
    return sock


def main():
    open(OBJ_SINK_PATH, 'w').close()
    objects = {"last_recv": None}
    ref_lat = None
    ref_lon = None
    ref_time = None
    msg = ''
    if DEBUG:
        raw_sink = open(OBJ_SINK_PATH_RAW, 'w')
    sock = open_connection()
    while True:
        try:
            data = sock.recv(1024).decode()
            objects['last_recv'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            msg += data
            if DEBUG:
                raw_sink.write(data)
            # If no new line at end of msg, keep reading
            if msg[-1] != '\n':
                continue
            # Split on newline to get objects.
            msg_s= msg.split('\n')
            objs = msg_s[:len(msg_s)-1]
            msg = msg_s[-1]
            for obj in objs:
                if obj[0] == '-':
                    try:
                        obj_id = obj.split('-')[1].strip()
                        log.debug(f'Dropping object {obj_id}')
                        objects.pop(obj_id)
                        continue
                    except KeyError as e:
                        log.error(e)
                        log.debug(f'Could not find object key {obj_id}!')
                        continue

                if not ref_lat:
                    log.debug('Checking for ref lat...')
                    ref_lat = parse_ref_obj(obj, "ReferenceLatitude")

                if not ref_lon:
                    log.debug('Checking for ref lon...')
                    ref_lon = parse_ref_obj(obj, "ReferenceLongitude")

                if not ref_time:
                    log.debug('Checking for ref time...')
                    ref_time = parse_ref_obj(obj, "ReferenceTime")
                    if ref_time:
                        last_seen = int((datetime.now() - ref_time).total_seconds()//60)

                if not ref_lat or not ref_lon or not ref_time:
                    continue

                if obj[0] == '#' and ref_time:
                    secs = float(obj.split('#')[-1])
                    log.debug(f'Found time offset val...updating ref_time by {secs}...')
                    set_time = ref_time + timedelta(seconds=secs)
                    last_seen = int((datetime.now() - set_time).total_seconds()//60)
                    log.debug(f'Last seen minutes updating to {last_seen}')
                    continue

                obj_dict = parse_line(obj, ref_lat, ref_lon, last_seen)
                if obj_dict is None:
                    continue

                if obj_id in objects.keys():
                    log.debug('Updating existing object...')
                    for k, v in obj_dict['LatLongAlt'].items():
                        if v != '':
                            objects[obj_id]['LatLongAlt'][k] = v
                    continue
                try:
                    if 'Pilot' not in list(obj_dict.keys()):
                        obj_dict['Pilot'] = obj_dict["Name"]
                    if 'Platform' not in list(obj_dict.keys()):
                        obj_dict['Platform'] = obj_dict["Name"]
                except KeyError as e:
                    log.error(e)
                    continue
                for k in list(obj_dict.keys()):
                    if k not in KEEP_KEYS:
                        obj_dict.pop(k)

                if len(obj_dict.keys()) < len(KEEP_KEYS):
                    continue

                try:
                    objects[obj_dict['Id']] = obj_dict
                    with open(OBJ_SINK_PATH, 'w') as obj_sink:
                        obj_sink.write(json.dumps(objects))
                except:
                    continue

        except Exception as e:
            log.error('Closing socket due to exception...')
            log.error(e)
            sock.close()
            sock = open_connection()

    if DEBUG:
        raw_sink.close()


if __name__=="__main__":
    main()
