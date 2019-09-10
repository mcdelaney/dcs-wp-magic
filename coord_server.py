#!/bin/python3
import datetime as dt
import logging
import json
import subprocess
from flask import Flask
import socket
import requests as r

from dcs import core, wp_ctrl
import os


app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def send_socket_request():
    HOST = '127.0.0.1'
    PORT = 8888
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    val = "hello".encode('UTF-8')
    sock.sendall(val)
    return


def request_coord_data():
    with open('C:/Users/mcdel/dcs-wb-magic/data/tacview_sink.json', 'r') as fp_:
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
        send_socket_request()
    except Exception as e:
        print(e)
        return 'error'
    return 'ok'


def main():
    open(core.OUT_PATH, 'w').close()
    app.run(debug=False, threaded=False)


if __name__ == "__main__":
    main()
