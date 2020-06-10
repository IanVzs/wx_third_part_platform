# -*-coding: utf-8-*-

import json
import datetime

from log import *
from . import redis_api
from . import op


def save(dsp_str, data):
    insert_id = None
    if isinstance(data, str):
        dsp_str = dsp_str
        insert_id = redis_api.set_new(dsp_str, data)
        if not insert_id:
            logger.error("save error: key: {}, value: {}".format(dsp_str, data))
    elif isinstance(data, dict):
        fake_delete(dsp_str)
        insert_id = op.create_account_info(**data)
        if not insert_id:
            log_error("save error: key: {}, value: {}".format(dsp_str, str(data)))
    return insert_id


def fake_delete(appid: str) -> bool:
    sign = False
    info = read_info(appid)
    if info:
        sign = op.fake_delete_service_account_info(appid)
    else:
        sign = True
    return sign


def update_base_info(appid, nick_name, principal_name, qrcode_url):
    sign = op.update_base_info(appid, nick_name, principal_name, qrcode_url)
    if not sign:
        log_error("update_base_info error: appid: {}, nick_name: {}, principal_name: {}, qrcode_url: {}".format(
            appid, nick_name, principal_name, qrcode_url))
    return sign


def update_access_token(appid, data):
    authorizer_access_token = data["authorizer_access_token"]
    authorizer_refresh_token = data["authorizer_refresh_token"]
    expires_ts = data["expires_ts"]
    sign = op.update_access_token(appid, authorizer_access_token, authorizer_refresh_token, expires_ts)
    if not sign:
        log_error(
            "update_access_token error: appid: {}, authorizer_access_token: {}, authorizer_refresh_token: {}, expires_ts: {}"
            .format(appid, authorizer_access_token, authorizer_refresh_token, expires_ts))
    return sign


def unauthorized(appid):
    sign = False
    rlt_list = []
    rlt = op.fake_delete_service_account_info(appid)
    auth_account_list = op.select_auth_info_by_wx_appid(appid)
    for i in auth_account_list:
        _id = i["id"]
        _pre_auth_code = "unauthorized" + i["pre_auth_code"] + str(_id)
        _app_id = "unauthorized" + i["appid"] + str(_id)
        rlt2 = op.fake_delete_appid_map(_pre_auth_code, _app_id, _id)
        rlt_list.append(rlt2)

    sign = 0 not in rlt_list
    return sign, auth_account_list


def write2file(data_dict, _path):
    ori_data = read2dict(_path)
    data_dict = {**ori_data, **data_dict}
    with open(_path, 'w') as f:
        json.dump(data_dict, f, sort_keys=True, indent=4, ensure_ascii=False)
    return "Done"


def save_data(dsp_str, is_str):
    write2file({dsp_str: is_str}, "dao/auths.json")
    return 1


def read2dict(_path):
    with open(_path, 'r') as f:
        data_dict = json.load(f)
    return data_dict


def read_data(dsp_str):
    rsp_data = redis_api.get_value(dsp_str)
    if not rsp_data:
        log_error("read_data error: key: {}, value: {}".format(dsp_str, rsp_data))
    return rsp_data


def read_info(appid=None):
    # 获取授权公众号信息
    info_data = {}
    if appid:
        info_data = op.get_account_info(appid) or {}
    else:
        info_data = op.get_account_info() or {}
    if not info_data:
        log_error("read_info error: appid: {}, info_data: {}".format(str(appid), str(info_data)))
    return info_data


if __name__ == '__main__':
    save("ticket", "ticketsase")
    print(read_data("ticket"))
    print(read_data("ticket_updatime"))
