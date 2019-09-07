#!/bin/python3
import datetime as dt
import logging
import json

from flask import Flask
import requests as r

from dcs import core

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def request_coord_data():
    with open('data/tacview_sink.json', 'r') as fp_:
        data = json.load(fp_)
    return data


@app.route("/coords/<coord_fmt>")
def as_strings_coords(coord_fmt):
    try:
        state = request_coord_data()
        enemies = core.construct_enemy_set(state, coord_fmt=coord_fmt)
    except Exception as e:
        print(e)
        raise e
    with open(core.OUT_PATH, 'wb') as fp:
        fp.write(enemies)
    return 'ok'

@app.route("/enter/<section>/<target>")
def enter_coords(section, target):
    try:
        log.info(f'Got request for section {section} and target {target}')
        coord = core.get_cached_coords(section, target)
        log.info(coord)
    except Exception as e:
        return 'error'
    return 'ok'


if __name__ == "__main__":
    open(core.OUT_PATH, 'w').close()
    app.run(debug=False, threaded=True)
