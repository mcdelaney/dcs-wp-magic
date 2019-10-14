import sqlite3
import datetime as dt
import logging
import os
import sys
import time

import ujson as json
from geopy.distance import vincenty

from . import get_logger
from .config import *
from . import db

DEBUG = False

log = get_logger(logging.getLogger(__name__))
log.setLevel(logging.DEBUG if DEBUG else logging.INFO)

LAST_RUN_CACHE = 'data/last_extract.json'


def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes) / 60 + float(seconds) / (60 * 60)
    if direction == 'E' or direction == 'N':
        dd *= -1
    return dd


def dd2precise(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    dec = '%0.4f' % (md - m)
    return [f'{d:02}', f'{m:02}', dec[2:]]


def dd2dms(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = round((md - m) * 60, 2)
    return [f'{d:02}', f'{m:02}', f'{sd:05.2f}']


class Enemy:
    """A single enemy unit with specific attributes."""

    def __init__(self, item, start_coords=None, coord_fmt='dms'):
        self.id = item["id"]
        self.name = item["pilot"]
        self.platform = item["platform"]
        self.type = item["type"]
        self.dist = 999
        self.alive = item["alive"]
        self.target_num = 1
        self.start_coords = start_coords
        try:
            self.last_seen = int(item['lastseen'])
        except KeyError:
            pass

        if 'grp' in item.keys() and item['grp'] != '':
            self.grp_name = item['grp']
        else:
            self.grp_name = f"{self.platform}-{self.id}"
            log.debug(f"grp key not found for obj {self.id}...setting grp as {self.grp_name}")
        try:
            self.alt = max([1, round((float(item["alt"])))])
        except Exception as e:
            self.alt = 1

        self.lat_raw = item["lat"]
        self.lon_raw = item["long"]

        try:
            self.cat = CAT_LOOKUP[self.platform]
            self.order_val = CAT_ORDER[self.cat]
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
                dist = vincenty(start_coords, (self.lat_raw, self.lon_raw))
                self.dist = round(dist.nm)

            except ValueError as e:
                log.error("Coordinates are incorrect: %f %f",
                          self.lat_raw, self.lon_raw)
        log.debug(f"Created Enemy: {self.name} {self.id}...")

    def set_target_order(self, target_num):
        self.target_num = target_num
        self.order_id = float(f"{self.order_val}.{self.target_num}")

    def str(self):
        str = f"{self.target_num}) {self.cat}: {self.platform} {self.lat}, "\
              f"{self.lon}, {self.alt}m, {self.dist}nm"
        log.debug(str)
        log.debug('Created enemy %s %d from start point in grp %s...',
                 self.platform, self.dist, self.grp_name)
        return str


class EnemyGroups:
    """Dataset of named enemy groups."""
    def __init__(self):
        self.grps = {}

    def add(self, enemy):
        try:
            targets = len(self.grps[enemy.grp_name])
            enemy.set_target_order(targets + 1)
            self.grps[enemy.grp_name].append(enemy)

        except (KeyError, NameError, TypeError):
            self.grps[enemy.grp_name] = [enemy]
        total = len(self.grps[enemy.grp_name])
        log.debug(f"Added enemy to grp {enemy.grp_name}...")
        self.grps[enemy.grp_name][total-1].target_num = total

    def names(self):
        return list(self.grps.keys())

    def sort(self):
        result = {}
        for grp_key in list(self.grps.keys()):
            ents = {e.order_id: e for e in self.grps[grp_key]}
            tmp = {}
            for i, k in enumerate(sorted(ents.keys())):
                ents[k].set_target_order(i+1)
                tmp[ents[k].target_num] = ents[k]

            out_lst = [None] * len(list(tmp.keys()))
            for i, k in enumerate(sorted(tmp.keys())):
                out_lst[i]  = tmp[k]
            result[grp_key] = out_lst
        self.grps = result

    def __len__(self):
        return self.total

    def __iter__(self):
        """Yields tuples of (grp_name, enemy_list, min_distance)"""
        for grp_name, grp in self.grps.items():
            min_dist = min([enemy.dist for enemy in grp])
            yield grp_name, grp, min_dist

    def serialize(self):
        log.debug("Serializing enemy grps...")
        output = {}
        for k, v in self.grps.items():
            min_dist = min([enemy.dist for enemy in v])
            output[min_dist] = [i.__dict__ for i in v]
        output = [output[k] for k in sorted(output.keys())]
        return json.dumps(output)


def create_enemy_groups(enemy_state, start_coord, coord_fmt='dms', only_alive=True):
    enemy_groups = EnemyGroups()
    for item in enemy_state:
        try:
            if (item['type'] in EXCLUDED_TYPES or
                item['coalition'] == COALITION or
                item["pilot"] in EXCLUDED_PILOTS):
                log.debug(f"Skipping enemy item {item['type']} {item['pilot']} {item['coalition']} as is in excluded types...")
                continue
        except KeyError:
            log.error(item)

        try:
            enemy = Enemy(item, start_coord, coord_fmt)
            if only_alive and not enemy.alive:
                log.debug(f'Enemy {enemy.name} is not alive...skipping...')
                pass
            else:
                enemy_groups.add(enemy)
        except Exception as e:
            log.error(item)
            raise e
    return enemy_groups


def construct_enemy_set(enemy_state, result_as_string=True, coord_fmt='dms',
                        only_alive=True):
    try:
        last_recv = "2019-09-01"
        start_coord = None
        start_pilot = 'None'
        for pilot in ['someone_somewhere']:
            log.debug(f"Checking for start unit: {pilot}")
            if start_coord:
                log.debug('Start coord is not none...breaking...')
                break
            for ent in enemy_state:
                log.debug(f"Checking enemy name {ent['name']}")
                if ent["pilot"] == pilot or ent['grp'] == pilot:
                    start_coord = (ent['lat'], ent['long'])
                    start_pilot = pilot
                    log.info(f"Using {pilot} for start at {start_coord}...")
                    break

        enemy_groups = create_enemy_groups(enemy_state, start_coord,
                                           coord_fmt=coord_fmt,
                                           only_alive=only_alive)

        enemy_groups.sort()
        with open(LAST_RUN_CACHE, 'w') as fp_:
            fp_.write(enemy_groups.serialize())

        if result_as_string:
            results = {}
            for grp_name, enemy_set, grp_dist in enemy_groups:
                if start_coord and (grp_dist > MAX_DIST):
                    log.info(f"Excluding {grp_name}...distance is {grp_dist}...")
                    if DEBUG:
                        log.debug("Enemies in excluded grp: ")
                        for en in enemy_set:
                            log.debug(f"{en.id} {en.name}")
                    continue

                grp_val = [e.str() for e in enemy_set]
                if len(grp_val) == 0:
                    continue
                grp_val.insert(0, f"{grp_name}")
                results[grp_dist] = '\r\n\t'.join(grp_val)

            results = [results[k] for k in sorted(results.keys())]
            results = [f"{i+1}) {r}" for i, r in enumerate(results)]
            results = '\r\n\r\n'.join(results)
            results = f"Start Ref: {start_pilot} "\
                      f"{(round(start_coord[0], 3), round(start_coord[1], 3))}"\
                      f" {last_recv}\r\n\r\n{results}"
            return results.encode('UTF-8')
    except Exception as err:
        log.exception(err)
    return enemy_groups


def read_coord_sink(sink_path='data/tacview_sink.json'):
    conn = db.create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM enemies \
                WHERE pilot IS NOT NULL and type IS NOT NULL AND alive=1")
    results = cur.fetchall()
    results = [dict(e) for e in results]
    return results


# conn.close()
# cur.execute("SELECT * FROM enemies limit 10")
# results = cur.fetchall()
# [print(dict(r)) for r in results]
# results[0]['alive']
