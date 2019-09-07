from pprint import pprint
import json
from geopy.distance import vincenty
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

LAST_RUN_CACHE = 'data/last_extract.json'
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
        "5p73 s-125 ln", "Osa 9A33 ln", "Strela-10M3", "Strela-1 9P31",
        'S_75M_Volhov'
    ],
    "AAA": [
        "ZSU-23-4 Shilka", "2S6 Tunguska", "Ural-375 ZU-23",
        "ZU-23 Emplacement Closed", "SA-18 Igla-S manpad",
        "ZU-23 Closed Insurgent"],
    'ARMOR': ["Ural-375 PBU", "BMP-2", "T-72B", "SAU Msta", "BMP-1"],
    "INFANTRY": ["Infantry AK", "Land Rover"],
}

CAT_LOOKUP = {}
for k, v in CATS.items():
    for i in v:
        CAT_LOOKUP[i] = k


def get_cached_coords(section, target):
    log.info('Checking for coords')
    with open(LAST_RUN_CACHE, 'r') as fp_:
        data = json.load(fp_)
    for item in data[int(section)-1]:
        if item['target_num'] == int(target):
            return (item['lat'], item['lon'], item['alt'])


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
        self.target_num = 0
        self.start_coords = start_coords

        self.group_name = item['Group'] if item["Group"] != '' else self.name
        if self.group_name == '':
            self.group_name = f"{self.platform}-{self.id}"
        try:
            self.alt = round(item["LatLongAlt"]["Alt"])
        except Exception as e:
            self.alt = 0
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
        except KeyError:
            self.cat = "Unknown"

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
    @property
    def str(self):
        str = f"{self.target_num}) {self.cat}: {self.platform} {self.lat}, {self.lon}, {self.alt}m, {self.dist}nm"
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
            enemey.target_num = len(self.groups[enemy.group_name]) + 1
            self.groups[enemy.group_name].append(enemy)
        except KeyError:
            enemy.target_num = 1
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
        output = {}
        for k, v in self.groups.items():
            min_dist = min([enemy.dist for enemy in v])
            output[min_dist] = [i.__dict__ for i in v]
        output = [output[k] for k in sorted(output.keys())]
        return json.dumps(output)


def construct_enemy_set(enemy_state, result_as_string=True, coord_fmt='dms'):
    """Parse json response from gaw state endpoint into an enemy list"""
    start_coord = None
    start_pilot = 'None'
    for pilot in ["someone_somewhere", "CVN-74", "Stennis"]:
        if start_coord:
            break
        for id, ent in enemy_state.items():
            if ent["Pilot"] == pilot or ent['Group'] == pilot:
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
        try:
            enemy = Enemy(item, start_coord, coord_fmt)
            enemy_groups.add(enemy)
        except Exception as e:
            pprint(item)
            raise e

    with open(LAST_RUN_CACHE, 'w') as fp_:
        fp_.write(enemy_groups.serialize())

    if result_as_string:
        results = {}

        for grp_name, enemy_set, grp_dist in enemy_groups:
            if start_coord and (grp_dist > MAX_DIST):
                log.info("Excluding %s...distance is %d...", grp_name,
                         grp_dist)
                continue
            grp_results = [e.str for e in enemy_set]
            grp_results.insert(0, f"{grp_name} - {grp_dist}")
            results[grp_dist] = '\r\n\t'.join(grp_results)

        results = [results[k] for k in sorted(results.keys())]
        results = [f"{i+1}) {r}" for i, r in enumerate(results)]
        results = '\r\n\r\n'.join(results)
        results = f"Start Coords: {start_pilot} {start_coord}\r\n\r\n{results}".encode('UTF-8')
        return results

    return enemies
