#!/bin/python3
import argparse
import os
import requests as r
import sys
from dcs import core


GAW_PATH = "C:/Users/mcdel/Saved Games/DCS/Scratchpad/gaw.txt"
PGAW_PATH = "C:/Users/mcdel/Saved Games/DCS/Scratchpad/pgaw.txt"


def main(args):
    print('Requesting enemies...')
    if args.m == "pgaw":
        url = core.PGAW_STATE_URL
        file_path = PGAW_PATH
    elif args.m == "gaw":
        url = core.GAW_STATE_URL
        file_path = GAW_PATH
    else:
        raise

    resp = r.get(url)
    resp.raise_for_status()
    state = resp.json()
    print('Enemies received...parsing...')
    enemies = core.construct_enemy_set(state)

    with open(file_path, 'wb') as fp:
        fp.write(enemies)
    print('Data written to: ', file_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("m")
    args = parser.parse_args()
    main(args)
    sys.exit(0)
