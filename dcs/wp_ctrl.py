import logging
import socket
import re
from time import sleep


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class Driver:
    def __init__(self, host="127.0.0.1", port=7778):
        self.logger = log
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host, self.port = host, port
        self.limits = dict()
        self.short_delay, self.medium_delay = 0.3, 0.3

    def press_with_delay(self, key, delay_after=None, delay_release=None, raw=False):
        if not key:
            return False

        if delay_after is None:
            delay_after = 0.35

        if delay_release is None:
            delay_release = 0.1

        encoded_str = key.encode('utf-8')

        # TODO get rid of the OSB -> OS replacement
        if not raw:
            sent = self.s.sendto(f"{key} 1\n".encode("utf-8"), (self.host, self.port))
            sleep(delay_release)

            self.s.sendto(f"{key} 0\n".encode("utf-8"), (self.host, self.port))
            strlen = len(encoded_str) + 3
        else:
            sent = self.s.sendto(f"{key}\n".encode("utf-8"), (self.host, self.port))
            strlen = len(encoded_str) + 1

        sleep(delay_after)
        return

    def stop(self):
        self.s.close()



class HornetDriver(Driver):
    def __init__(self):
        super().__init__()
        self.limits = dict(WP=None, MSN=6)
        self.logging = log

    def ufc(self, num):
        key = f"UFC_{num}"
        self.press_with_delay(key, delay_after=None,
                              delay_release=None)
        if num == 'ENT':
            sleep(0.2)

    def lmdi(self, pb):
        key = f"LEFT_DDI_PB_{pb.zfill(2)}"
        self.press_with_delay(key, delay_after=None,
                              delay_release=None)

    def ampcd(self, pb):
        key = f"AMPCD_PB_{pb.zfill(2)}"
        self.press_with_delay(key, delay_after=None,
                              delay_release=None)

    def enter_pp_msn(self, coord, n=1):
        lat = coord[0]
        long = coord[1]
        elev = coord[2]
        self.logging.info(f"Entering coords string: {'.'.join(lat)}, {'.'.join(long)}")
        self.lmdi("14")
        self.ufc("OS3") # POS
        self.ufc("OS1") # LAT
        for char in lat:
            self.ufc(char)

        self.ufc("OS3") # LONG
        for char in long:
            self.ufc(char)

        sleep(0.5)
        self.lmdi("14") # TGT UFT
        sleep(0.1)
        self.lmdi("14") # TGT UFT
        sleep(0.1)
        self.ufc("OS4") # UFT ELEV
        sleep(0.1)
        self.ufc("OS4")  # UFC FT
        sleep(0.1)
        for char in str(elev):
            self.ufc(char)
        sleep(0.2)
        self.ufc('ENT')
        self.ufc('CLR')
        self.ufc('CLR')
        return

    def enter_pp_coord(self, coords):
        for i, coord in enumerate(coords):
            if i == 0:
                pass
            elif (i % 2) != 0:
                self.lmdi("7") #PP2
            else:
                self.lmdi("13") # STEP
            self.enter_pp_msn(coord, n=0)

    # def enter_missions(self, missions):
    #     def stations_order(x):
    #         if x == 8:
    #             return 0
    #         elif x == 7:
    #             return 1
    #         elif x == 3:
    #             return 2
    #         elif x == 2:
    #             return 3
    #
    #     sorted_stations = list()
    #     stations = dict()
    #     for mission in missions:
    #         station_msn_list = stations.get(mission.station, list())
    #         station_msn_list.append(mission)
    #         stations[mission.station] = station_msn_list
    #
    #     for k in sorted(stations, key=stations_order):
    #         sorted_stations.append(stations[k])
    #
    #     self.lmdi("19")
    #     self.lmdi("15")
    #     # select stations
    #     if 8 in stations:
    #         self.lmdi("14")
    #     if 2 in stations:
    #         self.lmdi("11")
    #     if 7 in stations:
    #         self.lmdi("13")
    #     if 3 in stations:
    #         self.lmdi("12")
    #     self.lmdi("15")
    #     self.lmdi("4")
    #
    #     for msns in sorted_stations:
    #         if not msns:
    #             return
    #
    #         n = 1
    #         for msn in msns:
    #             self.enter_pp_msn(msn, n)
    #             n += 1
    #
    #         self.lmdi("13")
    #     self.lmdi("6")

    # def enter_all(self, waypoints):
    #     self.enter_missions(waypoints)
    # def enter_waypoints(self, wps, sequences):
    #     if not wps:
    #         return
    #
    #     self.ampcd("10")
    #     self.ampcd("19")
    #     self.ufc("CLR")
    #     self.ufc("CLR")
    #
    #     for i, wp in enumerate(wps):
    #         if not wp.name:
    #             self.logger.info(f"Entering waypoint {i+1}")
    #         else:
    #             self.logger.info(f"Entering waypoint {i+1} - {wp.name}")
    #
    #         self.ampcd("12")
    #         self.ampcd("5")
    #         self.ufc("OSB1")
    #         self.enter_coords(wp.position, wp.elevation, pp=False, decimal_minutes_mode=True)
    #         self.ufc("CLR")
    #
    #     for sequencenumber, waypointslist in sequences.items():
    #         if sequencenumber != 1:
    #             self.ampcd("15")
    #             self.ampcd("15")
    #         else:
    #             waypointslist = [0] + waypointslist
    #
    #         self.ampcd("1")
    #
    #         for waypoint in waypointslist:
    #             self.ufc("OSB4")
    #             self.enter_number(waypoint)
    #
    #     self.ufc("CLR")
    #     self.ufc("CLR")
    #     self.ufc("CLR")
    #     self.ampcd("19")
    #     self.ampcd("10")
