from pprint import pprint
import json
import datetime as dt
import keyboard
from geopy.distance import vincenty
import logging
import time

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

LAST_RUN_CACHE = 'data/last_extract.json'
OUT_PATH = "C:/Users/mcdel/Saved Games/DCS/Scratchpad/coords.txt"

START_UNIT = ["CVN-74", "Stennis"]

PGAW_STATE_URL = "https://pgaw.hoggitworld.com/"
GAW_STATE_URL = "https://dcs.hoggitworld.com/"

EXCLUDED_TYPES = ['Air+FixedWing', 'Ground+Light+Human+Air+Parachutist', '',
                  "Air+Rotorcraft", "Ground+Static+Aerodrome",
                  "Misc+Shrapnel", 'Weapon+Missile', 'Projectile+Shell',
                  'Misc+Containers']

EXCLUDED_PILOTS = ["FARP"]

FRIENDLY_COUNTRIES = ['us', 'fr']
COALITION = "Enemies"

MAX_DIST = 650

CATS = {
    'MOBILE_CP': ["S-300PS 54K6 cp", "SKP-11"],
    'RADAR': [
        "S-300PS 40B6M tr", "S-300PS 40B6MD sr", "S-300PS 64H6E sr",
        "Kub 1S91 str", "snr s-125 tr", "1L13 EWR", "Dog Ear radar",
        "SA-11 Buk SR 9S18M1", "SA-18 Igla-S comm"
    ],
    'SAM': [
        "S-300PS 5P85C ln", "Kub 2P25 ln", "SA-11 Buk LN 9A310M1", 'Tor 9A331',
        "5p73 s-125 ln", "Osa 9A33 ln", "Strela-10M3", "Strela-1 9P31",
        'S_75M_Volhov'
    ],
    "AAA": [
        "ZSU-23-4 Shilka", "2S6 Tunguska", "Ural-375 ZU-23",
        "ZU-23 Emplacement Closed", "SA-18 Igla-S manpad",
        "ZU-23 Closed Insurgent"],
    'ARMOR': ["Ural-375 PBU", "BMP-2", "T-72B", "SAU Msta", "BMP-1", "BMD-1",
              "BTR-80"],
    "INFANTRY": ["Infantry AK", "Land Rover", "Zil-4331"],
}

CAT_ORDER = {'MOBILE_CP': 1,
             'RADAR': 2,
             "SAM": 3,
             'Unknown': 4,
             'AAA': 5,
             'ARMOR': 6,
             'INFANTRY': 7}

CAT_LOOKUP = {}
for k, v in CATS.items():
    for i in v:
        CAT_LOOKUP[i] = k


def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes) / 60 + float(seconds) / (60 * 60)
    if direction == 'E' or direction == 'N':
        dd *= -1
    return dd


# def dd2precise(deg):
#     d = int(deg)
#     md = abs(deg - d) * 60
#     m = int(md)
#     dec = str(round((((md - m) * 60)/60)*100, 3))
#     return [f'{d:02}', f'{m:02}', dec]


def dd2dms(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = round((md - m) * 60, 2)
    return [f'{d:02}', f'{m:02}', f'{sd:05.2f}']


class Enemy:
    """A single enemy unit with specific attributes."""

    def __init__(self, item, start_coords=None, coord_fmt='dms'):
        self.id = item["Id"]
        self.name = item["Pilot"]
        self.platform = item["Platform"]
        self.type = item["Type"]
        self.dist = 999
        self.target_num = 1
        self.start_coords = start_coords
        self.order_val = None

        self.group_name = item['Group'] if item["Group"] != '' else self.name
        if self.group_name == '':
            self.group_name = f"{self.platform}-{self.id}"
        try:
            self.alt = max([1, round((item["LatLongAlt"]["Alt"]))])
        except Exception as e:
            self.alt = 1
        self.lat_raw = item["LatLongAlt"]["Lat"]
        self.lon_raw = item["LatLongAlt"]["Long"]
        self.last_seen = item['LastSeenMinsAgo']

        lat_card = 'S' if self.lat_raw < 0 else 'N'
        lon_card = 'W' if self.lon_raw < 0 else 'E'

        self.lat_precise = [lat_card] + dd2precise(self.lat_raw)
        self.lon_precise = [lon_card] + dd2precise(self.lon_raw)

        self.lat_dd = lat_card + '.' + str(abs(round(self.lat_raw, 6)))
        self.lon_dd = lon_card + '.' + str(abs(round(self.lon_raw, 6)))

        self.lat_dms = [lat_card] + dd2dms(self.lat_raw)
        self.lon_dms = [lon_card] + dd2dms(self.lon_raw)

        try:
            self.cat = CAT_LOOKUP[self.platform]
            self.order_val = CAT_ORDER[self.cat]
        except KeyError:
            self.cat = self.type
            self.order_val = 4

        self.order_id = float(f"{self.order_val}.{self.target_num}")

        if coord_fmt == 'dms':
            self.lat = '.'.join(self.lat_dms)
            self.lon = '.'.join(self.lon_dms)
        elif coord_fmt == 'precise':
            self.lat = '.'.join(self.lat_precise)
            self.lon = '.'.join(self.lon_precise)
        elif coord_fmt == 'dd':
            self.lat = self.lat_dd
            self.lon = self.lon_dd
        else:
            self.lat = 0
            self.lon = 0

        if start_coords:
            try:
                dist = vincenty(start_coords, (self.lat_raw, self.lon_raw))
                self.dist = round(dist.nm)

            except ValueError as e:
                log.error("Coordinates are incorrect: %f %f",
                          self.lat_raw, self.lon_raw)
    def set_target_order(self, target_num):
        self.target_num = target_num
        self.order_id = float(f"{self.order_val}.{self.target_num}")

    def str(self):
        str = f"{self.target_num}) {self.cat}: {self.platform} {self.lat}, "\
              f"{self.lon}, {self.alt}m, {self.dist}nm"
        log.debug(str)
        log.debug('Created enemy %s %d from Stennis in group %s...',
                 self.platform, self.dist, self.group_name)
        return str


class EnemyGroups:
    """Dataset of named enemy groups."""
    def __init__(self):
        self.groups = {}
        self.total = 0

    def add(self, enemy):
        try:
            targets = len(self.groups[enemy.group_name])
            enemy.set_target_order(targets + 1)
            self.groups[enemy.group_name].append(enemy)

        except (KeyError, NameError, TypeError):
            self.groups[enemy.group_name] = [enemy]
        total = len(self.groups[enemy.group_name])
        self.groups[enemy.group_name][total-1].target_num = total
        self.total += 1
        self.sort()

    def names(self):
        return list(self.groups.keys())

    def sort(self):
        for k in list(self.groups.keys()):
            ents = {e.order_id: e for e in self.groups[k]}
            tmp = []
            for i, k in enumerate(sorted(ents.keys())):
                ents[k].set_target_order(i)
                tmp.append(ents[k])
            self.groups[k] = tmp
            # self.groups[k] = [ents[i] for i in sorted(ents.keys())]

    def __len__(self):
        return self.total

    def __iter__(self):
        """Yields tuples of (group_name, enemy_list, min_distance)"""
        for group_name, group in self.groups.items():
            min_dist = min([enemy.dist for enemy in group])
            yield group_name, group, min_dist

    def serialize(self):
        log.debug("Serializing enemy groups...")
        output = {}
        for k, v in self.groups.items():
            min_dist = min([enemy.dist for enemy in v])
            output[min_dist] = [i.__dict__ for i in v]
        output = [output[k] for k in sorted(output.keys())]
        return json.dumps(output)


def construct_enemy_set(enemy_state, result_as_string=True, coord_fmt='dms'):
    """Parse json response from gaw state endpoint into an enemy list"""
    last_recv = enemy_state.pop('last_recv')
    start_coord = None
    start_pilot = 'None'
    for pilot in ["someone_somewhere", "CVN-74", "Stennis"]:
        if start_coord:
            break
        for id, ent in enemy_state.items():
            if ent["Pilot"] == pilot or ent['Group'] == pilot:
                log.info(f"Using {pilot} for start coords...")
                start_coord = (ent['LatLongAlt']['Lat'],
                               ent['LatLongAlt']['Long'])
                start_pilot = pilot
                break

    enemy_groups = EnemyGroups()
    for id, item in enemy_state.items():
        if item['Type'] in EXCLUDED_TYPES:
            continue

        if item["Coalition"] == COALITION:
            continue

        try:
            if item["Pilot"] in EXCLUDED_PILOTS:
                continue
        except KeyError:
            log.error(item)

        try:
            enemy = Enemy(item, start_coord, coord_fmt)
            enemy_groups.add(enemy)
        except Exception as e:
            log.error(item)
            raise e

    enemy_groups.sort()
    with open(LAST_RUN_CACHE, 'w') as fp_:
        fp_.write(enemy_groups.serialize())

    if result_as_string:
        results = {}

        for grp_name, enemy_set, grp_dist in enemy_groups:
            if start_coord and (grp_dist > MAX_DIST):
                log.info("Excluding %s...distance is %d...", grp_name,
                         grp_dist)
                continue

            grp_val = [e.str() for e in enemy_set]
            grp_results.insert(0, f"{grp_name}")
            results[grp_dist] = '\r\n\t'.join(grp_results)

        results = [results[k] for k in sorted(results.keys())]
        results = [f"{i+1}) {r}" for i, r in enumerate(results)]
        results = '\r\n\r\n'.join(results)
        results = f"Start Ref: {start_pilot} "\
                  f"{(round(start_coord[0], 3), round(start_coord[1], 3))}"\
                  f" {last_recv}\r\n\r\n{results}"
        return results.encode('UTF-8')

    return enemies
