from pprint import pprint
import requests as r


if __name__=="__main__":
    result = r.get("http://127.0.0.1:5000/coords/dms").content
    print(result.decode('UTF-8'))
    with open('C:/Users/mcdel/Saved Games/DCS/Scratchpad/coords.txt', 'r') as fp_:
        result = fp_.readlines()
    pprint(result)
