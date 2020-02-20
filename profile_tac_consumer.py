#!/usr/bin/env python
import argparse
from functools import partial
from multiprocessing import Process
from dcs.tacview import client
from tests.serve_test_data import main


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--iters", type=int, default=50000,
                        help='Number of lines to read')
    parser.add_argument('--profile', action='store_true',
                        help='Set this flag to run yappi profiler')
    args = parser.parse_args()

    if args.profile:
        import yappi
        filename = 'callgrind.tacview.prof'
        yappi.set_clock_type('cpu')
        yappi.start(builtins=True)

    server_proc = Process(target=partial(
        main, filename='tests/data/tacview-test2.txt'))
    server_proc.start()
    client.main(host='127.0.0.1',
                port=5555,
                debug=False,
                max_iters=args.iters,
                only_proc=False)
    server_proc.terminate()
    # server_proc.close()

    if args.profile:
        stats = yappi.get_func_stats()
        stats.save(filename, type='callgrind')
        stats.print_all()
