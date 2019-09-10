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

for i in ["5",'5','6',  'enter']:
    keyboard.press_and_release(NUMPAD[i] + ', space')
    time.sleep(0.25)

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
