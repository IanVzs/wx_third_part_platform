# -*-coding: utf-8-*-
"""对外请求api"""

import json
import requests

from log import logger
from helper import config


def request_parser_helper(api, params, timeout=10000, format_="json", method="POST"):
    """请求总通道"""
    js_out = None
    try:
        if method == "GET":
            response = requests.request("GET", api, params=params, timeout=timeout)
        elif format_ == "json":
            response = requests.post(api, json=params, timeout=timeout)
        elif format_ == "form":
            response = requests.post(api, data=params, timeout=timeout)
        else:
            raise Exception("request_parser_helper: not valid format")
        if response.status_code == 200:
            js_out = response.json()
            if js_out.get("status") != 0:
                logger.error("request_parser: [api:%s] [input:%s] [output:%s]" %
                             (api, json.dumps(params, ensure_ascii=False), json.dumps(js_out, ensure_ascii=False)))
        else:
            logger.error("request_parser http error %s" % response.text)
        api_js = {"api": api, "js_out": js_out}
        logger.debug(f'API_AND_RETURN|{api_js}')
        return js_out
    except Exception as err_msg:
        logger.error(f'err_msg: {err_msg}')
        return


def get_WH_para(params):
    """
    威海，通过fpid换取pid.
    已更换方案，将此模块移至前端处理
    """
    api_root = config.emmm_HOST
    resp = request_parser_helper(api_root + "/emr/fpid", params, timeout=config.PARSER_TIMEOUT, method="GET")
    if resp and resp["status"] == 0:
        return resp


def get_hos_cfg(appid):
    """
    获取组织部落配置，模板消息内容、小程序跳转页面等项
    """
    api_root = config.emmm_HOST
    params = {"appid": appid, "cfg_name": "wx_third_platform"}
    resp = request_parser_helper(
        api_root + "/service_setting/pull", params, timeout=config.PARSER_TIMEOUT, method="GET")
    if resp and resp["status"] == 0:
        return resp


def get_doctor_info(doctor_id):
    """
    获取医师信息
    """
    api_root = config.WYS_HOST
    params = {}
    resp = request_parser_helper(api_root + "/internal/doctor/{}".format(doctor_id), params, timeout=0.5, method="GET")
    if resp and resp["status"] == 0:
        return resp


def get_patient_info(union_id):
    """
    获取患者信息
    """
    api_root = config.WYS_HOST
    params = {}
    resp = request_parser_helper(api_root + "/internal/patient/{}".format(union_id), params, timeout=0.5, method="GET")
    if resp and resp["status"] == 0:
        return resp
