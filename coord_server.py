#!/bin/python3
import datetime as dt
import logging
import json
import subprocess
from flask import Flask
import socket
import requests as r
import threading
from multiprocessing import Process
import os

from dcs import core, wp_ctrl


app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
JOBS = []


def send_socket_request():
    HOST = '127.0.0.1'
    PORT = 8888
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    val = "hello".encode('UTF-8')
    sock.sendall(val)
    return


def get_coord_data():
    with open('data/tacview_sink.json', 'r') as fp_:
        data = json.load(fp_)
    return data


@app.route("/stop")
def stop_entry():
    log.info('Attempting to kill thread...')
    try:
        log.info("Terminating thread...")
        j = JOBS.pop(0)
        j.terminate()
    except Exception as e:
        log.error(e)
    return 'ok'

@app.route('/start')
def start_entry():
    if JOBS:
        try:
            log.info("Removing job from list...")
            j = JOBS.pop(0)
            j.terminate()
        except Exception as e:
            log.error(e)

    log.info("Starting process and appending to global...")
    t = Process(target=wp_ctrl.update_coord)
    t.start()
    JOBS.append(t)
    return "ok"


@app.route("/coords/<coord_fmt>")
def as_strings_coords(coord_fmt):
    try:
        state = get_coord_data()
        enemies = core.construct_enemy_set(state, coord_fmt=coord_fmt)
    except Exception as e:
        log.error(e)
        raise e
    with open(core.OUT_PATH, 'wb') as fp:
        fp.write(enemies)
    return 'ok'


@app.route("/enter")
def enter_coords():
    try:
        send_socket_request()
    except Exception as e:
        log.error(e)
        return 'error'
    return 'ok'


def main():
    open(core.OUT_PATH, 'w').close()
    app.run(debug=False, threaded=False)


if __name__ == "__main__":
    main()
