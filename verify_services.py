import urllib.request

urls = ["http://127.0.0.1:8000/", "http://127.0.0.1:8001/docs"]
for url in urls:
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            data = r.read()
            print(url, r.status, len(data))
    except Exception as e:
        print("ERROR", url, e)
