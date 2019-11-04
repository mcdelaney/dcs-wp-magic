#!/usr/bin/env python3
"""Start the tacview reader."""
import argparse

from dcs import tacview


if __name__ == '__main__':
    parser = argparse.ArgumentParser() # pylint: disable=invalid-name
    parser.add_argument("--host", default="147.135.8.169", type=str,
                        help="Name of the host to connect to.")
    parser.add_argument("--port", default=42674, type=int,
                        help="Name of the host to connect to.")
    parser.add_argument("--mode", default="local", type=str,
                        help="If local, records only written to sqlite.\
                        If remote, they are written to pubsub also.")
    parser.add_argument("--debug", default=False, type=bool,
                        help="If local, records only written to sqlite.\
                        If remote, they are written to pubsub also.")
    args = parser.parse_args() # pylint: disable=invalid-name
    tacview.main(args.host, args.port, args.mode, args.debug) # pylint: disable=too-many-function-args
