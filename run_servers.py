from threading import Thread

import coord_executor
import coord_server
import tacview_client


if __name__=='__main__':
    try:
        coord_exec = Thread(target=coord_executor.main)
        coord_srv = Thread(target=coord_server.main)
        tacview_cli = Thread(target=tacview_client.main)

        coord_exec.start()
        tacview_cli.start()
        coord_srv.start()
    except:
        print('Shutting down')
        coord_exec.raise_exception()
        coord_srv.raise_exception()
        tacview_cli.raise_exception()

        coord_exec.join()
        coord_srv.join()
        tacview_cli.join()
