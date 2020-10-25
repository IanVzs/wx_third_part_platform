# -*-coding: utf-8-*-
"""埋点"""

import time
import json
import requests

from lib import config
from lib.send_log import send_log


def track(event, propertie={}):
    # 打点埋点统计
    properties = json.dumps(propertie)
    created = time.time().as_integer_ratio()[0]
    data = {
        "event": event,
        "properties": properties,
        "created": created,
    }
    params = {"data": json.dumps([data])}
    url = config.URL_TRACK
    resp = requests.request("POST", url, data=params)
    js_resp = resp.json()
    err = False
    if js_resp.get("status") == 0 and js_resp.get("request_id"):
        err = False
    else:
        err = True
    send_log("track|params: {}, track_massage: {}".format(params["data"], js_resp.get("message") or ''), err=err)
