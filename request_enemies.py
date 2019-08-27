import os
from pprint import pprint
import requests as r
from tkinter import Tk

if __name__ == "__main__":
    print('Requesting enemies...')
    resp = r.get("http://127.0.0.1:5000/as_strings")
    print('Enemies received...parsing...')
    enemies = resp.content.decode()
    print(enemies)
    # enemy_result = enemy_to_string(enemies)

    # r = Tk()
    # r.withdraw()
    # r.clipboard_clear()
    # r.clipboard_append(enemy_result)
    # r.update() # now it stays on the clipboard after the window is closed
    # print(r.selection_get(selection="CLIPBOARD"))
    # r.destroy()
