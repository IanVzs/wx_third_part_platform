# -*-coding: utf-8-*-

import config
from log import *
from lib.wx_service import WeChat_OAP


def send_log(msg, err=False):
    try:
        log_info(msg)
        if config.DEBUG_LOG.get("switch"):
            if (config.DEBUG_LOG.get("log_key") and config.DEBUG_LOG.get("log_key") in msg) or err:
                wechat_oap = WeChat_OAP("third_part_platform", config.DEBUG_LOG.get("appid") or '')
                if len(msg) > 2048:
                    msg = msg[:2048]
                data = {"touser": config.DEBUG_LOG.get("touser") or '', "msgtype": "text", "text": {"content": msg}}
                wechat_oap.send_custom_msg(data)
    except:
        pass

    return 1
