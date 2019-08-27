from pprint import pprint
import keyboard
import time

NUMPAD = {
    "0": "num 0",
    "1": "num 1",
    "2": "num 2",
    "3": "num 3",
    "4": "num 4",
    "5": "num 5",
    "6": "num 6",
    "7": "num 7",
    "8": "num 8",
    "9": "num 9",
    ".": "decimal",
    "enter": "num enter"
}

# pprint(keyboard.KeyboardEvent(event_type='down', name="num 5").__dict__)
# keyboard.send(73)
event = keyboard.read_event()

pprint(event.__dict__)
# keyboard.send([event])
# keyboard.send("82")f
# keyboard.send("79")
# keyboard.send("75")


# for i in ['a','b','c']:
#     keyboard.write(i)
#     time.sleep(0.5)
    # keyboard.write(i, do_press=False, do_release=True)
#
# for i in [8,5,5,6]:
#     keyboard.send(NUMPAD[i])
#     time.sleep(0.5)
# keyboard.send("Num+5")
event1 = keyboard.parse_hotkey("decimal")
pprint(event1)
# for i in [8,5,5,6]:
#     keyboard.send(NUMPAD[i], do_press=True, do_release=False)
#     time.sleep(0.5)
#     keyboard.send(NUMPAD[i], do_press=False, do_release=True)

# event1 = keyboard.KeyboardEvent(event_type='down', scan_code= NUMPAD[8],55
#                                 is_keypad=True)
# event2 = keyboard.KeyboardEvent(event_type='up', scan_code= NUMPAD[8],
#                                 is_keypad=True)
# event3 = keyboard.KeyboardEvent(event_type='down', scan_code=NUMPAD[5],
#                                 is_keypad=True)
# event4 = keyboard.KeyboardEvent(event_type='up', scan_code=NUMPAD[5],
#                                 is_keypad=True)
# events = [event1, event2, event3, event4]
# keyboard.replay(events)

# keyboard.start_recording()
# time.sleep(5)
# events = keyboard.stop_recording()
# for i in events:
#     pprint(i)
# keyboard.replay(events)
# print(events.__dir__())
