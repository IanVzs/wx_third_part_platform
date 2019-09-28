# -*- coding: utf-8 -*-

import logging
import json
from flask import request
from logging.config import fileConfig

fileConfig('log.ini')
logger = logging.getLogger()


def log_info(_info, _msg=None, id_=""):
    if _msg:
        if isinstance(_msg, str):
            logger.info("%s\t\t%s\t%s" % (id_, _info, _msg))
        elif isinstance(_msg, dict):
            logger.info("%s\t\t%s\t%s" % (id_, _info, json.dumps(_msg, ensure_ascii=False)))
        elif isinstance(_msg, type(request)):
            logger.info("%s\t\t%s\t%s" % (id_, _info, _msg.url))
    else:
        logger.info("%s\t\t%s" % (id_, _info))


def log_error(_info, _error=None, id_=""):
    if not _error:
        logger.error("%s\t\t%s" % (id_, _info))
    else:
        logger.error("%s\t\t%s\t%s\t%s" % (id_, _error.__class__.__name__, str(_error), _info))


def log_warning(_info):
    logger.warning(_info)
