# -*- coding: utf-8 -*-

import pymysql
import time

from . import config
from log import logger


class MySQL():
    def __init__(self, config):
        self.config = config

    def execute_once(self, query, params):
        conn = pymysql.connect(**self.config)
        cur = conn.cursor()
        result = cur.execute(query, params)
        cur.nextset()
        cur.close()
        conn.commit()
        conn.close()
        return result

    def insert_and_get_id(self, query, params):
        conn = pymysql.connect(**self.config)
        cur = conn.cursor()
        result = cur.execute(query, params)
        last_id = None
        if result:
            last_id = cur.lastrowid
        cur.nextset()
        cur.close()
        conn.commit()
        conn.close()
        return last_id

    def fetch_one(self, query, params):
        conn = pymysql.connect(**self.config)
        cur = conn.cursor(pymysql.cursors.DictCursor)
        result = cur.execute(query, params)
        rlt = None
        if result:
            rlt = cur.fetchone()
        cur.nextset()
        cur.close()
        conn.close()
        return rlt

    def fetch_all(self, query, params):
        conn = pymysql.connect(**self.config)
        cur = conn.cursor(pymysql.cursors.DictCursor)
        result = cur.execute(query, params)
        rlt = []
        if result:
            rlt = list(cur.fetchall())
        cur.nextset()
        cur.close()
        conn.close()
        return rlt


mysql_conn = MySQL(config.MYSQL)
