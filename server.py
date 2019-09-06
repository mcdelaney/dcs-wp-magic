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


def request_gaw_data(url):
    with open('data/tacview_sink.json', 'r') as fp_:
        data = json.load(fp_)
    return data


@app.route("/")
def all_enemies():
    state = request_gaw_data(core.PGAW_STATE_URL)
    enemies = core.construct_enemy_set(state, result_as_string=False)
    out = enemies.serialize()
    return out


@app.route("/pgaw/<coord_fmt>")
def as_strings_pgaw(coord_fmt):
    try:
        state = request_gaw_data(core.PGAW_STATE_URL)
        enemies = core.construct_enemy_set(state, coord_fmt=coord_fmt)
    except Exception as e:
        enemies = "Error"
        print(e)
    with open(core.OUT_PATH, 'wb') as fp:
        fp.write(enemies)
    return enemies


@app.route("/gaw/<coord_fmt>")
def as_strings_gaw(coord_fmt):
    try:
        state = request_gaw_data(core.GAW_STATE_URL)
        enemies = core.construct_enemy_set(state, coord_fmt=coord_fmt)
    except Exception as e:
        enemies = "Error"
        print(e)
    with open(core.OUT_PATH, 'wb') as fp:
        fp.write(enemies)
    return enemies


if __name__ == "__main__":
    app.run(debug=False, threaded=True)
