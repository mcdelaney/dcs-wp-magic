"""
Client methods to consume a stream from Tacview.
Results are parsed into usable format, and then written to a local sqlite
database.
"""
import asyncio
from asyncio.log import logging
from datetime import datetime
import sqlite3
import socket

from dcs import tacview as tac
from dcs import get_logger, db

DEBUG = False


async def run_server():
    """Main method to execute stream listener."""
    log = get_logger(logging.getLogger("tacview_client"))
    log.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    objects = []
    last_seen = 0
    conn = db.create_connection(replace_db=True)
    db.create_db(conn)
    sock = tac.SocketReader(debug=DEBUG)
    await sock.open_connection()
    while True:
        try:
            obj = await sock.read_stream()
            if obj == '' or obj[0:2] == '\\' or obj[0] == '#':
                continue

            if not sock.ref.all_set():
                sock.ref.parse_ref_obj(obj)
                continue

            obj_dict = tac.parse_line(obj, sock.ref, last_seen)
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
                    db.insert_new_rec(conn, obj_dict, cols=['id', 'lat', 'long', 'alt', 'alive'],
                                      table='events')
                except sqlite3.Error as err:
                    log.error("Could not insert object into db! %s",
                              obj_dict)

        except ConnectionError as err:
            log.error('Closing socket due to exception...')
            log.exception(err)
            await sock.close()
            conn.close()
            conn = db.create_connection(replace_db=True)
            db.create_db(conn)
            await sock.open_connection()


def main():
    asyncio.run(run_server())


if __name__=="__main__":
    main()
