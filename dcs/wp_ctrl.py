import logging
import socket
import re
from time import sleep
import json

COORD_PATH = 'C:/Users/mcdel/Saved Games/DCS/ScratchPad/target.txt'
LAST_RUN_CACHE = 'data/last_extract.json'

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def coord_to_keys(coord):
    out = []
    for char in ''.join(coord):
        if char == 'N':
            out.append('2')
        elif char == 'S':
            out.append('8')
        elif char == 'E':
            out.append('6')
        elif char == 'W':
            out.append('4')
        elif char == '.':
            continue
        else:
            out.append(f"{char}")
        if len(out) == 7:
            out.append("ENT")
    out.append("ENT")
    return out


class Driver:
    def __init__(self, host="127.0.0.1", port=7778):
        self.log = log
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host, self.port = host, port
        self.limits = dict()
        self.delay_after = 0.2
        self.delay_release = 0.15

    def press_with_delay(self, key, raw=False):
        if not key:
            return False
        encoded_str = key.encode('utf-8')
        if not raw:
            sent = self.s.sendto(f"{key} 1\n".encode("utf-8"), (self.host, self.port))
            sleep(self.delay_release)
            self.s.sendto(f"{key} 0\n".encode("utf-8"), (self.host, self.port))
            strlen = len(encoded_str) + 3
        else:
            sent = self.s.sendto(f"{key}\n".encode("utf-8"), (self.host, self.port))
            strlen = len(encoded_str) + 1
        sleep(self.delay_after)
    def stop(self):
        self.s.close()


class HornetDriver(Driver):
    """Control Hornet Waypoints."""
    def __init__(self):
        super().__init__()
        self.limits = dict(WP=None, MSN=6)

    def ufc(self, num):
        key = f"UFC_{num}"
        self.press_with_delay(key)
        if num == 'ENT':
            sleep(0.2)

    def lmdi(self, pb):
        key = f"LEFT_DDI_PB_{pb.zfill(2)}"
        self.press_with_delay(key)

    def ampcd(self, pb):
        key = f"AMPCD_PB_{pb.zfill(2)}"
        self.press_with_delay(key)

    def enter_pp_msn(self, coord, n=1):
        lat = coord[0]
        long = coord[1]
        elev = coord[2]
        self.log.info(f"Entering coords: {'.'.join(lat)}, {'.'.join(long)}")

        if n > 1:
            self.lmdi("13") # STEP
        if n > 4:
            self.lmdi("7") # PP2

        self.lmdi("14") # TGT UFC
        self.ufc("OS3") # POS
        self.ufc("OS1") # LAT
        for char in lat:
            self.ufc(char)

        self.ufc("OS3") # LONG
        for char in long:
            self.ufc(char)

        # sleep(0.5)
        self.lmdi("14") # TGT UFT
        # sleep(0.1)
        self.lmdi("14") # TGT UFT
        # sleep(0.1)
        self.ufc("OS4") # UFT ELEV
        # sleep(0.1)
        self.ufc("OS4")  # UFC METERS
        # sleep(0.1)
        for char in str(elev):
            self.ufc(char)
        # sleep(0.2)
        self.ufc('ENT')
        self.ufc('CLR')
        self.ufc('CLR')
        return

    def enter_pp_coord(self, coords):
        for i, coord in enumerate(coords):
            self.enter_pp_msn(coord, n=i+1)
        return 'ok'



def get_cached_coords(section, target):
    log.info('Checking for coords')
    with open(LAST_RUN_CACHE, 'r') as fp_:
        data = json.load(fp_)
    for item in data[int(section)-1]:
        if item['target_num'] == int(target):
            lat = coord_to_keys(item['lat'])
            lon = coord_to_keys(item['lon'])
            alt = [f"{n}" for n in str(item['alt'])]
            alt.append('ENT')
            return (lat, lon, alt)


def update_coord():
    with open(COORD_PATH, 'r') as fp_:
        targets = fp_.readlines()
    targets = [t.strip().split(',') for t in targets]
    open(COORD_PATH, 'w').close()
    coords = [get_cached_coords(t[0], t[1]) for t in targets]
    driver = HornetDriver()
    driver.enter_pp_coord(coords)
    return "ok"
