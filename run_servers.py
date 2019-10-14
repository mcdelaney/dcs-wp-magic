#!python

from threading import Thread
import time

import coord_server
import tacview_client


if __name__=='__main__':
    try:
        tacview_cli = Thread(target=tacview_client.main)
        tacview_cli.start()
        time.sleep(3)
        coord_srv = Thread(target=coord_server.main)
        coord_srv.start()

    except:
        print('Shutting down')
        coord_srv.raise_exception()
        tacview_cli.raise_exception()

        coord_srv.join()
        tacview_cli.join()
