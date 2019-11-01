import logging
from os import path
from multiprocessing import Process
from tkinter import Tk, Label, Button, Entry

from dcs.common import get_logger, config
from dcs import tacview
from dcs import coord_server

logging.basicConfig(level=logging.INFO)
LOG = get_logger(logging.getLogger('app'))


class DCSWPControllerApp(Tk):
    """DCS WP-Manager GUI layer."""

    def __init__(self):
        super().__init__()
        self.geometry("300x200")
        self.iconbitmap('icon.ico')
        self.title("DCS WP Manager")

        self.user_label = Label(self, text='Username:')
        self.user_label.grid(column=0, row=1)
        self.user = Entry()
        self.user.insert(50, 'someone_somewhere')
        self.user.grid(column=1, row=1)

        self.host_label = Label(self, text='Host:')
        self.host_label.grid(column=0, row=2)
        self.host = Entry()
        self.host.insert(50, config.HOST)
        self.host.grid(column=1, row=2)

        self.port_label = Label(self, text='Port:')
        self.port_label.grid(column=0, row=3)
        self.port = Entry()
        self.port.insert(10, config.PORT)
        self.port.grid(column=1, row=3)

        self.start = Button(self, text="Start", state="normal",
                               command=self.switch_status)
        self.start.grid(column=0, row=5)

        self.stop = Button(self, text="Stop", state='disabled',
                              command=self.switch_status)
        self.stop.grid(column=1, row=5)

        self.label = Label(self, text='Status:')
        self.label.grid(column=0, row=6)
        self.status_value = Label(self, text="Stopped")
        self.status_value.grid(column=1, row=6)

        self.tac_proc = None
        self.coord_proc = None

    def switch_status(self):
        """Either start or stop all processes, depending on current state."""
        if str(self.stop['state']) == 'disabled':
            self.start_tac_client()
            self.start_coord_server()
            self.stop.configure(state="normal")
            self.start.configure(state="disabled")
            self.status_value.configure(text="Running with user:\n %s" % self.user.get())
            LOG.info('Status values updated correctly...')
        else:
            self.stop_process()
            LOG.info('Process stopped...updating status values...')
            self.stop.configure(state="disabled")
            self.start.configure(state="normal")
            self.status_value.configure(text="Stopped")
            LOG.info('Status values updated correctly...')

    def start_tac_client(self):
        """Start the tacview client in a background process."""
        if self.tac_proc:
            raise ValueError("Tacview client process already exists!")
        LOG.info('Starting tacview client process...')
        self.tac_proc = Process(target=tacview.main, args=(self.host.get(),
                                                           self.port.get(),))
        self.tac_proc.start()
        LOG.info("Tacview client process started successfully...")

    def start_coord_server(self):
        """Start the coord server in a background process."""
        if self.coord_proc:
            raise ValueError("Coord Server process already exists!")
        LOG.info('Starting coord server process...')
        self.coord_proc = Process(target=coord_server.main)
        self.coord_proc.start()
        LOG.info("Coord server process started successfully...")

    def stop_process(self):
        """Stop both the tacview client and coord server processes."""
        if self.coord_proc:
            LOG.info('Stopping coord server process...')
            self.coord_proc.terminate()
            self.coord_proc.join()
            self.coord_proc = None
            LOG.info("Coord server process stopped successfully...")
        if self.tac_proc:
            LOG.info('Stopping tacview client process...')
            self.tac_proc.terminate()
            self.tac_proc.join()
            self.tac_proc = None
            LOG.info("tacview client process stopped successfully...")
