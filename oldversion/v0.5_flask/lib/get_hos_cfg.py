# -*-cording: utf-8-*-
"""
传入appid 获取各个组织部落的个性化配置
优先调取接口，从flaskk项目中，数据库中拉取。
若无，再从同级目录下配置文件`hos_config.json`中获取
"""
import json

from helper import api
from lib import send_log, config as lib_config
from dao import wx_service as dao_wxservice


def get_config(appid) -> dict:
    """获取配置信息"""
    cfg_data = {}
    cfg_data = get_cfg_db(appid) or get_cfg_file(appid)
    return cfg_data


def get_cfg_db(appid) -> dict:
    """从数据库获取各项配置"""
    cfg_data = {}
    app_id = dao_wxservice.get_app_id_by_wechat_id(appid) or lib_config.MAP_TEMP_APPID.get(appid) or ''
    rep_data = api.get_hos_cfg(app_id) or {}
    send_log.send_log(f'GET_CFG_DB|{rep_data}')
    rep_data = {}  # TODO 核实无误后，再启用从数据库读取配置
    if rep_data:
        release = rep_data["data"]["release"]
        cfg_data = json.loads(release or "{}")

    return cfg_data


def get_cfg_file(appid) -> dict:
    """从本地配置文件中读取配置"""
    cfg_data = {}
    with open("lib/hos_config.json", 'rb') as cfg_file:
        cfg_data = json.load(cfg_file).get(appid)
    return cfg_data
