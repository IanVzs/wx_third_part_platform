# -*-coding: utf-8-*-

import json
import datetime
import requests
from flask import Blueprint, jsonify, abort, request, make_response
from flask import Response, render_template

import config
from log import *
from lib import access, authorization, access2, wx_workers
from lib.wx_service import WeChat_OAP
from lib.monitor import WechatOffAccPlatformMonitor
from dao import wx_api as dao_wxapi
from dao import wx_service as dao_wxservice
from helper.authorization_info import all_info
from . import wx_api as blue_wxapi

WXSERVICE = Blueprint('wxservice', __name__)


@WXSERVICE.route('/wx_service/send_template_msg', methods=['POST'])
#@profiler.profileit
def send_template_msg():
    log_info('', request)
    wrapped = None
    inputs = {}
    try:
        inputs = request.get_json()
    except ValueError as e:
        log_error("error parasing input", e)
    if inputs:
        log_info("POST INPUT", inputs)
        app_id = inputs.get("app_id")  # 组织部落在微信处的appid
        data = inputs.get("data")  # 模板数据
        wechat_oap = WeChat_OAP("third_part_platform", app_id)

        msg_data = wechat_oap.send_template_msg(data)
        if msg_data.get("status"):
            wrapped = {
                "status": msg_data.get("status"),
                "message": msg_data.get("msg"),
            }
        else:
            wrapped = {
                "status": 0,
                "message": "请求成功",
            }
    if not wrapped:
        wrapped = {
            "status": 1,
            "message": "请求失败",
        }
    log_info("WRAPPED", wrapped)
    resp = make_response(jsonify(wrapped))
    return resp


@WXSERVICE.route('/wx_service/get_auth_access_token', methods=['POST', 'GET'])
#@profiler.profileit
def get_auth_access_token():
    log_info('', request)
    wrapped = None
    inputs = {}
    try:
        if request.method == "POST":
            inputs = request.get_json()
        elif request.method == "GET":
            inputs["app_id"] = request.args.get("app_id")
    except ValueError as e:
        log_error("error parasing input", e)
    if inputs:
        log_info("POST INPUT", inputs)
        app_id = inputs.get("app_id")  # 组织部落在微信处的appid
        read_info_dict = dao_wxapi.read_info(app_id)
        if isinstance(read_info_dict, dict):
            auth_access_token = read_info_dict.get("authorizer_access_token")
        else:
            auth_access_token = 'null'
        wrapped = {"status": 0, "message": "请求成功", "data": {"auth_access_token": auth_access_token}}
    if not wrapped:
        wrapped = {"status": 1, "message": "请求失败", "data": {}}
    log_info("WRAPPED", wrapped)
    resp = make_response(jsonify(wrapped))
    return resp


@WXSERVICE.route('/wx_service/get_menu', methods=['POST', 'GET'])
#@profiler.profileit
def get_menu():
    log_info('', request)
    wrapped = None
    rsp = {"sign": 0, "msg": ""}
    inputs = {}
    try:
        if request.method == "POST":
            inputs = request.get_json()
        elif request.method == "GET":
            inputs["app_id"] = request.args.get("app_id")
            inputs["cur_self"] = request.args.get("cur_self") or ''
            # 另调用一个查询接口(可查询公众号后台配置)
    except ValueError as e:
        log_error("error parasing input", e)
    if inputs:
        log_info("POST INPUT", inputs)
        app_id = inputs.get("app_id")  # 组织部落在微信处的appid
        if app_id:
            event_data = {"Event": "create", "EventKey": "Get_Menu", "Data": inputs.get("cur_self") or ''}
            rsp = wx_workers.wx_event(app_id, event_data)
            if rsp.get("sign"):
                wrapped = {"status": 0, "message": "请求成功", "data": {**rsp, "ok": 1}}
            else:
                wrapped = {"status": 0, "message": rsp.get("msg"), "data": {"ok": 0}}
        else:
            wrapped = {"status": 1, "message": "缺少必要参数", "data": {"sign": 0, "msg": "app_id"}}
    if not wrapped:
        wrapped = {"status": 1, "message": "请求失败", "data": {"ok": 0}}
    log_info("WRAPPED", wrapped)
    resp = make_response(jsonify(wrapped))
    return resp


@WXSERVICE.route('/wx_service/create_menu', methods=['POST'])
#@profiler.profileit
def create_menu():
    """
    :para  app_id ::type str
    :para  data ::type dict
    app_id 微信appid，为必须传入
    data 自定义菜单详情可选传入(POST支持)
    """
    log_info('', request)
    wrapped = None
    rsp = {"sign": 0, "msg": ""}
    inputs = {}
    try:
        if request.method == "POST":
            inputs = request.get_json()
        elif request.method == "GET":
            inputs["app_id"] = request.args.get("app_id")
    except ValueError as e:
        log_error("error parasing input", e)
    if inputs:
        log_info("POST INPUT", inputs)
        app_id = inputs.get("app_id")  # 组织部落在微信处的appid
        if app_id:
            # 调取lib 方法，生成自定义菜单(get从本地配置读取，post支持上传菜单详情)
            event_data = {"Event": "create", "EventKey": "Crt_Menu", "Data": inputs.get("data")}
            rsp = wx_workers.wx_event(app_id, event_data)
            wrapped = {"status": 0, "message": "请求成功", "data": {"ok": rsp.get("sign"), "msg": rsp.get("msg")}}
        else:
            wrapped = {"status": 1, "message": "缺少必要参数", "data": {"ok": 0, "msg": "app_id"}}
    if not wrapped:
        wrapped = {"status": 1, "message": "请求失败", "data": {"ok": 0}}
    log_info("WRAPPED", wrapped)
    resp = make_response(jsonify(wrapped))
    return resp


@WXSERVICE.route('/wx_service/get_user_info', methods=['POST', 'GET'])
#@profiler.profileit
def get_user_info():
    """
    :para  app_id ::type str
    :para  open_id ::type str
    :para  union_id ::type str
    app_id 微信appid，为必须传入, open_id、union_id自选
    """
    log_info('', request)
    wrapped = None
    rsp = {"sign": 0, "msg": ""}
    inputs = {}
    try:
        if request.method == "POST":
            inputs = request.get_json()
        elif request.method == "GET":
            inputs["app_id"] = request.args.get("app_id")
            inputs["open_id"] = request.args.get("open_id")
            inputs["union_id"] = request.args.get("union_id")
    except ValueError as e:
        log_error("error parasing input", e)
    if inputs:
        log_info("POST INPUT", inputs)
        app_id = inputs.get("app_id")  # 组织部落在微信处的appid
        open_id = inputs.get("open_id")
        union_id = inputs.get("union_id")
        if app_id and open_id:
            # 调取lib 方法，生成自定义菜单(get从本地配置读取，post支持上传菜单详情)
            event_data = {"Event": "from_api", "EventKey": "Get_User_Info", "Data": inputs}
            rsp = wx_workers.wx_event(app_id, event_data)
            wrapped = {"status": 0, "message": "请求成功", "data": rsp}
        elif app_id and union_id:
            rsp = dao_wxservice.get_user_base_info(app_id, {"unionid": union_id}) or rsp
            if rsp and rsp.get("nickname"):
                rsp["sign"] = 1
                rsp["msg"] = ""
            else:
                rsp["msg"] = "该用户未关注公众号"
            wrapped = {"status": 0, "message": "请求成功", "data": rsp}
        else:
            wrapped = {"status": 1, "message": "缺少必要参数", "data": {"ok": 0, "msg": "app_id"}}
    if not wrapped:
        wrapped = {"status": 1, "message": "请求失败", "data": {"ok": 0}}
    log_info("WRAPPED", wrapped)
    resp = make_response(jsonify(wrapped))
    return resp


def do_get_auth_url(inputs: dict, test: bool = False) -> (list, dict):
    fail = []
    wrapped = {}
    log_info("POST INPUT", inputs)
    app_id = inputs.get("app_id")
    if app_id:
        # 调取blueprints 方法，生成授权URL
        from_ = "wx_service"
        auth_rsp = blue_wxapi.auth(from_)
        # 存入数据库占位, 授权完成后调取信息补位
        if auth_rsp.get("pre_auth_code") and auth_rsp.get("url_auth") or test:
            placeholder = {"pre_auth_code": auth_rsp.get("pre_auth_code"), "appid": app_id, "nick_name": "_placeholder"}
            save_rst = dao_wxservice.save(placeholder)
            if save_rst["sign"]:
                wrapped = {
                    "status": 0,
                    "message": "请求成功",
                    "data": {
                        "ok": auth_rsp.get("sign"),
                        "msg": '',
                        "url_auth": auth_rsp.get("url_auth")
                    }
                }
            else:
                fail.append(save_rst["msg"])
    else:
        fail.append("para: loss app_id")
    return fail, wrapped


@WXSERVICE.route('/wx_service/get_auth_url', methods=['POST', 'GET'])
#@profiler.profileit
def get_auth_url():
    """
    :para  app_id ::type str ::desc 唉,医者自医appid
    """
    log_info('', request)
    wrapped = None
    rsp = {"sign": 0, "msg": ""}
    inputs = {}
    fail = []
    try:
        if request.method == "POST":
            inputs = request.get_json()
        elif request.method == "GET":
            inputs["app_id"] = request.args.get("app_id")
    except ValueError as e:
        log_error("error parasing input", e)
    if inputs:
        fail, wrapped = do_get_auth_url(inputs)
    if not wrapped:
        wrapped = {"status": 1, "message": ", ".join(fail), "data": {"ok": 0}}
    log_info("WRAPPED", wrapped)
    resp = make_response(jsonify(wrapped))
    return resp


def do_get_auth_info(inputs: dict, test: bool = False) -> (dict, list):
    def deal_msg(authorizer_info, authorization_info):
        base_info = {}
        power_list = []
        all_power_list = []
        try:
            if authorizer_info:
                # base_info
                base_info["nick_name"] = authorizer_info["nick_name"]
                base_info["principal_name"] = authorizer_info["principal_name"].split("(")[0] if authorizer_info[
                    "principal_name"] else ''  # 删除主体名中的多余别名
                base_info["alias"] = authorizer_info["alias"]
                base_info["head_img"] = authorizer_info.get("head_img") or ''
                base_info["service_type_info"] = all_info["authorizer_info"]["service_type_info"][authorizer_info[
                    "service_type_info"]["id"]]  # 订阅、服务
                base_info["verify_type_info"] = all_info["authorizer_info"]["verify_type_info"][authorizer_info[
                    "verify_type_info"]["id"]]  # 认证

                if "牛肉大王" in base_info["principal_name"]:
                    base_info["principal_name"] = "牛肉丸子"
            if authorization_info:
                # power_list
                base_info["wechat_appid"] = authorization_info.get("authorizer_appid") or ''
                for ii in authorization_info["func_info"]:
                    if ii["funcscope_category"]["id"] in all_info["authorization_info"][authorizer_info[
                            "service_type_info"]["id"]]:
                        power_list.append(all_info["authorization_info"][authorizer_info["service_type_info"]["id"]][ii[
                            "funcscope_category"]["id"]])
                    else:
                        error_dict = {
                            "key":
                            ii["funcscope_category"]["id"],
                            "service_type_info":
                            all_info["authorizer_info"]["service_type_info"][authorizer_info["service_type_info"]["id"]]
                        }
                        log_error(f'LOSS_POWER_DICT|{error_dict}')
                if authorizer_info["service_type_info"]["id"] in all_info["authorization_info"]:
                    all_power_list = [
                        iii
                        for iii in all_info["authorization_info"][authorizer_info["service_type_info"]["id"]].values()
                    ]
                else:
                    all_power_list = ["num", authorizer_info["service_type_info"]["id"]]
        except Exception as e:
            error_dict = {
                "authorization_info": authorization_info,
                "authorizer_info": authorizer_info,
                "all_info": all_info,
                "e": e
            }
            log_error(f'translate info error|{error_dict}')

        return base_info, power_list, all_power_list

    fail = []
    wrapped = {}
    log_info("POST INPUT", inputs)
    app_id = inputs.get("app_id")
    if app_id:
        auth_info_dict = dao_wxservice.get_auth_info(app_id)
        if auth_info_dict.get("sign"):
            # 从数据库中获取授权信息
            auth_info_all = auth_info_dict.get("auth_info")
            if auth_info_all:
                info_dict_data = json.loads(auth_info_all)
                authorizer_info = info_dict_data.get("authorizer_info") or ''
                authorization_info = info_dict_data.get("authorization_info") or ''
                base_info, power_list, all_power_list = deal_msg(authorizer_info, authorization_info)
                wrapped = {
                    "status": 0,
                    "message": "请求成功",
                    "data": {
                        "ok": 1,
                        "authorizer_info": base_info,
                        "authorization_info": power_list,
                        "all_power_info": all_power_list,
                        "msg": "完成授权",
                    },
                }
            else:
                wrapped = {
                    "status": 0,
                    "message": "请求成功",
                    "data": {
                        "ok": 0,
                        "msg": "未完成授权操作",
                    },
                }
        else:
            fail.append(auth_info_dict.get("msg"))
    else:
        fail.append("para: loss app_id")
    return fail, wrapped


@WXSERVICE.route('/wx_service/get_auth_info', methods=['POST', 'GET'])
#@profiler.profileit
def get_auth_info():
    """
    :para app_id ::type str ::desc 唉,医者自医appid
    """
    log_info('', request)
    wrapped = None
    rsp = {"sign": 0, "msg": ""}
    inputs = {}
    fail = []
    try:
        if request.method == "POST":
            inputs = request.get_json()
        elif request.method == "GET":
            inputs["app_id"] = request.args.get("app_id")
            inputs["iszsjk"] = request.args.get("iszsjk")
        if inputs.get("iszsjk") and inputs.get("app_id") == "5234asf3e45eavb 24dad8":
            # FUCK THIS MAP
            inputs["app_id"] = "zuoyijiankang_todo_appid"
    except ValueError as e:
        log_error("error parasing input", e)
    if inputs:
        fail, wrapped = do_get_auth_info(inputs)
    if not wrapped:
        wrapped = {"status": 1, "message": ", ".join(fail), "data": {"ok": 0}}
    log_info("WRAPPED", wrapped)
    resp = make_response(jsonify(wrapped))
    return resp


def do_exchange(inputs: dict, test: bool = False) -> (list, dict):
    fail = []
    wrapped = {}
    log_info("POST INPUT", inputs)
    app_id = inputs.get("app_id")
    if app_id:
        auth_info_dict = dao_wxservice.get_auth_info(app_id)
        if auth_info_dict.get("sign"):
            # 从数据库中获取授权信息
            wechat_appid = auth_info_dict.get("wechat_appid")
            if wechat_appid:
                wrapped = {
                    "status": 0,
                    "message": "请求成功",
                    "data": {
                        "ok": 1,
                        "wechat_appid": wechat_appid,
                        "msg": "完成授权",
                    },
                }
            else:
                wrapped = {
                    "status": 0,
                    "message": "请求成功",
                    "data": {
                        "ok": 0,
                        "msg": "未完成授权操作",
                    },
                }
        else:
            fail.append(auth_info_dict.get("msg"))
    else:
        fail.append("para: loss app_id")

    return fail, wrapped


@WXSERVICE.route('/wx_service/exchange', methods=['POST', 'GET'])
#@profiler.profileit
def exchange():
    """
    :para app_id ::type str ::desc 唉,医者自医appid
    """
    log_info('', request)
    wrapped = None
    rsp = {"sign": 0, "msg": ""}
    inputs = {}
    fail = []
    try:
        if request.method == "POST":
            inputs = request.get_json()
        elif request.method == "GET":
            inputs["app_id"] = request.args.get("app_id")
    except ValueError as e:
        log_error("error parasing input", e)
    if inputs:
        fail, wrapped = do_exchange(inputs)
    if not wrapped:
        wrapped = {"status": 1, "message": ", ".join(fail), "data": {"ok": 0}}
    log_info("WRAPPED", wrapped)
    resp = make_response(jsonify(wrapped))
    return resp


@WXSERVICE.route('/wx_service/refresh_info', methods=['POST', 'GET'])
#@profiler.profileit
def refresh_info():
    """
    :para app_id ::type str ::desc 唉,医者自医appid
    """
    log_info('', request)
    wrapped = None
    rsp = {"sign": 0, "msg": ""}
    inputs = {}
    fail = []
    update_list = authorization.refresh_info()
    if not wrapped:
        wrapped = {"status": 0, "message": "请求成功", "data": {"ok": 1, "msg": "更新完成", "update_list": update_list}}
    log_info("WRAPPED", wrapped)
    resp = make_response(jsonify(wrapped))
    return resp


@WXSERVICE.route('/wx_service/refresh_hos_config', methods=['POST', 'GET'])
#@profiler.profileit
def refresh_hos_config():
    """
    :para appid ::type str ::desc 微信appid
    """
    log_info('', request)
    wrapped = None
    rsp = {"sign": 0, "msg": ""}
    inputs = {}
    try:
        if request.method == "POST":
            inputs = request.get_json()
        elif request.method == "GET":
            # wechat appid
            inputs["appid"] = request.args.get("appid") or ''
    except ValueError as e:
        log_error("error parasing input", e)
    appid = inputs.get("appid") or ''
    new_cfg_data = wx_workers.update_hos_config(appid)
    if not wrapped:
        wrapped = {"status": 0, "message": "请求成功", "data": {"ok": 1, "msg": "更新完成", "config_data": new_cfg_data}}
    log_info("WRAPPED", wrapped)
    resp = make_response(jsonify(wrapped))
    return resp


@WXSERVICE.route('/wx_service/get_qrcode', methods=['POST', 'GET'])
#@profiler.profileit
def get_qrcode():
    log_info('', request)
    wrapped = None
    rsp = {"sign": 0, "msg": ""}
    inputs = {}
    try:
        if request.method == "POST":
            inputs = request.get_json()
        elif request.method == "GET":
            inputs["app_id"] = request.args.get("app_id") or ''
            inputs["scene_str"] = request.args.get("scene_str") or ''
    except ValueError as e:
        log_error("error parasing input", e)
    if inputs:
        log_info("POST INPUT", inputs)
        app_id = inputs.get("app_id")  # 组织部落在微信处的appid
        if app_id:
            # 调取lib 方法，生成自定义菜单(get从本地配置读取，post支持上传菜单详情)
            event_data = {"Event": "create", "EventKey": "Get_Menu_QrCode", "Data": inputs}
            rsp = wx_workers.wx_event(app_id, event_data)
            if rsp.get("sign"):
                wrapped = {"status": 0, "message": "请求成功", "data": {**rsp, "ok": 1}}
            else:
                wrapped = {"status": 0, "message": rsp.get("msg"), "data": {"ok": 0}}
        else:
            wrapped = {"status": 1, "message": "缺少必要参数", "data": {"sign": 0, "msg": "app_id"}}
    if not wrapped:
        wrapped = {"status": 1, "message": "请求失败", "data": {"ok": 0}}
    log_info("WRAPPED", wrapped)
    resp = make_response(jsonify(wrapped))
    return resp


@WXSERVICE.route('/wx_service/send_mini_card', methods=['POST', 'GET'])
#@profiler.profileit
def send_mini_card():
    log_info('', request)
    wrapped = None
    rsp = {"sign": 0, "msg": ""}
    inputs = {}
    try:
        if request.method == "POST":
            inputs = request.get_json()
        elif request.method == "GET":
            inputs["title"] = request.args.get("title") or ''
            inputs["app_id"] = request.args.get("app_id") or ''
            inputs["open_id"] = request.args.get("open_id") or ''
            inputs["pagepath"] = request.args.get("pagepath") or ''
            inputs["thumb_media_id"] = request.args.get("thumb_media_id") or ''
    except ValueError as e:
        log_error("error parasing input", e)
    if inputs:
        log_info("POST INPUT", inputs)
        app_id = inputs.get("app_id")  # 组织部落在微信处的appid
        if app_id:
            # 调取lib 方法，生成自定义菜单(get从本地配置读取，post支持上传菜单详情)
            event_data = {"Event": "from_api", "EventKey": "Send_Mini_Card", "Data": inputs}
            rsp = wx_workers.wx_event(app_id, event_data)
            if rsp.get("sign"):
                wrapped = {"status": 0, "message": "请求成功", "data": {**rsp, "ok": 1}}
            else:
                wrapped = {"status": 0, "message": rsp.get("msg"), "data": {"ok": 0}}
        else:
            wrapped = {"status": 1, "message": "缺少必要参数", "data": {"sign": 0, "msg": "app_id"}}
    if not wrapped:
        wrapped = {"status": 1, "message": "请求失败", "data": {"ok": 0}}
    log_info("WRAPPED", wrapped)
    resp = make_response(jsonify(wrapped))
    return resp


@WXSERVICE.route('/wx_service/get_signature', methods=['GET', 'POST'])
#@profiler.profileit
def get_signature():
    """
    :para  app_id ::type str
    :para  data ::type dict
    app_id 微信appid，为必须传入
    data 预留, 或作signature 生成限制参数
    """
    log_info('', request)
    wrapped = None
    rsp = {"sign": 0, "msg": ""}
    inputs = {}
    calllback = ''
    try:
        if request.method == "POST":
            inputs = request.get_json()
        elif request.method == "GET":
            inputs["app_id"] = request.args.get("app_id")
            calllback = request.args.get("callback") or ''
            inputs["data"] = json.loads(request.args.get("data") or "{}")
            url = request.args.get("url")
    except ValueError as e:
        log_error("error parasing input", e)
    log_info(f'Jsonp_Request||{str(requests.__dict__)}')
    if inputs:
        inputs["data"]["url"] = url or inputs["data"].get("url")
        log_info("POST INPUT", inputs)
        app_id = inputs.get("app_id")  # 组织部落在微信处的appid
        if app_id:
            # 调取lib 方法，生成自定义菜单(get从本地配置读取，post支持上传菜单详情)
            event_data = {"Event": "from_api", "EventKey": "Get_Signature", "Data": inputs.get("data")}
            rsp = wx_workers.wx_event(app_id, event_data)
            wrapped = {
                "status": 0,
                "message": "请求成功",
                "data": {
                    "ok": rsp.get("sign"),
                    "msg": rsp.get("msg"),
                    "ret": rsp.get("ret")
                }
            }
        else:
            wrapped = {"status": 1, "message": "缺少必要参数", "data": {"ok": 0, "msg": "app_id"}}
    if not wrapped:
        wrapped = {"status": 1, "message": "请求失败", "data": {"ok": 0}}
    if calllback:
        wrapped_jsonp = f'{calllback}({json.dumps(wrapped)})'
        return wrapped_jsonp
    log_info("WRAPPED", wrapped)
    resp = make_response(jsonify(wrapped))
    return resp


@WXSERVICE.route('/wx_service/check_account_menu', methods=['GET', 'POST'])
#@profiler.profileit
def check_account_menu():
    """
    检查公众号菜单状态， 是否我方配置按钮正常
    """
    log_info('', request)
    wrapped = None
    status_list = WechatOffAccPlatformMonitor.menu_monitor_status()
    wrong_list = []
    for menu_status in status_list:
        if menu_status["status"]:
            wrong_list.append(menu_status)
    wrapped = {
        "menu_status_list": wrong_list,
        "fix_url": "https://wx.zudqw2sweheng.com/wx_service/create_menu",
        "fix_doc": "http://wiki.zudqwdcsdcicsdng.com/docs/wx_third_part_platform/forevcwveqwne#fjqwjkd",
    }
    log_info("WRAPPED", wrapped)
    resp = make_response(jsonify(wrapped))
    return resp
