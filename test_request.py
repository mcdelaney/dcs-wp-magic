import requests as r


if __name__=="__main__":
    result = r.get("http://127.0.0.1:5000/pgaw").content
    print(result.decode('UTF-8'))

    result = r.get("http://127.0.0.1:5000/gaw").content
    print(result.decode('UTF-8'))
