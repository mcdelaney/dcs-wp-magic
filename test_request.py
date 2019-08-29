import requests as r


if __name__=="__main__":
    # print(r.get("http://127.0.0.1:5000/gaw").json())
    result = r.get("http://127.0.0.1:5000/pgaw").content
    print(result.decode('UTF-8'))
    
