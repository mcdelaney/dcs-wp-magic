#!python
from multiprocessing import Process
import time

import coord_server
import tacview_client


def main():
    """Start tacview client and coord_server."""
    try:
        tacview_cli = Process(target=tacview_client.main)
        tacview_cli.start()
        coord_srv = Process(target=coord_server.main)
        coord_srv.start()

    except KeyboardInterrupt:
        coord_srv.terminate()
        tacview_cli.terminate()
        coord_srv.join()
        tacview_cli.join()


if __name__=='__main__':
    main()
