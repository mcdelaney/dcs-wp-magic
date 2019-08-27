#!/bin/python3
import os
import requests as r
import sys
from dcs import core


FILE_PATH = "C:/Users/mcdel/Saved Games/DCS/Scratchpad/0000.txt"


if __name__ == "__main__":
    print('Requesting enemies...')
    resp = r.get(core.STATE_URL)
    resp.raise_for_status()
    state = resp.json()
    print('Enemies received...parsing...')
    enemies = core.construct_enemy_set(state)
    # enemies = resp.content.decode()
    with open(FILE_PATH, 'w') as fp:
        fp.write(enemies)
    print('Data written to: ', FILE_PATH)
    sys.exit(0)
