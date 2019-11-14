#!/bin/python3
import logging
from multiprocessing import Process

from flask import Flask, Response

from dcs.coords.processor import construct_enemy_set
from dcs.coords.wp_ctrl import lookup_coords, update_coord


# class CoordServer:
#
#     def __init__(self, coord_user="someone_somewhere"):
#         self.app = Flask("coord_server")
#         self.logger = self.app.logger
#         self.coord_user = coord_user
#

app = Flask('coord_server')
app.logger.setLevel(level=logging.INFO)
JOB = None
COORD_USER = "someone_somewhere"

@app.route("/stop")
def stop_job():
    global JOB
    try:
        if JOB:
            app.logger.info("Terminating thread...")
            JOB.terminate()
            JOB = None
        else:
            app.logger.info("No thread currently running...")
    except Exception as e:
        app.logger.error(e)
    return Response(status=200)


@app.route('/enter_coords/<rack>/<coord_string>')
def start_entry(rack, coord_string):
    global JOB
    try:
        stop_job()
        coords = lookup_coords(coord_string)
        JOB = Process(target=update_coord, args=(rack, coords,))
        JOB.start()
        return Response(status=200)
    except Exception:
        return Response(status=500)


@app.route('/set_username/<username>')
def username(username, *args):
    try:
        global COORD_USER
        COORD_USER = username
    except Exception:
        pass
    app.logger.info("New username: %s...", COORD_USER)
    return "ok"


@app.route("/coords/<coord_fmt>/<pilot>")
def as_strings_coords(coord_fmt, pilot=None):
    try:
        app.logger.info("Settings coords from user: %s...", COORD_USER)
        enemies = construct_enemy_set(COORD_USER, coord_fmt=coord_fmt)
        app.logger.info('Enemeies Collected...')
        return enemies

    except Exception as e:
        app.logger.error(e)
        resp = Response(500)
        resp.set_data('Error Collecting Enemies!')
        return resp


def main(coord_user=None, *args):
    app.logger.info("Starting app...")
    app.run(debug=False, threaded=False)


if __name__ == "__main__":
    main()
