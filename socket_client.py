import sys
import socket
from pprint import pprint
from pathlib import Path
import json


KEEP_KEYS = ['Pilot', 'Name', 'Type', 'Country', 'Coalition', 'Group',
             'LatLongAlt', 'Id', 'Platform']
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


def parse_line(line, ref_lat, ref_lon):
    try:
        split_line = line.split(',')
        obj_id = split_line[0]
        obj_dict = {k:v for k, v in [l.split('=') for l in split_line[1:]]}
        coord = obj_dict['T'].split('|')[0:3]
        obj_dict['LatLongAlt'] = {'Lat': float(coord[0]) + ref_lat,
                                  'Long': float(coord[1]) + ref_lon,
                                  'Alt': float(coord[2])}
        obj_dict['Id'] = obj_id

        if 'Pilot' not in list(obj_dict.keys()):
            obj_dict['Pilot'] = obj_dict["Name"]
        if 'Platform' not in list(obj_dict.keys()):
            obj_dict['Platform'] = obj_dict["Name"]

        for k in list(obj_dict.keys()):
            if k not in KEEP_KEYS:
                obj_dict.pop(k)

        if len(list(obj_dict.keys())) < len(KEEP_KEYS):
            return None
        return obj_id, obj_dict
    except (KeyError, ValueError):
        return


def parse_ref_lat(line):
    try:
        val = line.split(',')[-1].split('=')
        if val[0] == "ReferenceLatitude":
            return float(val[1])
    except IndexError:
        return None


def parse_ref_lon(line):
    try:
        val = line.split(',')[-1].split('=')
        if val[0] == "ReferenceLongitude":
            return float(val[1])
    except IndexError:
        return None


if __name__=='__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    objects = {}
    ref_lat = None
    ref_lon = None
    msg = ''
    raw_sink = open(OBJ_SINK_PATH_RAW, 'w')
    try:
        print('sending handshake')
        sock.sendall(HANDSHAKE)
        result = ''
        i = 0
        while True:
            data = sock.recv(1024)
            msg += data.decode()

            # raw_sink.write(data.decode())

            if msg[-1] != '\n':
                continue
            msg_s = msg.split('\n')
            objs = msg_s[:len(msg_s)-1]
            msg = msg_s[-1]
            for obj in objs:
                if not ref_lat or not ref_lon:
                    ref_lat = parse_ref_lat(obj)
                    ref_lon = parse_ref_lon(obj)
                obj = parse_line(obj, ref_lat, ref_lon)
                if obj:
                    objects[obj[0]] = obj[1]
                    with open(OBJ_SINK_PATH, 'w') as obj_sink:
                        obj_sink.write(json.dumps(objects))
    finally:
        sys.stderr('closing socket')
        raw_sink.close()
