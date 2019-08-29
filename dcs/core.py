import json
import geopy.distance

OUT_PATH = "C:/Users/mcdel/Saved Games/DCS/Scratchpad/coords.txt"

START_UNIT = "CVN-74"

PGAW_KEY = "243bd8b1-3198-4c0b-817a-fadb40decf23"
PGAW_STATUS_URL = f"https://status.hoggitworld.com/{PGAW_KEY}"
PGAW_STATE_URL = f"https://state.hoggitworld.com/{PGAW_KEY}"

GAW_KEY = "f67eecc6-4659-44fd-a4fd-8816c993ad0e"
GAW_STATUS_URL = f"https://status.hoggitworld.com/{GAW_KEY}"
GAW_STATE_URL = f"https://state.hoggitworld.com/{GAW_KEY}"


ENEMY_COALITION = "Allies"

MAX_DIST = 200

CATS = {
    'MOBILE_CP': ["S-300PS 54K6 cp", "SKP-11"],
    'RADAR': [
        "S-300PS 40B6M tr", "S-300PS 40B6MD sr", "S-300PS 64H6E sr",
        "Kub 1S91 str", "snr s-125 tr", "1L13 EWR", "Dog Ear radar",
        "SA-11 Buk SR 9S18M1"
    ],
    'SAM': [
        "S-300PS 5P85C ln", "Kub 2P25 ln", "SA-11 Buk LN 9A310M1",
        "5p73 s-125 ln", "Osa 9A33 ln", "Strela-10M3", "Strela-1 9P31"
    ],
    "AAA": [
        "ZSU-23-4 Shilka", "2S6 Tunguska", "Ural-375 ZU-23",
        "ZU-23 Emplacement Closed", "SA-18 Igla-S manpad"
    ],
    'ARMOR': ["Ural-375 PBU", "BMP-2", "T-72B", "SAU Msta"],
    "INFANTRY": ["Infantry AK"],
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
            unit_str = "\t" + unit + '  '.join([lat, lon, elem['alt'] + 'm'
                                                ]) + "\r\n"
            str_base += unit_str
        enemy_out.append(str_base)
    return '\r\n'.join(enemy_out)


def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes) / 60 + float(seconds) / (60 * 60)
    if direction == 'E' or direction == 'N':
        dd *= -1
    return dd


def dd2dms(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = round((md - m) * 60, 2)
    return [f'{d:02}', f'{m:02}', f'{sd:05.2f}']


class Enemy:
    """A single enemy unit with specific attributes."""
    def __init__(self, item, start_coords=None):
        self.id = item["id"]
        self.name = item["Name"]
        self.dist = 999
        try:
            self.group_name = item['GroupName']
        except KeyError:
            self.group_name = self.name + '-' + str(item['id'])
        self.type = item["Type"]
        try:
            self.unit_name = item["UnitName"]
        except KeyError:
            self.unit_name = None
        self.alt = round(item["LatLongAlt"]["Alt"])
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

        lat = '.'.join(self.lat_dms)
        lon = '.'.join(self.lon_dms)

        if start_coords:
            self.dist = round(
                geopy.distance.vincenty(start_coords,
                                        [self.lat_raw, self.lon_raw]).nm)

        self.str = f"{self.cat}: {self.name} {lat}, {lon}, {self.alt}m, {self.dist}nm"



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


def construct_enemy_set(enemy_state, result_as_string=True):
    """Parse json response from gaw state endpoint into an enemy list"""
    start_coord = None
    for ent in enemy_state['objects']:
        if "UnitName" in list(ent.keys()) and ent["UnitName"] == START_UNIT:
            start_coord = [ent['LatLongAlt']['Lat'], ent['LatLongAlt']['Long']]
            break

    enemy_groups = EnemyGroups()
    for item in enemy_state['objects']:
        if item["Coalition"] == ENEMY_COALITION and item['Type']['level1'] == 2:
            enemy = Enemy(item, start_coord)
            enemy_groups.add(enemy)

    if result_as_string:
        results = {}
        for grp_name, enemy_set, grp_dist in enemy_groups:
            if grp_dist > MAX_DIST:
                continue
            grp_string = grp_name + '\r\n\t'
            grp_string +='\r\n\t'.join([elem.str for elem in enemy_set])
            results[grp_dist] = grp_string

        results_string = [results[k] for k in sorted(results.keys())]
        result_string = '\r\n\r\n'.join(results_string)
        result_string = result_string.encode('UTF-8')
        return result_string

    return enemies
