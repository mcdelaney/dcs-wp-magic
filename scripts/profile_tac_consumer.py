#!/usr/bin/env python
import argparse
from functools import partial
from multiprocessing import Process
import sys
from pathlib import Path
import yappi


sys.path.append(str(Path('.').parent.absolute()))
from dcs.tacview import client

sys.path.append(str(Path('.').parent.absolute().joinpath('tests')))
import serve_test_data # type: ignore


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--iters", type=int, default=50000,
                        help='Number of lines to read')
    parser.add_argument('--profile', action='store_true',
                        help='Set this flag to run yappi profiler')
    parser.add_argument('--filename', type=str,
                        help='Filename to process')
    parser.add_argument('--bulk', action='store_true',
                        help='Should the program run in bulk mode?')
    args = parser.parse_args()

    if args.profile:
        yappi.set_clock_type('cpu')
        yappi.start(builtins=True)

    server_proc = Process(target=partial(
        serve_test_data.main, filename=args.filename))
    server_proc.start()

    client.main(host='127.0.0.1',
                port=5555,
                debug=False,
                max_iters=args.iters,
                only_proc=False,
                bulk=args.bulk)

    if not args.profile:
        client.check_results()

    server_proc.terminate()

    if args.profile:
        prof_filename = 'callgrind.tacview.prof'
        thread_stats = yappi.get_thread_stats()
        mem_stats = yappi.get_mem_usage()
        stats = yappi.get_func_stats()
        stats.sort('ttot', 'asc')
        stats.save(prof_filename, type='callgrind') # type: ignore
        mem_stats.print_all() # type: ignore
        thread_stats.print_all() # type: ignore
