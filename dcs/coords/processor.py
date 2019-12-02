"""Classes and methods to prepare enemy records for export to dcs-ui."""
import logging
import json
import sqlite3

from geopy.distance import geodesic

from dcs.common import get_logger
from dcs.common import config

DEBUG = False

LOG = get_logger(logging.getLogger('dcs_core'))
LOG.setLevel(logging.DEBUG if DEBUG else logging.INFO)

LAST_RUN_CACHE = 'data/last_extract.json'


def dms2dd(degrees, minutes, seconds, direction):
    """Convert dms coord to dd."""
    # pylint: disable=invalid-name
    dd = float(degrees) + float(minutes) / 60 + float(seconds) / (60 * 60)
    if direction in ('E', 'N'):
        dd *= -1
    return dd


def dd2precise(deg):
    """Convert DD formatted coords to precise."""
    # pylint: disable=invalid-name
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    dec = '%0.4f' % (md - m)
    return [f'{d:02}', f'{m:02}', dec[2:]]


def dd2dms(deg):
    """Convert DD to dms coords."""
    # pylint: disable=invalid-name
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = round((md - m) * 60, 2)
    return [f'{d:02}', f'{m:02}', f'{sd:05.2f}']


class Enemy:  # pylint: disable=too-many-instance-attributes
    """A single enemy unit with specific attributes."""

    def __init__(self, item, start_coords=None, coord_fmt='dms'):
        self.id = item["id"]  # pylint: disable=invalid-name
        self.name = item["name"]
        self.pilot = item["pilot"]
        self.platform = item["platform"]
        self.type = item["type"]
        self.dist = 999
        self.target_num = 1
        self.last_seen = item['last_seen']

        if item['grp'] != '':
            self.grp_name = item['grp']
        else:
            self.grp_name = f"{self.platform}-{self.id}"
            LOG.debug("grp key not found for obj %s...setting grp as %s",
                      self.id, self.grp_name)
        try:
            if item['alt'] is None:
                self.alt = 1.0
            else:
                self.alt = max([1.0, round((float(item["alt"])))])
        except (TypeError, ValueError):
            self.alt = 1.0

        self.lat_raw = item["lat"]
        self.lon_raw = item["lon"]

        try:
            self.cat = config.CAT_LOOKUP[self.name]
            self.order_val = config.CAT_ORDER[self.cat]
        except KeyError:
            self.cat = self.type
            self.order_val = 4

        self.order_id = float(f"{self.order_val}.{self.target_num}")

        lat_card = 'S' if self.lat_raw < 0 else 'N'
        lon_card = 'W' if self.lon_raw < 0 else 'E'
        if coord_fmt == 'dms':
            self.lat_dms = [lat_card] + dd2dms(self.lat_raw)
            self.lon_dms = [lon_card] + dd2dms(self.lon_raw)
            self.lat = '.'.join(self.lat_dms)
            self.lon = '.'.join(self.lon_dms)
        elif coord_fmt == 'precise':
            self.lat_precise = [lat_card] + dd2precise(self.lat_raw)
            self.lon_precise = [lon_card] + dd2precise(self.lon_raw)
            self.lat = '.'.join(self.lat_precise)
            self.lon = '.'.join(self.lon_precise)
        elif coord_fmt == 'dd':
            self.lat_dd = lat_card + '.' + str(abs(round(self.lat_raw, 6)))
            self.lon_dd = lon_card + '.' + str(abs(round(self.lon_raw, 6)))

            self.lat = self.lat_dd
            self.lon = self.lon_dd
        else:
            self.lat = 0
            self.lon = 0

        if start_coords:
            try:
                self.dist = geodesic((start_coords['lat'],
                                      start_coords['lon']),
                                     (self.lat_raw, self.lon_raw)).nm
            except ValueError:
                LOG.error("Coordinates are incorrect: %f %f",
                          self.lat_raw, self.lon_raw)
        LOG.debug("Created Enemy: %s %s...", self.name, self.id)

    def set_target_order(self, target_num):
        """Set order number for each target using category prioritization."""
        self.target_num = target_num
        self.order_id = float(f"{self.order_val}.{self.target_num}")

    def str(self):
        """Coerce an enemy to string for display in DCS."""
        val = f"{self.target_num}) {self.cat}: {self.name} {self.lat}, "\
              f"{self.lon}, {self.alt}m, {round(self.dist)}nm"
        LOG.debug(val)
        LOG.debug('Created enemy %s %d from start point in grp %s...',
                  self.platform, self.dist, self.grp_name)
        return val


class EnemyGroups:
    """Dataset of named enemy groups."""

    def __init__(self):
        self.grps = {}

    def add(self, enemy):
        """Add an enemy to the group."""
        try:
            targets = len(self.grps[enemy.grp_name])
            enemy.set_target_order(targets + 1)
            self.grps[enemy.grp_name].append(enemy)
        except (KeyError, NameError, TypeError):
            self.grps[enemy.grp_name] = [enemy]
        total = len(self.grps[enemy.grp_name])
        LOG.debug("Added enemy to grp %s...", enemy.grp_name)
        self.grps[enemy.grp_name][total-1].target_num = total

    def names(self):
        """Return the names of all enemy groups."""
        return list(self.grps.keys())

    def sort(self):
        """Sort enemy groups by distance to start-coord."""
        result = {}
        for grp_key in list(self.grps.keys()):
            ents = {e.order_id: e for e in self.grps[grp_key]}
            tmp = {}
            for i, k in enumerate(sorted(ents.keys())):
                ents[k].set_target_order(i+1)
                tmp[ents[k].target_num] = ents[k]

            out_lst = [None] * len(list(tmp.keys()))
            for i, k in enumerate(sorted(tmp.keys())):
                out_lst[i] = tmp[k]
            result[grp_key] = out_lst
        self.grps = result

    def __iter__(self):
        """Yields tuples of (grp_name, enemy_list, min_distance)"""
        for grp_name, grp in self.grps.items():
            min_dist = min([enemy.dist for enemy in grp])
            yield grp_name, grp, min_dist

    def serialize(self):
        """Serialize enemy group for output."""
        LOG.debug("Serializing enemy grps...")
        output = {}
        for val in self.grps.values():
            min_dist = min([enemy.dist for enemy in val])
            output[min_dist] = [i.__dict__ for i in val]
        output = [output[key] for key in sorted(output.keys())]
        return json.dumps(output)


def create_enemy_groups(enemy_state, start_coord, coord_fmt='dms'):
    """Create an enemy group set from state."""
    enemy_groups = EnemyGroups()
    for item in enemy_state:
        if (item['type'] in config.EXCLUDED_TYPES or
                item['coalition'] == config.COALITION):
            LOG.debug("Skipping item %s %s %s as is in excluded types...",
                      item['type'], item['pilot'], item['coalition'])
            continue
        try:
            enemy = Enemy(item, start_coord, coord_fmt)
            enemy_groups.add(enemy)
        except Exception as err:
            LOG.exception(err)
            LOG.error(item)
            raise err
    return enemy_groups


def construct_enemy_set(start_unit=None, result_as_string=True,
                        coord_fmt='dms', pilot=None):
    """Constuct a EnemyGroup of Enemies, returning a formatted string."""

    enemy_state, start_coord = read_coords(start_unit)
    enemy_groups = create_enemy_groups(enemy_state, start_coord,
                                       coord_fmt=coord_fmt)
    enemy_groups.sort()

    if not result_as_string:
        return enemy_groups

    with open(LAST_RUN_CACHE, 'w') as fp_:
        fp_.write(enemy_groups.serialize())

    results = {}
    for grp_name, enemy_set, grp_dist in enemy_groups:
        if start_coord and (grp_dist > config.MAX_DIST):
            LOG.info("Excluding %s...distance is %s...",
                     grp_name, str(grp_dist))
            continue

        grp_val = [e.str() for e in enemy_set]
        if not grp_val:
            continue

        grp_val.insert(0, f"{grp_name}")
        results[grp_dist] = '\r\n\t'.join(grp_val)

    results = [results[k] for k in sorted(results.keys())]
    results = [f"{i+1}) {r}" for i, r in enumerate(results)]
    results = '\r\n\r\n'.join(results)
    results = f"Start Ref: {start_coord['pilot']} "\
              f"{(round(start_coord['lat'], 3), round(start_coord['lon'], 3))} "\
              f"{start_coord['last_seen']}" \
              f"\r\n\r\n{results}"
    return results.encode('UTF-8')


def read_coords(start_units=config.START_UNITS, coalition='Enemies'):
    """Collect a list of Enemy Dictionaries from the database."""
    conn = sqlite3.connect(config.DB_LOC,
                           detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    LOG.info('Querying for enemy list...')
    cur.execute("SELECT * FROM object \
                 WHERE alive = 1 AND coalition != '%s'" % coalition)
    enemies = [dict(e) for e in cur.fetchall()]

    for unit in [start_units]:
        LOG.info('Querying for start unit %s...', unit)
        cur = conn.cursor()
        cur.execute("SELECT lat, lon, alt, name, pilot, last_seen \
                     FROM object \
                     WHERE coalition = '%s' AND \
                       alive = 1 AND pilot = '%s'" % (coalition, unit))
        start = [dict(r) for r in cur.fetchall()]
        if start:
            start = start[0]
            break
    if not start:
        raise ValueError("No record found for start_unit %s..." % start_units)
    LOG.info('Start coord found: %s...', start)
    conn.close()
    return enemies, start
