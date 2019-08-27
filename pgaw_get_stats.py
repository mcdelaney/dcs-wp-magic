#!/bin/python3
import datetime as dt
from pprint import pprint
import requests as r
import flask
import json
from flask import Flask

app = Flask(__name__)
KEY = "243bd8b1-3198-4c0b-817a-fadb40decf23"
STATUS_URL = "https://status.hoggitworld.com/" + KEY
STATE_URL = "https://state.hoggitworld.com/" + KEY
ENEMY_COALITION = "Allies"

LAST_REQ = None
LAST_RESPONSE = None


CATS = {
    'MOBILE_CP': [
        "S-300PS 54K6 cp",
        "SKP-11"
    ],
    'RADAR': [
        "S-300PS 40B6M tr",
        "S-300PS 40B6MD sr",
        "Kub 1S91 str",
        "1L13 EWR",
        "Dog Ear radar"
    ],
    'SAM': [
        "S-300PS 5P85C ln",
        "Kub 2P25 ln",
        "5p73 s-125 ln",
        "snr s-125 tr"
        "Osa 9A33 ln",
        "Strela-10M3",
        "Strela-1 9P31"
    ],
    'ARMOR': [
        "Ural-375 PBU",
        "BMP-2",
        "T-72B"
        "SAU Msta",
        "SA-18 Igla-S manpad"
        "ZSU-23-4 Shilka",
        "2S6 Tunguska",
        "Ural-375 ZU-23",
        "ZU-23 Emplacement Closed"
    ],
    "INFANTRY": [
        "Infantry AK"
    ]
}

CAT_LOOKUP = {}
for k, v in CATS.items():
    for i in v:
        CAT_LOOKUP[i] = k


def enemy_to_string(enemy_set):
    enemy_out = []
    for k, v in enemy_set.items():
        str_base = k + '\r\n'
        for elem in v:
            unit = elem['cat'] + ' ' + elem['name'] + ': '
            lat = '.'.join(elem['lat_dms'])
            lon = '.'.join(elem['lon_dms'])
            unit_str = "\t" + unit + '  '.join([lat, lon, elem['alt'] + 'm']) + "\r\n"
            str_base += unit_str
        enemy_out.append(str_base)
    return '\r\n'.join(enemy_out)


def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60);
    if direction == 'E' or direction == 'N':
        dd *= -1
    return dd;

def dd2dms(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = round((md - m) * 60,2)
    return [f'{d:02}', f'{m:02}', f'{sd:05.2f}']


class Enemy:
    """A single enemy unit with specific attributes."""
    def __init__(self, item):
        self.id = item["id"]
        self.name = item["Name"]
        try:
            self.group_name = item['GroupName']
        except KeyError:
            self.group_name = self.name + '-' + str(item['id'])
        self.type = item["Type"]
        try:
            self.unit_name = item["UnitName"]
        except KeyError:
            self.unit_name = None
        self.alt = str(round(item["LatLongAlt"]["Alt"])) + 'm'
        self.lat_raw = item["LatLongAlt"]["Lat"]
        self.lon_raw = item["LatLongAlt"]["Long"]

        lat_card = 'S' if self.lat_raw < 0 else 'N'
        lon_card = 'W' if self.lon_raw < 0 else 'E'

        self.lat_dd = lat_card + str(abs(round(self.lat_raw, 3)))
        self.lon_dd = lon_card + str(abs(round(self.lon_raw, 3)))

        self.lat_dms = [lat_card] + dd2dms(self.lat_raw)
        self.lon_dms = [lon_card] + dd2dms(self.lon_raw)

        try:
            self.cat = CAT_LOOKUP[self.name]
        except KeyError:
            self.cat = "Unknown"

        unit = self.cat + ': ' + self.name + ': '
        lat = '.'.join(self.lat_dms)
        lon = '.'.join(self.lon_dms)
        self.result_string = f"\t{unit} {lat} {lon} {self.alt}\r\n"


class EnemyGroups:
    """Dataset of named enemy groups."""
    def __init__(self):
        self.groups = {}
        self.total = 0

    def add(self, enemy):
        try:
            self.groups[enemy.group_name].append(enemy)
        except KeyError:
            self.groups[enemy.group_name] = [enemy]
        self.total += 1

    def names(self):
        return list(self.groups.keys())

    def __len__(self):
        return self.total

    def __iter__(self):
        for group_name, group in self.groups.items():
            yield group_name, group

    def serialize(self):
        return json.dumps({k:[i.__dict__ for i in v]
                           for k, v in self.groups.items()})


def request_gaw_data(url):
    global LAST_RESPONSE
    global LAST_REQ
    if LAST_RESPONSE and (dt.datetime.now() - LAST_REQ).total_seconds() < 30:
        pprint("Using cached value")
        return LAST_RESPONSE
    resp = r.get(url)
    if resp.status_code != 200:
        raise ValueError("Respose is not 200!")
    data = resp.json()
    LAST_RESPONSE = data
    LAST_REQ = dt.datetime.now()
    return data


def get_enemies():
    print('Making request..')
    state = request_gaw_data(STATE_URL)
    enemies = EnemyGroups()
    for item in state['objects']:
        if item["Coalition"] != ENEMY_COALITION:
            continue
        if item["Flags"]["Human"] == True:
            pprint(item)
        if item['Type']['level1'] == 2:
            enemy = Enemy(item)
            enemies.add(enemy)
    return enemies


@app.route("/")
def all_enemies():
    return get_enemies().serialize()


@app.route("/as_strings")
def as_strings():
    results = []
    enemies = get_enemies()
    for k, v in enemies:
        group_string = k + '\r\n'
        for elem in v:
            group_string += elem.result_string
        results.append(group_string)
    return '\r\n'.join(results)



if __name__=="__main__":
    app.run(debug=True)
