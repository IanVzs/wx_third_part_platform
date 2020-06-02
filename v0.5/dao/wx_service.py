# -*-coding: utf-8-*-

import json
import time

from log import *
from . import redis_api
from . import op


def save(data: dict) -> dict:
    insert_id = None
    rsp_dict = {"sign": 0, "msg": ''}
    insert_id = op.create_appid_map(**data)
    if insert_id:
        rsp_dict = {"sign": 1, "msg": insert_id}
    if insert_id == "retry":
        if not data.get("pre_auth_code"):
            data["pre_auth_code"] = "_placeholder_" + str(time.time())
        rsp_dict_del = fake_delete_appid_map(data.get("app_id"), data.get("pre_auth_code"))
        if not rsp_dict_del["msg"] == "CANCEL":
            insert_id = 1
        else:
            insert_id = op.create_appid_map(**data)
        if insert_id:
            rsp_dict = {"sign": 1, "msg": insert_id}
    else:
        rsp_dict["msg"] = "insert appid_map failed."
        log_error("insert appid_map failed, data: {}".format(str(data)))
    return rsp_dict


def update_auth_info(data: dict) -> dict:
    insert_id = None
    rsp_dict = {"sign": 0, "msg": ''}
    if data.get("pre_auth_code") and data.get("wechat_appid") and not data.get("appid"):
        # 根据pre_auth_code 填充授权信息
        rlt_del = fake_delete_appid_map('', data.get("pre_auth_code"))
        if rlt_del.get("sign") and rlt_del.get("appid"):
            data["appid"] = rlt_del["appid"]
            rsp_dict = save(data)
            log_info("update_auth_info|save: data:{}, rsp_dict: {}".format(str(data), str(rsp_dict)))
        elif rlt_del.get("sign"):
            rsp_dict["msg"] = "update_auth_info|match failed." + rlt_del["msg"]
            log_error(rsp_dict["msg"] +
                      "Finded info: pre_auth_code: {}, rlt_del: {}".format(data.get("pre_auth_code"), str(rlt_del)))
        else:
            rsp_dict = rlt_del
    elif data.get("wechat_appid") and not data.get("pre_auth_code"):
        # 根据wechat_appid更新授权信息
        if op.select_auth_info_by_wx_appid(data.get("wechat_appid")):
            # 更新
            rsp_dict = update(data.get("wechat_appid"), data.get("nick_name"), data.get("auth_info"))
        else:
            # 从service_account_info表迁移.
            data["appid"] = data["pre_auth_code"] = "_placeholder_" + str(time.time())
            rsp_dict = save(data)
    else:
        # 其他
        if data.get("wechat_appid") == "waa111asdw43f3b5":
            # 测试
            rlt_del = fake_delete_appid_map('', data.get("pre_auth_code"))
            if rlt_del.get("sign"):
                data["appid"] = rlt_del["appid"]
                rsp_dict = save(data)
            else:
                rsp_dict = rlt_del
        else:
            rsp_dict["msg"] = "input para error"
    return rsp_dict


def fake_delete_service_account_info(app_id: str) -> dict:
    rsp_dict = {"sign": 0, "msg": ''}
    rlt_info = get_auth_info(app_id)
    if rlt_info.get("sign"):
        _id = rlt_info.get("id")
        _app_id = rlt_info.get("appid") + '_' + str(_id)
        _pre_auth_code = pre_auth_code + '_' + str(_id)
        rlt = op.fake_delete_appid_map(_pre_auth_code, _app_id, _id)
        if rlt:
            rsp_dict["sign"] = 1
            rsp_dict["appid"] = rlt_info.get("appid")
        else:
            rsp_dict["msg"] = "fake_delete_service_account_info|delete duplicate failed."
            log_error(rsp_dict["msg"] + "Finded info: appid: {}, rlt_info: {}".format(app_id, str(rlt_info)))
    else:
        rsp_dict["sign"] = 1
        rsp_dict["msg"] = "not found"

    return rsp_dict


def fake_delete_appid_map(app_id: str, pre_auth_code: str) -> dict:
    """
    para app_id
    para pre_auth_code
    """
    rsp_dict = {"sign": 0, "msg": ''}
    rlt_info = get_auth_info(app_id, pre_auth_code)
    if rlt_info.get("sign"):
        _id = rlt_info.get("id")
        _app_id = rlt_info.get("appid") + '_' + str(_id)
        _pre_auth_code = pre_auth_code + '_' + str(_id)
        _auth_info = rlt_info.get("auth_info") or ''
        if not _auth_info:
            rlt = op.fake_delete_appid_map(_pre_auth_code, _app_id, _id)
            if rlt:
                rsp_dict["sign"] = 1
                rsp_dict["appid"] = rlt_info.get("appid")
            else:
                rsp_dict[
                    "msg"] = "fake_delete_appid_map|delete duplicate failed." + "Finded info: appid: {}, pre_auth_code: {}, rlt_info: {}".format(
                        app_id, pre_auth_code, str(rlt_info))
                log_error(rsp_dict["msg"])
        else:
            rsp_dict["sign"] = 0
            rsp_dict["msg"] = "CANCEL"
    else:
        rsp_dict["sign"] = 1
        rsp_dict["msg"] = "not found"

    return rsp_dict


def update(wechat_appid: str, nick_name: str, auth_info: dict) -> dict:
    rsp_dict = {"sign": 0, "msg": ''}
    rlt = op.update_auth_info(wechat_appid, nick_name, auth_info)
    rsp_dict["sign"] = 1
    return rsp_dict


def get_auth_info(app_id: str, pre_auth_code: str = '') -> dict:
    """
    para: app_id ::左开appid
    para: pre_auth_code ::预授权码
    find by app_id or pre_auth_code
    """
    rsp_dict = {"sign": 0, "msg": ''}
    rlt = op.get_auth_info(app_id, pre_auth_code)
    if rlt:
        if isinstance(rlt, list) and len(rlt) == 1:
            rlt = rlt[0]
        elif isinstance(rlt, list) and len(rlt) != 1:
            rsp_dict["msg"] = "get_auth_info num not expect."
            return rsp_dict
        rsp_dict["sign"] = 1
        rsp_dict = {**rsp_dict, **rlt}
    else:
        rsp_dict["msg"] = "not found."
    return rsp_dict


def get_all_auth_appid():
    """
    获取全部的授权账号appid
    """
    ret_list = []
    rlt = op.get_all_auth_appid()
    for info_obj in rlt:
        appid = info_obj["appid"]
        if appid:
            ret_list.append(appid)
    return ret_list


def get_app_id_by_wechat_id(wechat_appid):
    rlt = op.get_app_id_by_wechat_id(wechat_appid)
    app_id = ''
    for i in rlt:
        if i["appid"] and isinstance(i["appid"], str) and len(i["appid"]) == 12:
            # 该长度为appid的长度
            app_id = i["appid"]
            break
    return app_id


def get_nick_name_by_wechat_id(wechat_appid):
    rlt = op.get_app_id_by_wechat_id(wechat_appid)
    app_id = ''
    nick_name = ''
    for i in rlt:
        if i["appid"] and isinstance(i["appid"], str) and len(i["appid"]) == 24:
            nick_name = i["nick_name"]
            break
    return nick_name


def real_delete_by(appid: str, pre_auth_code: str):
    rlt = None
    rlt = op.real_delete_by(appid, pre_auth_code)
    return rlt


def save_user_base_info(base_info):
    # 存储用户基本信息
    save_base_info = {}
    for save_key in ("wechat_appid", "nickname", "openid", "subscribe", "sex", "language", "city", "province",
                     "country", "headimgurl", "unionid", "remark", "groupid", "subscribe_time", "subscribe_scene",
                     "qr_scene", "qr_scene_str"):
        save_base_info[save_key] = base_info.get(save_key) or ''
    save_base_info["all_info"] = json.dumps(base_info, ensure_ascii=False)
    insert_id = op.create_user_base_info(**save_base_info)
    return insert_id


def get_user_base_info(appid: str, data):
    """查询用户基本信息"""
    user_s_info = op.get_user_base_info(appid, data)
    return user_s_info


def update_user_base_info_status_by_openid(appid, open_id, data):
    """
    更新用户基本信息
    
    关注、取关状态更新
    """
    item_values = ''
    for _key, _value in data.items():
        if _key not in ("subscribe", "status"):
            continue
        item_values = item_values + f'{_key} = {_value}, '
    if item_values:
        item_values = item_values[:-2]
        update_num = op.update_user_base_info_by_openid(appid, open_id, item_values)
    else:
        update_num = 0
    return update_num


def update_user_base_info_subScene_qrStr_by_openid(appid, open_id, data):
    """
    更新用户基本信息

    关注途径更新
    """
    item_values = ''
    for _key, _value in data.items():
        if _key not in ("subscribe_scene", "qr_scene_str"):
            continue
        item_values = item_values + f'{_key} = "{_value}", '
    if item_values:
        item_values = item_values[:-2]
        update_num = op.update_user_base_info_by_openid(appid, open_id, item_values)
    else:
        update_num = 0
    return update_num
