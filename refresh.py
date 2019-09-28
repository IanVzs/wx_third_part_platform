import time
import datetime
import requests

a = 0

while 1:
    url = "http://127.0.0.1:8979/wx_service/refreshtoken"
    requests.request("GET", url)
    print(a)
    time.sleep(2700)
    a += 1
