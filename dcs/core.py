from pprint import pprint
import json
from geopy.distance import vincenty
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

OUT_PATH = "C:/Users/mcdel/Saved Games/DCS/Scratchpad/coords.txt"

START_UNIT = ["CVN-74", "Stennis"]

# PGAW_KEY = "243bd8b1-3198-4c0b-817a-fadb40decf23"
# PGAW_STATE_URL = f"https://state.hoggitworld.com/{PGAW_KEY}"
PGAW_STATE_URL = "https://pgaw.hoggitworld.com/"

# GAW_KEY = "f67eecc6-4659-44fd-a4fd-8816c993ad0e"
# GAW_STATE_URL = f"https://state.hoggitworld.com/{GAW_KEY}"
GAW_STATE_URL = "https://dcs.hoggitworld.com/"
EXCLUDED_TYPES = ['Air+FixedWing', 'Ground+Light+Human+Air+Parachutist', '',
                  'Sea+Watercraft+AircraftCarrier', "Air+Rotorcraft",
                  "Ground+Static+Aerodrome"]

EXCLUDED_PILOTS = ["FARP"]

FRIENDLY_COUNTRIES = ['us', 'fr']
COALITION = "Enemies"

MAX_DIST = 650

CATS = {
    'MOBILE_CP': ["S-300PS 54K6 cp", "SKP-11"],
    'RADAR': [
        "S-300PS 40B6M tr", "S-300PS 40B6MD sr", "S-300PS 64H6E sr",
        "Kub 1S91 str", "snr s-125 tr", "1L13 EWR", "Dog Ear radar",
        "SA-11 Buk SR 9S18M1"
    ],
    'SAM': [
        "S-300PS 5P85C ln", "Kub 2P25 ln", "SA-11 Buk LN 9A310M1", 'Tor 9A331',
        "5p73 s-125 ln", "Osa 9A33 ln", "Strela-10M3", "Strela-1 9P31"
    ],
    "AAA": [
        "ZSU-23-4 Shilka", "2S6 Tunguska", "Ural-375 ZU-23",
        "ZU-23 Emplacement Closed", "SA-18 Igla-S manpad"
    ],
    'ARMOR': ["Ural-375 PBU", "BMP-2", "T-72B", "SAU Msta", "BMP-1"],
    "INFANTRY": ["Infantry AK"],
}

CAT_LOOKUP = {}
for k, v in CATS.items():
    for i in v:
        CAT_LOOKUP[i] = k


def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes) / 60 + float(seconds) / (60 * 60)
    if direction == 'E' or direction == 'N':
        dd *= -1
    return dd

def dd2precise(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    dec = str(round((((md - m) * 60)/60)*100, 3))
    return [f'{d:02}', f'{m:02}', dec]


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

        self.group_name = item['Group'] if item["Group"] != '' else self.name
        if self.group_name == '':
            self.group_name = f"{self.platform}-{self.id}"

        self.alt = round(item["LatLongAlt"]["Alt"])
        self.lat_raw = item["LatLongAlt"]["Lat"]
        self.lon_raw = item["LatLongAlt"]["Long"]

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
        except KeyError:
            self.cat = "Unknown"

        if coord_fmt == 'dms':
            lat = '.'.join(self.lat_dms)
            lon = '.'.join(self.lon_dms)
        elif coord_fmt == 'precise':
            lat = '.'.join(self.lat_precise)
            lon = '.'.join(self.lon_precise)
        elif coord_fmt == 'dd':
            lat = self.lat_dd
            lon = self.lon_dd
        else:
            lat = 0
            lon = 0

        if start_coords:
            try:
                log.info([start_coords, (self.lat_raw, self.lon_raw)])
                dist = vincenty(start_coords, (self.lat_raw, self.lon_raw))
                self.dist = round(dist.nm)

            except ValueError as e:
                log.error("Coordinates are incorrect: %f %f",
                          self.lat_raw, self.lon_raw)

        self.str = f"{self.cat}: {self.platform} {lat}, {lon}, {self.alt}m, {self.dist}nm"
        log.debug(self.str)
        log.info('Created enemy %s %d from Stennis in group %s...',
                 self.platform, self.dist, self.group_name)


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
        """Yields tuples of (group_name, enemy_list, min_distance)"""
        for group_name, group in self.groups.items():
            min_dist = min([enemy.dist for enemy in group])
            yield group_name, group, min_dist

    def serialize(self):
        return json.dumps(
            {k: [i.__dict__ for i in v]
             for k, v in self.groups.items()})


def construct_enemy_set(enemy_state, result_as_string=True, coord_fmt='dms'):
    """Parse json response from gaw state endpoint into an enemy list"""
    start_coord = None
    start_pilot = 'None'
    for pilot in ["someone_somewhere", "CVN-74", "Stennis"]:
        if start_coord:
            break
        for id, ent in enemy_state.items():
            if ent["Pilot"] == pilot:
                log.info("Using %s for start coords...", pilot)
                start_coord = (ent['LatLongAlt']['Lat'], ent['LatLongAlt']['Long'])
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
        except:
            pprint(item)

        if item["LatLongAlt"]["Alt"] == 0:
            continue

        enemy = Enemy(item, start_coord, coord_fmt)
        enemy_groups.add(enemy)

    if result_as_string:
        results = {}
        for grp_name, enemy_set, grp_dist in enemy_groups:
            if start_coord and (grp_dist > MAX_DIST):
                log.info("Excluding %s...distance is %d...", grp_name,
                         grp_dist)
                continue
            grp_string = f"{grp_name} - {grp_dist}\r\n\t"
            grp_string += '\r\n\t'.join([elem.str for elem in enemy_set])
            results[grp_dist] = grp_string

        results = [results[k] for k in sorted(results.keys())]
        results = '\r\n\r\n'.join(results)
        results = f"Start Coords: {start_pilot} {start_coord}\r\n\r\n{results}".encode('UTF-8')
        return results

    return enemies
