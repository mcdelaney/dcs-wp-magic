#!/usr/bin/env python3
"""Start the tacview reader."""
import argparse

from dcs import tacview


def str2bool(val):
    """Better bool arg handling."""
    if isinstance(val, bool):
        return val
    if val.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    if val.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    raise argparse.ArgumentTypeError('Boolean value expected.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser() # pylint: disable=invalid-name
    parser.add_argument("--host", default="147.135.8.169", type=str,
                        help="Name of the host to connect to.")
    parser.add_argument("--port", default=42674, type=int,
                        help="Name of the host to connect to.")
    parser.add_argument("--mode", default="local", type=str,
                        help="If local, records only written to sqlite.\
                        If remote, they are written to pubsub also.")
    parser.add_argument("--debug", default=False, type=str2bool,
                        help="If local, records only written to sqlite.\
                        If remote, they are written to pubsub also.")
    parser.add_argument("--parents", default=False, type=str2bool,
                        help="If true, parents will be calculated for weapons \
                        and shrapnel.")
    parser.add_argument("--events", default=True, type=str2bool,
                        help="If true, events will be recorded to the database.")
    parser.add_argument("--max_iters", default=None, type=int,
                        help="Sets the maximum number of iterations before exiting.")
    parser.add_argument("--only_proc", default=False, type=str2bool,
                        help="If true, only convert line to dict.")
    args = parser.parse_args() # pylint: disable=invalid-name

    tacview.client.main(host=args.host, port=args.port, mode=args.mode,
                        debug=args.debug, parents=args.parents,
                        events=args.events, max_iters=args.max_iters,
                        only_proc=args.only_proc) # pylint: disable=too-many-function-args
