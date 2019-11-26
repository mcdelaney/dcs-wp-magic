#!/bin/python3
import logging
from multiprocessing import Process

from flask import Flask, Response

from dcs.coords.processor import construct_enemy_set
from dcs.coords.wp_ctrl import lookup_coords, update_coord

logFormatter = logging.Formatter(
    "%(asctime)s [%(name)s] [%(levelname)-5.5s]  %(message)s")
fileHandler = logging.FileHandler("log/app.log", 'w')
fileHandler.setFormatter(logFormatter)


class CoordApp(Flask):
    def __init__(self, app_name):
        super().__init__(app_name)
        self.user = "someone_somewhere"
        self.logger.setLevel(level=logging.INFO)
        self.logger.addHandler(fileHandler)
        self.logger.propogate = False
        self.job = None


app = CoordApp('coord_server')


@app.route("/stop")
def stop_job():
    try:
        if app.job:
            app.logger.info("Terminating thread...")
            app.job.terminate()
            app.job = None
        else:
            app.logger.info("No thread currently running...")
    except Exception as e:
        app.logger.error(e)
    return Response(status=200)


@app.route('/enter_coords/<rack>/<coord_string>')
def start_entry(rack, coord_string):
    try:
        stop_job()
        coords = lookup_coords(coord_string)
        app.job = Process(target=update_coord, args=(rack, coords,))
        app.job.start()
        return Response(status=200)
    except Exception:
        return Response(status=500)


@app.route('/set_username/<username>')
def username(username):
    app.user = username
    app.logger.info("New username: %s...", app.user)
    return Response(status=200)


@app.route("/coords/<coord_fmt>")
def as_strings_coords(coord_fmt, pilot=None):
    try:
        app.logger.info("Settings coords from user: %s...", app.user)
        enemies = construct_enemy_set(app.user, coord_fmt=coord_fmt)
        app.logger.info('Enemeies Collected...')
        return enemies
    except Exception as e:
        app.logger.error(e)
        resp = Response(500)
        resp.set_data('Error Collecting Enemies!')
        return resp


def main(*args):
    app.logger.info("Starting app...")
    app.run(debug=False, threaded=False)


if __name__ == "__main__":
    main()
