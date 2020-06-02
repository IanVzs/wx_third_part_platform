# -*-coding: utf-8-*-

import redis

from log import *
from . import config

r_db = redis.Redis(host=config.HOST_REDIS, port=config.POER_REDIS)


def set_new(_key, _value):
    sign = False
    try:
        sign = r_db.set(_key, _value)
    except:
        log_error("save to redis error: key:{}, value:{}".format(str(_key), str(_value)))
    return sign


def get_value(_key):
    value = r_db.get(_key)
    if value:
        value = value.decode("utf-8")
    return value
