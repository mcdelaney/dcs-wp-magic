import aiofiles
import asyncio
from asyncio.log import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
import ujson as json
import os
import sqlite3
from pathlib import Path
import sys

from . import get_logger
from .config import EXCLUDED_EXPORT

DEBUG = False
log = get_logger(logging.getLogger(__name__))
log.setLevel(logging.DEBUG if DEBUG else logging.INFO)

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
REF_TIME_FMT = '%Y-%m-%dT%H:%M:%SZ'


def parse_line(obj, ref, last_seen, prev_skipped):
    try:
        line = obj.strip()
        split_line = line.split(',')
        id = split_line[0]
        if id in prev_skipped:
            return
        obj_dict = {k.lower():v for k, v in [l.split('=', 1) for l in split_line[1:]]}
        obj_dict['id'] = id
        try:
            if obj_dict['type'] in EXCLUDED_EXPORT or obj_dict["Coalition"] != "Enemies":
                if obj_dict['pilot'] != "someone_somewhere":
                    log.debug("Adding to prev skipped...")
                    prev_skipped.append(id)
                    return
        except KeyError:
            pass
        obj_dict['lastseen'] = last_seen
        try:
            coord = obj_dict.pop('t')
            coord = coord.split('|')[0:3]
            coord = [float(c) if c != '' else '' for c in coord]
        except KeyError:
            log.debug(f"Key: t not in dict keys for line {obj}")
            return

        obj_dict['lat'] = coord[1] + ref.lat if coord[1] != '' else ''
        obj_dict['long'] = coord[0] + ref.lon if coord[0] != '' else ''
        obj_dict['alt'] = coord[2]

        if 'group' in obj_dict.keys():
            obj_dict['grp'] = obj_dict.pop('group')
        elif 'name' in obj_dict.keys():
            obj_dict['grp'] = obj_dict['name'] + '-' + obj_dict['id']

        for val in ['pilot', 'platform']:
            if val not in obj_dict.keys():
                if 'name' in obj_dict.keys():
                    obj_dict[val] = obj_dict['name']
        obj_dict['alive'] = True
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
            log.info(f'Found ref object {key} with value {val[1]}')
            return val[1]
    except IndexError:
        pass



@dataclass
class Ref:
    lat = None
    lon = None
    time = None

    def all_set(self):
        return (self.lat and self.lon and self.time)


class SocketReader:
    host = HOST
    port = PORT
    handshake = HANDSHAKE

    def __init__(self, debug=False, raw_sink_path=None):
        self.ref = Ref()
        self.raw_sink = raw_sink_path
        self.debug = debug
        self.reader = None
        self.writer = None
        self.last_recv = None

    async def open_connection(self):
        if self.debug:
            self.raw_sink = await aiofiles.open(self.raw_sink, 'w')
        while True:
            try:
                self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
                log.info('Socket connection opened...sending handshake...')
                self.writer.write(self.handshake)
                self.ref = Ref()
                break
            except Exception as e:
                log.error(e)
                log.error('Socket connection failed....will retry in 5 seconds...')
                asyncio.sleep(5)

    async def read_stream(self):
        data = await self.reader.readline()
        msg = data.decode().strip()
        if msg:
            self.last_revc = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.debug:
            await self.raw_sink.write(msg + "\n")
        return msg

    async def close(self):
        if self.debug:
            await self.raw_sink.close()
        self.writer.close()
        await self.writer.wait_closed()
