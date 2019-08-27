#!/bin/python3
import datetime as dt
import requests as r
from flask import Flask

from dcs import core

app = Flask(__name__)

LAST_REQ = None
LAST_RESPONSE = None


def request_gaw_data(url):
    global LAST_RESPONSE
    global LAST_REQ
    if LAST_RESPONSE and (dt.datetime.now() - LAST_REQ).total_seconds() < 30:
        print("Using cached value")
        return LAST_RESPONSE
    resp = r.get(url)
    if resp.status_code != 200:
        raise ValueError("Respose is not 200!")
    data = resp.json()
    LAST_RESPONSE = data
    LAST_REQ = dt.datetime.now()
    return data


@app.route("/")
def all_enemies():
    state = request_gaw_data(core.STATE_URL)
    enemies = core.construct_enemy_set(state, result_as_string=False)
    return get_enemies().serialize()


@app.route("/as_strings")
def as_strings():
    state = request_gaw_data(core.STATE_URL)
    return core.construct_enemy_set(state)


if __name__=="__main__":
    app.run(debug=False)
