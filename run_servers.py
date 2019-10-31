#!python
from multiprocessing import Process

from dcs import tacview
from dcs import coord_server


def main():
    """Start tacview client and coord_server."""
    try:
        tacview_cli = Process(target=tacview.main)
        tacview_cli.start()
        coord_srv = Process(target=coord_server.main)
        coord_srv.start()

    except Exception:
        coord_srv.terminate()
        tacview_cli.terminate()
        coord_srv.join()
        tacview_cli.join()


if __name__ == '__main__':
    main()
