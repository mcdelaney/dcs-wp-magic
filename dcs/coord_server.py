#!/bin/python3
import logging
from multiprocessing import Process
import sqlite3

from flask import Flask, Response

from dcs.coords.processor import construct_enemy_set
from dcs.coords.wp_ctrl import lookup_coords, update_coord

logFormatter = logging.Formatter(
    "%(asctime)s [%(name)s] [%(levelname)-5.5s]  %(message)s")
fileHandler = logging.FileHandler("log/app.log", 'w')
fileHandler.setFormatter(logFormatter)


class CoordApp(Flask):
    logger: logging.Logger
    def __init__(self, app_name):
        super().__init__(app_name)
        self.user = "someone_somewhere"
        self.logger.setLevel(level=logging.INFO)
        self.logger.addHandler(fileHandler)
        self.logger.propogate = False
        self.job = None
        self.targets = []

    def add_targets(self, targets):
        for tar in targets:
            self.logger.info("Adding target: %s manifest...", tar)
            self.targets.append(tar)

    def kill_job(self):
        if self.job:
            self.logger.info("Terminating thread...")
            self.job.terminate()
            self.job = None
        else:
            app.logger.info("No thread currently running...")

    def set_user(self, username):
        self.user = username

    def start_job(self, rack, coords):
        self.kill_job()
        self.job = Process(target=update_coord, args=(rack, coords,))
        self.job.start()

    def get_targets(self):
        try:
            conn = self.connect_to_db()
        except sqlite3.Error:
            return "Could Not Connect To Database!"

        resp = ""
        for tar in self.targets:
            req = conn.execute("""SELECT alive, name
                               FROM object WHERE id = ?""", [tar])
            val = req.fetchone()
            status = "alive" if val[0] == 1 else "dead"
            resp += f"{tar}-{val[1]}: {status}\r\n"
        if resp == "":
            return "No Targets Designated!"
        return resp

    def connect_to_db(self):
        return sqlite3.connect("data/dcs.db")


app = CoordApp('coord_server')


@app.route("/stop")
def stop_job():
    try:
        app.kill_job()
    except Exception as e:
        app.logger.error(e)
    return Response(status=200)


@app.route('/enter_coords/<rack>/<coord_string>')
def start_entry(rack, coord_string):
    try:
        coords, target_ids = lookup_coords(coord_string)
        app.add_targets(target_ids)
        app.start_job(rack, coords)
        return Response(status=200)
    except Exception as e:
        app.logger.error(e)
        return Response(status=500)


@app.route('/set_username/<username>')
def username(username):
    app.set_user(username)
    return Response(status=200)


@app.route('/target_status')
def target_status():
    return app.get_targets()


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
