# -*-coding: utf-8-*-

import time
import json
import xmltodict
import requests
from flask import Flask, jsonify, abort, request, make_response

import config
from log import *
from dao import wx_api as dao_wxapi
from dao import wx_service as dao_wxservice
from lib import access as lib_access
from lib.send_log import send_log
from lib.monitor import WechatOffAccPlatformMonitor

appid = config.WXAPPID
appsecret = config.WXAPPSECRET


def request(methods, url, data):
    rsp = requests.request(methods, url, data=json.dumps(data))
    if rsp.status_code == 200:
        dict_data = rsp.json()
    else:
        dict_data = {}
        WechatOffAccPlatformMonitor.make_wrarning({
            "event_name": f'三方平台访问微信API错误 {methods}',
            "url": url,
            "data": json.dumps(data, ensure_ascii=False),
            "status_code": rsp.status_code,
            "rsp": str(rsp.__dict__)
        })
    log_info("WX_API request input_out  url: {}, data: {}, rsp: {}".format(url, json.dumps(data), str(dict_data)))
    return dict_data


def com_access_token():
    # 通过ticket 获取第三方接口调用凭据
    ticket = dao_wxapi.read_data("ticket")
    data = {"component_appid": appid, "component_appsecret": appsecret, "component_verify_ticket": ticket}
    url_com_access_token = config.URL_COM_ACCESS_TOKEN
    dict_data = request("POST", url_com_access_token, data)
    com_access_token = dict_data["component_access_token"]
    dao_wxapi.save("com_access_token", com_access_token)


def pre_auth_code():
    # 通过com_access_token获取预授权码
    com_access_token = dao_wxapi.read_data("com_access_token")
    data = {"component_appid": appid}
    url_pre_auth_code = config.URL_PRE_AUTH_CODE.format(com_access_token)
    dict_data = request("POST", url_pre_auth_code, data)
    pre_auth_code = dict_data.get("pre_auth_code") or ''
    if not pre_auth_code:
        log_error("pre_auth_code get failed: appid: {}, com_access_token: {}".format(appid, com_access_token))
    dao_wxapi.save("pre_auth_code", pre_auth_code)
    return pre_auth_code


def do_authorizer_access_token(dict_data: dict, auth_code: str, set_map: bool = True, test_data: dict = {}) -> dict:
    rsp_dict = {"sign": 0, "msg": ''}
    com_access_token = dao_wxapi.read_data("com_access_token")
    authorizer_appid = dict_data["authorization_info"]["authorizer_appid"]
    dao_wxapi.save("authorizer_appid", authorizer_appid)
    authorizer_access_token = dict_data["authorization_info"]["authorizer_access_token"]
    dao_wxapi.save("authorizer_access_token", authorizer_access_token)

    authorizer_refresh_token = dict_data["authorization_info"]["authorizer_refresh_token"]
    dao_wxapi.save("authorizer_refresh_token", authorizer_refresh_token)
    auth_ex = int(dict_data["authorization_info"]['expires_in'])

    # 顺便获取授权方的账号基本信息
    #头像、昵称、账号类型、认证类型、微信号、原始ID和二维码ＵＲＬ
    url_getinfo = config.URL_GETINFO.format(com_access_token)
    data_info = {"component_appid": appid, "authorizer_appid": authorizer_appid}
    info_dict_data = request("POST", url_getinfo, data_info)
    send_log("AuthorizationAccountInfoDetail:" + str(info_dict_data))
    auth_info_all = ''
    if ("authorizer_info" in info_dict_data) or test_data:
        if "authorizer_info" in test_data and "authorization_info" in test_data:
            info_dict_data = test_data
        auth_info_all = json.dumps(info_dict_data, ensure_ascii=False)
        auth_info = info_dict_data["authorizer_info"]
        nick_name = auth_info["nick_name"]
        service_type_info = int(auth_info["service_type_info"]["id"])
        verify_type_info = int(auth_info["verify_type_info"]["id"])
        user_name = auth_info["user_name"]
        principal_name = auth_info["principal_name"]
        qrcode_url = auth_info["qrcode_url"]
        expire_ts = int(time.time()) + auth_ex - 11 * 60
    else:
        nick_name = ''  # auth_info["nick_name"]
        service_type_info = ''  # int(auth_info["service_type_info"]["id"])
        verify_type_info = ''  # int(auth_info["verify_type_info"]["id"])
        user_name = ''  # auth_info["user_name"]
        principal_name = ''  # auth_info["principal_name"]
        qrcode_url = ''  # auth_info["qrcode_url"]
        expire_ts = 0
        log_error("获取信息失败: wxappid: {}, info_dict_data: {}".format(authorizer_appid, str(info_dict_data)))

    logger.info("获得授权方账号信息|%s|%s", nick_name, principal_name)
    if service_type_info != 2:  # 2 表示服务号
        logger.info("接入的公众号不是服务号|%s|%s", nick_name, principal_name)
    else:
        logger.info("接入的公众号是服务号|%s|%s", nick_name, principal_name)

    if verify_type_info == -1:
        logger.warning("接入的公众号未经认证|%s|%s", nick_name, principal_name)

    # 接入服务号到本服务器
    # 存储
    save_info_data = {
        "appid": authorizer_appid,
        "authorizer_access_token": authorizer_access_token,
        "authorizer_refresh_token": authorizer_refresh_token,
        "expires_ts": expire_ts,
        "nick_name": nick_name,
        "user_name": user_name,
        "principal_name": principal_name,
        "qrcode_url": qrcode_url,
    }
    insert_id = dao_wxapi.save(authorizer_appid, save_info_data)
    send_log("AuthorizationAccountSaveBaseInfo|insert_id: {}".format(str(insert_id)))
    if insert_id and set_map:
        # 基本信息插入成功，并且需要建立两方appid map
        pre_auth_code = dao_wxapi.read_data(auth_code) or ''
        log_info("get_pre_code_back: {}".format(auth_code))
        auth_info_data = {
            "pre_auth_code": pre_auth_code,
            "wechat_appid": authorizer_appid,
            "nick_name": nick_name,
            "auth_info": auth_info_all,
        }
        insert_id2_dict = dao_wxservice.update_auth_info(auth_info_data)
        send_log("AuthorizationAccountSaveInfoDetail|inser_dict: {}".format(str(insert_id2_dict)))
        if not insert_id2_dict.get("sign"):
            send_log("Authorized_Update_Map_Error")
            retry_appid = dao_wxapi.read_data(pre_auth_code) or pre_auth_code
            retry_auth_info_data = {
                "appid": retry_appid,
                "pre_auth_code": pre_auth_code,
                "wechat_appid": authorizer_appid,
                "nick_name": nick_name,
                "auth_info": auth_info_all,
            }
            send_log("Retry_Save: {}".format(str(retry_auth_info_data)), err=True)
            if retry_appid and authorizer_appid and pre_auth_code:
                # 删除占位，重新写入
                del_data1 = dao_wxservice.get_auth_info(retry_appid, '')
                del_data2 = dao_wxservice.get_auth_info('', pre_auth_code)
                send_log("Del_Data: del_data1: {}, del_data2: {}".format(str(del_data1), str(del_data2)), err=True)
                dao_wxservice.real_delete_by(retry_appid, pre_auth_code)
                dao_wxservice.save(retry_auth_info_data)
        if not insert_id2_dict.get("sign"):
            log_error(rsp_dict["msg"])
            rsp_dict["msg"] = "update_auth_info error. auth_info_data: {}".format(auth_info_data)
    if insert_id:
        # pre_auth_code, 一个预授权码，只能被一个公众号接入, 但blueprints中保证了每次都会新生成一个pre_auth_code
        rsp_dict["sign"] = 1

    return rsp_dict


def authorizer_access_token(auth_code, set_map=True):
    # 通过com_access_token获取公众号/小程序接口调用凭据/令牌
    # 以及刷新凭据/刷新令牌
    rsp_dict = {"sign": 0, "msg": ''}
    com_access_token = dao_wxapi.read_data("com_access_token")
    auth_code = auth_code  # dao_wxapi.read_data("auth_code")
    data = {"component_appid": appid, "authorization_code": auth_code}
    url_authorizer_access_token = config.URL_AUTHORIZER_ACCESS_TOKEN.format(com_access_token)
    dict_data = request("POST", url_authorizer_access_token, data)
    send_log("AuthorizationAccountInfo:" + str(dict_data))
    auth_info_all = ''
    if "authorization_info" in dict_data:
        # 授权信息
        rsp_dict = do_authorizer_access_token(dict_data, auth_code, set_map=set_map)
    else:
        rsp_dict["msg"] = "微信服务器故障: authorizer_info not in response"

    return rsp_dict


def unauthorized(authorizer_appid):
    # 取消授权
    rsp_dict = {"sign": 0, "msg": ''}
    rsp_dict["sign"], auth_account_list = dao_wxapi.unauthorized(authorizer_appid)
    if not rsp_dict["sign"]:
        rsp_dict["msg"] = "server busy, the authorization info will delete after minutes."
    send_log("UnAuthorizationInfo|appid: {}, auth_account_list: {}, rsp_dict: {}".format(
        authorizer_appid, str(auth_account_list), str(rsp_dict)))
    return rsp_dict


def refresh_token():
    # 通过com_access_token刷新公众号/小程序接口调用凭据/令牌
    # 刷新刷新令
    com_access_token = dao_wxapi.read_data("com_access_token")
    appid = config.WXAPPID
    user_info_list = dao_wxapi.read_info()
    for user_info in user_info_list:
        authorizer_appid = user_info["appid"]
        authorizer_refresh_token = user_info.get("authorizer_refresh_token")
        data = {
            "component_appid": appid,
            "authorizer_appid": authorizer_appid,
            "authorizer_refresh_token": authorizer_refresh_token
        }
        url_refresh_token = config.URL_REFRESH_TOKEN.format(com_access_token)
        dict_data = request("POST", url_refresh_token, data)
        if "authorizer_access_token" in dict_data:
            authorizer_access_token = dict_data["authorizer_access_token"]
            dao_wxapi.save("authorizer_access_token", authorizer_access_token)
            authorizer_refresh_token = dict_data["authorizer_refresh_token"]
            dao_wxapi.save("authorizer_refresh_token", authorizer_refresh_token)
            user_info_dict = {}
            user_info_dict["authorizer_access_token"] = authorizer_access_token
            user_info_dict["authorizer_refresh_token"] = authorizer_refresh_token
            user_info_dict["expires_ts"] = int(time.time()) + int(dict_data["expires_in"]) - 11 * 60

            dao_wxapi.update_access_token(authorizer_appid, user_info_dict)
        else:
            log_error("refresh_token error: {}".format(str(user_info)))

    logger.info("refresh_token Done")


def do_refresh_info(info_dict_data: dict, old_info: dict = {}) -> dict:
    """
    刷新appid_map表信息(《左手医生开放平台》&&《微信开放平台》的appid映射，以及各个appid为第三方平台的授权信息 )
    
    顺便刷新授权方的账号基本信息(有更改则刷新，无则跳过)
    头像、昵称、账号类型、认证类型、微信号、原始ID和二维码ＵＲＬ
    """
    rsp_dict = {"sign": 0, "msg": ''}
    authorizer_appid = info_dict_data.get("authorization_info").get("authorizer_appid") if info_dict_data.get(
        "authorization_info") else ''
    if "authorizer_info" in info_dict_data:
        auth_info_all = json.dumps(info_dict_data, ensure_ascii=False)
        auth_info = info_dict_data["authorizer_info"]
        nick_name = auth_info["nick_name"]
        service_type_info = int(auth_info["service_type_info"]["id"])
        user_name = auth_info["user_name"]
        principal_name = auth_info["principal_name"]
        qrcode_url = auth_info["qrcode_url"]
        expire_ts = 9999
    else:
        nick_name = ''  # auth_info["nick_name"]
        service_type_info = ''  # int(auth_info["service_type_info"]["id"])
        user_name = ''  # auth_info["user_name"]
        principal_name = ''  # auth_info["principal_name"]
        qrcode_url = ''  # auth_info["qrcode_url"]
        expire_ts = 0
        log_error("获取信息失败: info_dict_data: {}, ".format(str(info_dict_data)))

    logger.info("获得授权方账号信息|%s|%s", nick_name, principal_name)
    # 接入服务号到本服务器
    # 存储
    save_info_data = {
        "appid": authorizer_appid,
        "nick_name": nick_name,
        "principal_name": principal_name,
        "qrcode_url": qrcode_url,
    }
    if not authorizer_appid:
        save_info_data["appid"] = old_info["appid"]
    merge_info = {**old_info, **save_info_data}
    if old_info and merge_info != old_info:
        insert_id = dao_wxapi.update_base_info(**save_info_data)
        send_log("AuthorizationRefresh|BaseInfoMerge|old_info: {}, save_info_data: {}, insert_id: {}".format(
            str(old_info), str(save_info_data), str(insert_id)))
    elif not old_info:
        insert_id = dao_wxapi.update_base_info(**save_info_data)
    else:
        insert_id = True
    if insert_id:
        auth_info_data = {
            "wechat_appid": authorizer_appid,
            "nick_name": nick_name,
            "auth_info": auth_info_all,
        }
        insert_id2_dict = dao_wxservice.update_auth_info(auth_info_data)
        send_log("AuthorizationRefresh|DetailInfo|auth_info_data: {}, insert_id2_dict: {}".format(
            str(auth_info_data), str(insert_id2_dict)))
        if not insert_id2_dict.get("sign"):
            log_error(rsp_dict["msg"])
            rsp_dict["msg"] = "update_auth_info error. auth_info_data: {}".format(auth_info_data)
    else:
        insert_id2_dict = {"sign": 0, "msg": "save base info error."}
        rsp_dict = insert_id2_dict
    if insert_id and insert_id2_dict.get("sign"):
        # pre_auth_code, 一个预授权码，只能被一个公众号接入, 但blueprints中保证了每次都会新生成一个pre_auth_code
        rsp_dict["sign"] = 1

    return rsp_dict


def refresh_info():
    appid = config.WXAPPID
    user_info_list = dao_wxapi.read_info()
    update_list = []
    for user_info in user_info_list:
        # 循环获取授权方基本信息
        com_access_token = dao_wxapi.read_data("com_access_token")
        url_getinfo = config.URL_GETINFO.format(com_access_token)
        authorizer_appid = user_info["appid"]
        data_info = {"component_appid": appid, "authorizer_appid": authorizer_appid}
        info_dict_data = request("POST", url_getinfo, data_info)
        rsp_dict = do_refresh_info(info_dict_data, user_info)
        update_list.append({user_info["nick_name"]: rsp_dict})
    return update_list
