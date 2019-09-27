from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import ujson as json
import os
from pathlib import Path
import socket
import time
import sys

DEBUG = False
BULK_MODE = False

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
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
OBJ_SINK_PATH_TMP = Path('data/tacview_sink_tmp.json')
OBJ_SINK_PATH_RAW = Path('data/tacview_sink_raw.txt')
REF_TIME_FMT = '%Y-%m-%dT%H:%M:%SZ'
EXCLUDED_TYPES = ['Ground+Light+Human+Air+Parachutist', '',
                  "Air+Rotorcraft", "Ground+Static+Aerodrome",
                  "Misc+Shrapnel", 'Weapon+Missile', 'Projectile+Shell',
                  'Misc+Container']

def parse_line(obj, ref, last_seen):
    line = obj.strip()
    split_line = line.split(',')
    try:
        obj_dict = {k:v for k, v in [l.split('=', 1) for l in split_line[1:]]}
        try:
            if obj_dict['Type'] in EXCLUDED_TYPES:
                return
        except KeyError:
            pass
        obj_dict['Id'] = split_line[0]
        obj_dict['LastSeen'] = last_seen
        if 'T' not in obj_dict.keys():
            return
        coord = obj_dict['T'].split('|')[0:3]
        coord = [float(c) if c != '' else '' for c in coord]
        obj_dict['LatLongAlt'] = {
            'Lat': coord[1] + ref.lat if coord[1] != '' else '',
            'Long': coord[0] + ref.lon if coord[0] != '' else '',
            'Alt': coord[2]}

        for val in ['Pilot', 'Platform']:
            if val not in obj_dict.keys():
                if 'Name' in obj_dict.keys():
                    obj_dict[val] = obj_dict['Name']

        if 'Group' not in obj_dict.keys():
            if 'Name' in obj_dict.keys():
                obj_dict['Group'] = obj_dict['Name'] + '-' + obj_dict['Id']

        return obj_dict
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        log.error("Error parsing object: %s on line %s" % (obj, str(exc_tb.tb_lineno)))
        for s in split_line:
            log.error(s)
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
        pass


def open_connection():
    """Attempt creation of a socket connection + handshake to Tacview."""
    while True:
        try:
            log.info("Attemping to connect to tacview server...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))
            log.info('Socket connection opened...sending handshake...')
            sock.sendall(HANDSHAKE)
            log.info("Socket connection opened...")
            ref = Ref()
            return sock, ref
        except Exception as e:
            log.error(e)
            log.error('Socket connection failed....will retry in 5 seconds...')
            time.sleep(5)


@dataclass
class Ref:
    lat = None
    lon = None
    time = None

    def all_set(self):
        return (not any([v is None for v in self.__dict__.values()]))


def main():
    open(OBJ_SINK_PATH, 'w').close()  # Clear contents of existing file.
    open(OBJ_SINK_PATH_TMP, 'w').close()  # Clear contents of existing tmp.
    objects = {"last_recv": None}
    msg = ''
    if DEBUG:
        raw_sink = open(OBJ_SINK_PATH_RAW, 'w')
    sock, ref = open_connection()
    while True:
        try:
            data = sock.recv(4056).decode()
            log.debug('Read new messages...')
            objects['last_recv'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            msg += data
            if DEBUG:
                raw_sink.write(data)
            # If no new line at end of msg, keep reading
            if msg[-1] != '\n':
                # log.info('Message does not end with newline...continuing...')
                continue
            # Split on newline to get objects.
            msg_s = msg.split('\n')
            objs = msg_s[:len(msg_s)-1]

            msg = msg_s[-1]
            for obj in objs:
                if obj[-1] == '\\':
                    log.debug('Continuing after forward slash %s' % obj)
                    continue
                if obj[0] == '-':
                    try:
                        obj_id = obj.split('-')[1].strip()
                        log.debug(f'Dropping object {obj_id}')
                        objects.pop(obj_id)
                        continue
                    except Exception as e:
                        log.debug(f'Could not find object key!')
                        continue

                if not ref.lat:
                    log.debug('Checking for ref lat...')
                    ref.lat = parse_ref_obj(obj, "ReferenceLatitude")

                if not ref.lon:
                    log.debug('Checking for ref lon...')
                    ref.lon = parse_ref_obj(obj, "ReferenceLongitude")

                if not ref.time:
                    log.debug('Checking for ref time...')
                    ref.time = parse_ref_obj(obj, "ReferenceTime")
                    if ref.time:
                        last_seen = int((datetime.now() - ref.time).total_seconds()//60)

                if not ref.all_set():
                    log.debug('All ref values not found...continuing...')
                    continue

                if obj[0] == '#':
                    continue

                obj_dict = parse_line(obj, ref, last_seen)
                if obj_dict is None:
                    continue

                if obj_dict['Id'] in objects.keys():
                    log.debug('Updating existing object...')
                    for k, v in obj_dict['LatLongAlt'].items():
                        if v != '':
                            objects[obj_dict['Id']]['LatLongAlt'][k] = v
                else:
                    if 'Name' not in obj_dict.keys():
                        continue
                    log.debug('Adding new object to data...')
                    objects[obj_dict['Id']] = obj_dict

                log.debug("Writing objects to file...")
                try:
                    with open(OBJ_SINK_PATH_TMP, 'w') as obj_sink:
                        obj_sink.write(json.dumps(objects))
                    os.replace(str(OBJ_SINK_PATH_TMP), str(OBJ_SINK_PATH))
                except Exception:
                    try:
                        with open(OBJ_SINK_PATH_TMP, 'w') as obj_sink:
                            obj_sink.write(json.dumps(objects))
                        os.replace(str(OBJ_SINK_PATH_TMP), str(OBJ_SINK_PATH))
                    except Exception as e:
                        raise e
                if BULK_MODE:
                    sock.close()
                    time.sleep(10)
                    sock, ref = open_connection()

        except Exception as e:
            msg = ''
            log.error('Closing socket due to exception...')
            log.error(e)
            sock.close()
            sock, ref = open_connection()


    if DEBUG:
        raw_sink.close()


if __name__=="__main__":
    main()
