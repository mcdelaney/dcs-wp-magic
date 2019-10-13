"""
Client methods to consume a stream from Tacview.
Results are parsed into usable format, and then written to a local sqlite
database.
"""
import asyncio
from asyncio.log import logging
from datetime import datetime
from pathlib import Path
import sys

from dcs import tacview as tac
from dcs import get_logger, db

DEBUG = False
OBJ_SINK_PATH = Path('data/tacview_sink.json')
OBJ_SINK_PATH_RAW = Path('data/tacview_sink_raw.txt')


async def run_server():
    """Main method to execute stream listener."""
    log = get_logger(logging.getLogger("tacview_client"))
    log.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    open(OBJ_SINK_PATH, 'w').close()  # Clear contents of existing file.
    objects = {"last_recv": None}
    conn = db.create_connection()
    db.create_db(conn)
    prev_skipped = []
    sock = tac.SocketReader(debug=DEBUG, raw_sink_path=OBJ_SINK_PATH_RAW)
    await sock.open_connection()
    while True:
        try:
            obj = await sock.read_stream()
            if obj == '':
                continue

            try:
                if obj[-2:] == '\\':
                    log.debug('Continuing after forward slash %s', obj)
                    continue

                if obj[0] == '-':
                    obj_id = obj.split('-')[1].strip()
                    log.debug('Marking object %s as dead...', obj_id)
                    if obj[0] not in prev_skipped:
                        db.update_enemy_field(conn, obj_id, "alive", False)
                    else:
                        log.debug('Element was previously skipped')
                    continue
            except Exception:
                log.debug('Could not find object key for %s!', obj_id)
                continue

            if not sock.ref.all_set():
                if not sock.ref.time:
                    log.debug('Checking for ref time...')
                    sock.ref.time = tac.parse_ref_obj(obj, "ReferenceTime")
                    if sock.ref.time:
                        last_seen = int((datetime.now() - sock.ref.time).total_seconds()//60)

                if not sock.ref.lon:
                    log.debug('Checking for ref lon...')
                    sock.ref.lon = tac.parse_ref_obj(obj, "ReferenceLongitude")

                if not sock.ref.lat:
                    log.debug('Checking for ref lat...')
                    sock.ref.lat = tac.parse_ref_obj(obj, "ReferenceLatitude")
                log.debug('All ref values not found...continuing...')
                continue

            if obj[0] == '#':
                continue

            obj_dict = tac.parse_line(obj, sock.ref, last_seen, prev_skipped)
            if obj_dict is None:
                continue

            if obj_dict['id'] in prev_skipped:
                log.debug("Enemy was previously skipped...not updating...")
                continue

            if obj_dict['id'] in objects.keys():
                log.debug("Object %s in keys...updating existing object...",
                          obj_dict['id'])
                for key, val in obj_dict.items():
                    if key in ['lat', 'long', 'alt']:
                        if val != '':
                            db.update_enemy_field(conn, obj_dict['id'],
                                                  key, val)

            else:
                if 'name' not in obj_dict.keys():
                    continue
                log.debug("Adding object %s-%s...",
                          obj_dict['id'], obj_dict['name'])
                objects[obj_dict['id']] = obj_dict
                try:
                    db.insert_new_rec(conn, obj_dict)
                except Exception as err:
                    log.error("Could not insert object into db! %s",
                              obj_dict)

        except Exception as err:
            log.error('Closing socket due to exception...')
            log.error(err)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            log.error("Error on line %s", (str(exc_tb.tb_lineno)))
            await sock.close()
            db.truncate_enemies(conn)
            await sock.open_connection()


def main():
    asyncio.run(run_server())


if __name__=="__main__":
    main()
