from tkinter import *

# import tkinter as tk

# class Application(tk.Frame):
#     def __init__(self, master=None):
#         super().__init__(master)
#         self.master = master
#         self.pack()
#         self.create_widgets()
#
#     def create_widgets(self):
#         self.hi_there = tk.Button(self)
#         self.hi_there["text"] = "Hello World\n(click me)"
#         self.hi_there["command"] = self.say_hi
#         self.hi_there.pack(side="top")
#
#         self.quit = tk.Button(self, text="QUIT", fg="red",
#                               command=self.master.destroy)
#         self.quit.pack(side="bottom")
#
#     def say_hi(self):
#         print("hi there, everyone!")
#
# root = tk.Tk()
# app = Application(master=root)
# app.mainloop()


window = Tk()
window.geometry('300x200')
window.title("DCS-WP-MAGIC")


def start_tac():
    start_tac.configure(state=DISABLED)
    stop_tac.configure(state="normal")
    tac_stat.configure(text="Running")


def stop_tac():
    start_tac.configure(state="normal")
    stop_tac.configure(state=DISABLED)
    tac_stat.configure(text="Stopped")

tac_label = Label(window, text="Tacview Client Status:")
tac_label.grid(column=0, row=0)

tac_stat = Label(window, text="Stopped")
tac_stat.grid(column=1, row=0)

start_tac = Button(window, text="Start", command=start_tac)
start_tac.grid(column=0, row=1)
stop_tac = Button(window, text="Stop", state=DISABLED,
                  command=stop_tac)
stop_tac.grid(column=1, row=1)


def start_coord_svr():
    coord_start.configure(state=DISABLED)
    coord_stop.configure(state="normal")
    coord_stat.configure(text="Running")

def stop_coord_svr():
    coord_stop.configure(state=DISABLED)
    coord_start.configure(state="normal")
    coord_stat.configure(text="Stopped")

coord_lbl = Label(window, text="Coord Server Status:")
coord_lbl.grid(column=0, row=2)
coord_stat = Label(window, text="Stopped")
coord_stat.grid(column=1, row=2)

coord_start = Button(window, text="Start", command=start_coord_svr)
coord_start.grid(column=0, row=3)
coord_stop = Button(window, text="Stop", state=DISABLED,
                  command=stop_coord_svr)
coord_stop.grid(column=1, row=3)


if __name__=='__main__':
    window.mainloop()
