#!/bin/python3
import logging
from multiprocessing import Process

from flask import Flask, abort, Response

from dcs.coords.processor import read_coord_sink, construct_enemy_set
from dcs.coords.wp_ctrl import lookup_coords, update_coord

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


@app.route("/coords/<coord_fmt>/<status>")
def as_strings_coords(coord_fmt, status="alive"):
    try:
        if status == "alive":
            only_alive = True
        else:
            only_alive = False
        state = read_coord_sink()
        enemies = construct_enemy_set(state, coord_fmt=coord_fmt,
                                                only_alive=only_alive)
        app.logger.info('Enemeies Collected...')
        return enemies

    except Exception as e:
        app.logger.error(e)
        resp = Response(500)
        resp.set_data('Error Collecting Enemies!')
        return resp


def main():
    app.logger.setLevel(level=logging.INFO)
    app.run(debug=False, threaded=False)


if __name__ == "__main__":
    main()
