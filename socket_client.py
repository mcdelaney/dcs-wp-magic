import sys
import socket
from pprint import pprint
from pathlib import Path
import json


KEEP_KEYS = ['Pilot', 'Name', 'Type', 'Country', 'Coalition', 'Group']
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


def parse_line(line):
    try:
        split_line = line.split(',')
        obj_id = split_line[0]
        obj_dict = {k:v for k, v in [l.split('=') for l in split_line[1:]]}
        obj_dict['LatLongAlt'] = obj_dict['T'].split('|')[0:3]

        for k in list(obj_dict.keys()):
            if k not in KEEP_KEYS:
                obj_dict.pop(k)

        if len(list(obj_dict.keys())) < len(KEEP_KEYS)-1:
            return None
        return obj_id, obj_dict
    except (KeyError, ValueError):
        pprint(line)
        return


if __name__=='__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    objects = {}
    obj_sink_path = Path('data/tacview_sink.json')
    msg = ''
    try:
        print('sending handshake')
        sock.sendall(HANDSHAKE)
        result = ''
        i = 0
        while True:
            data = sock.recv(1024)
            msg += data.decode()
            if msg[-1] != '\n':
                continue
            msg_s = msg.split('\n')
            objs = msg_s[:len(msg_s)-1]
            msg = msg_s[-1]
            for obj in objs:
                obj = parse_line(obj)
                if obj:
                    objects[obj[0]] = obj[1]
                    with open(obj_sink_path, 'w') as obj_sink:
                        obj_sink.write(json.dumps(objects))
    finally:
        sys.stderr('closing socket')
        pprint(objects)
