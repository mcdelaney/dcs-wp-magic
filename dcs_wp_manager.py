#!python
from multiprocessing import freeze_support
from dcs import gui

freeze_support()


def _delete_window():
    try:
        app.destroy()
    except Exception:
        pass


def _destroy(event):
    app.stop_process()


if __name__ == '__main__':
    app = gui.DCSWPControllerApp()
    app.protocol("WM_DELETE_WINDOW", _delete_window)
    app.bind("<Destroy>", _destroy)
    app.switch_status()
    app.mainloop()
