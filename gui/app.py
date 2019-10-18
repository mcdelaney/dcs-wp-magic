import logging
from multiprocessing import Process
import tkinter as tk

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")


class StartStopController:
    """Create Start/Stop Buttons that update Status."""

    def __init__(self, label, start_row, proc_to_run, window):
        self.label = tk.Label(window, text=label)
        self.label.grid(column=0, row=start_row)

        self.status = tk.Label(window, text="Stopped")
        self.status.grid(column=1, row=start_row)

        self.start = tk.Button(window, text="Start", state="normal",
                               command=self.switch_status)
        self.start.grid(column=0, row=start_row+1)

        self.stop = tk.Button(window, text="Stop", state='disabled',
                              command=self.switch_status)
        self.stop.grid(column=1, row=start_row+1)

        self.proc_to_run = proc_to_run
        self.proc = None

    def switch_status(self):
        if str(self.stop['state']) == 'disabled':
            self.start_process()
            self.stop.configure(state="normal")
            self.start.configure(state="disabled")
            self.status.configure(text="Running")
            log.info('Status values updated correctly...')
        else:
            self.stop_process()
            log.info('Process stopped...updating status values...')
            self.stop.configure(state="disabled")
            self.start.configure(state="normal")
            self.status.configure(text="Stopped")
            log.info('Status values updated correctly...')

    def start_process(self):
        if self.proc:
            raise ValueError("Process already exists!")
        log.info('Starting process...')
        self.proc = Process(target=self.proc_to_run)
        self.proc.start()
        log.info("Process started successfully...")

    def stop_process(self):
        if not self.proc:
            return
        log.info('Stopping process...')
        self.proc.terminate()
        self.proc.join()
        self.proc = None
        log.info("Process stopped successfully...")
