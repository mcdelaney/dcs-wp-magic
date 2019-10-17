#!python
from multiprocessing import Process
import time

import coord_server
import tacview_client


if __name__=='__main__':
    try:
        tacview_cli = Process(target=tacview_client.main)
        tacview_cli.start()
        time.sleep(1)
        coord_srv = Process(target=coord_server.main)
        coord_srv.start()

    except KeyboardInterrupt:
        coord_srv.terminate()
        tacview_cli.terminate()
        coord_srv.join()
        tacview_cli.join()
