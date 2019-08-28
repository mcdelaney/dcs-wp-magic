#!/bin/python3
import datetime as dt
import requests as r
from flask import Flask

from dcs import core

app = Flask(__name__)


def request_gaw_data(url):
    resp = r.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data


@app.route("/")
def all_enemies():
    state = request_gaw_data(core.PGAW_STATE_URL)
    enemies = core.construct_enemy_set(state, result_as_string=False)
    return get_enemies().serialize()


@app.route("/pgaw")
def as_strings_pgaw():
    state = request_gaw_data(core.PGAW_STATE_URL)
    enemies = core.construct_enemy_set(state)
    with open(core.PGAW_PATH, 'wb') as fp:
        fp.write(enemies)
    return "ok"


@app.route("/gaw")
def as_strings_gaw():
    state = request_gaw_data(core.GAW_STATE_URL)
    enemies = core.construct_enemy_set(state)
    with open(core.GAW_PATH, 'wb') as fp:
        fp.write(enemies)
    return "ok"


if __name__ == "__main__":
    app.run(debug=False, threaded=True)
