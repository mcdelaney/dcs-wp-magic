#!python
from tkinter import *

import coord_server
from gui import app
import tacview_client


def _delete_window():
    try:
        window.destroy()
    except:
        pass

def _destroy(event):
    tac_controller.stop_process()
    coord_controller.stop_process()


if __name__=='__main__':
    window = Tk()
    window.geometry('300x200')
    window.title("DCS-WP-MAGIC")

    tac_controller = app.StartStopController('Tacview Client Status:', 0,
                                             tacview_client.main, window)
    coord_controller = app.StartStopController('Coord Server Status:', 2,
                                               coord_server.main, window)

    window.protocol("WM_DELETE_WINDOW", _delete_window)
    window.bind("<Destroy>", _destroy)

    window.mainloop()
