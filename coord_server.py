#!/bin/python3
import ujson as json
from flask import Flask, abort
from multiprocessing import Process

from dcs import core, wp_ctrl

app = Flask('coord_server')
JOB = None


@app.route("/stop")
def stop_job():
    global JOB
    try:
        if JOB:
            app.logger.info("Terminating thread...")
            JOB.terminate()
            JOB = None
    except Exception as e:
        app.logger.error(e)
    return 'ok'


@app.route('/enter_coords/<coord_string>')
def start_entry(coord_string):
    global JOB
    try:
        stop_job()
        coords = wp_ctrl.lookup_coords(coord_string)
        JOB = Process(target=wp_ctrl.update_coord, args=(coords,))
        JOB.start()
        return "ok"
    except Exception:
        return abort(500)


@app.route("/coords/<coord_fmt>")
def as_strings_coords(coord_fmt):
    try:
        state = core.read_coord_sink()
        enemies = core.construct_enemy_set(state, coord_fmt=coord_fmt)
        return enemies
    except Exception as e:
        app.logger.error(e)
        return abort(500)


def main():
    open(core.OUT_PATH, 'w').close()
    app.run(debug=False, threaded=False)


if __name__ == "__main__":
    main()
