import requests as r


if __name__=="__main__":
    result = r.get("http://127.0.0.1:5000/enter/1/1").content
    print(result.decode('UTF-8'))
