# -*-coding: utf-8-*-

import pymysql

from . import db
from log import *
from . import config


def create_account_info(**kwargs):
    keys = []
    values = []
    for key, value in kwargs.items():
        keys.append('`%s`' % key)
        values.append(value)
    keys = ','.join(keys)
    query = 'insert into service_account_info(%s) values (%s)' % (keys, ','.join(len(values) * ['%s']))
    params = tuple(values)
    row_id = db.mysql_conn.insert_and_get_id(query, params)
    logger.debug("new_account_info:%s %s %s" % (query, str(params), row_id))
    return row_id


def update_access_token(appid, authorizer_access_token, authorizer_refresh_token, expires_ts):
    rlt = None
    query = 'update service_account_info set authorizer_access_token = %s, authorizer_refresh_token = %s, expires_ts = %s where appid = %s'
    params = (authorizer_access_token, authorizer_refresh_token, expires_ts, appid)
    rlt = db.mysql_conn.execute_once(query, params)
    logger.debug("update_access_token: %s %s %s" % (query, str(params), str(rlt)))
    return rlt


def update_base_info(appid, nick_name, principal_name, qrcode_url):
    rlt = None
    query = 'update service_account_info set nick_name = %s, principal_name = %s, qrcode_url = %s where appid = %s'
    params = (nick_name, principal_name, qrcode_url, appid)
    rlt = db.mysql_conn.execute_once(query, params)
    logger.debug("update_base_info: %s %s %s" % (query, str(params), str(rlt)))
    return rlt


def get_account_info(appid=None):
    if appid:
        query = 'select * from service_account_info where appid = %s and status = 1'
        params = (appid, )
        rlt = db.mysql_conn.fetch_one(query, params)
    else:
        query = 'select * from service_account_info where status = 1'
        params = ()
        rlt = db.mysql_conn.fetch_all(query, params)
    logger.debug("get_account_info: %s %s %s" % (query, str(params), str(rlt)))
    return rlt


def get_all_auth_appid():
    query = "select distinct(appid) from service_account_info"
    params = ()
    rlt = db.mysql_conn.fetch_all(query, params) or ()
    logger.debug("get_all_auth_appid: %s %s %s" % (query, str(params), str(rlt)))
    return rlt


def create_appid_map(**kwargs):
    keys = []
    values = []
    for key, value in kwargs.items():
        keys.append('`%s`' % key)
        values.append(value)
    keys = ','.join(keys)
    query = 'insert into appid_map(%s) values (%s)' % (keys, ','.join(len(values) * ['%s']))
    params = tuple(values)
    try:
        row_id = db.mysql_conn.insert_and_get_id(query, params)
        logger.debug("create_appid_map:%s %s %s" % (query, str(params), row_id))
    except Exception as e:
        if e.__class__.__name__ == "IntegrityError":
            row_id = "retry"
        else:
            row_id = None
    return row_id


def fake_delete_service_account_info(app_id):
    rlt = None
    query = 'update service_account_info set status = 0 where appid = %s and status = 1'
    params = (app_id, )
    rlt = db.mysql_conn.execute_once(query, params)
    logger.debug("fake_delete_service_account_info: %s %s %s" % (query, str(params), str(rlt)))
    return rlt


def fake_delete_appid_map(_pre_auth_code, _app_id, _id):
    rlt = None
    query = 'update appid_map set status = 0, pre_auth_code = %s, appid = %s where id = %s'
    params = (_pre_auth_code, _app_id, _id)
    rlt = db.mysql_conn.execute_once(query, params)
    logger.debug("fake_delete_appid_map: %s %s %s" % (query, str(params), str(rlt)))
    return rlt


def get_auth_info(appid='', pre_auth_code=''):
    if appid or pre_auth_code:
        if appid and pre_auth_code:
            query = 'select * from appid_map where (appid = %s and pre_auth_code = %s) and status = 1'
            params = (appid, pre_auth_code)
        elif appid:
            query = 'select * from appid_map where appid = %s and status = 1'
            params = (appid, )
        elif pre_auth_code:
            query = 'select * from appid_map where pre_auth_code = %s and status = 1'
            params = (pre_auth_code, )
        rlt = db.mysql_conn.fetch_one(query, params)
    else:
        query = 'select * from appid_map where status = 1'
        params = ()
        rlt = db.mysql_conn.fetch_all(query, params)
    logger.debug("get_auth_info: %s %s %s" % (query, str(params), str(rlt)))
    return rlt


def get_app_id_by_wechat_id(wechat_appid):
    query = 'select appid, nick_name from appid_map where wechat_appid = %s and status = 1'
    params = (wechat_appid, )
    rlt = db.mysql_conn.fetch_all(query, params)
    logger.debug(": %s %s %s" % (query, str(params), str(rlt)))
    return rlt


def update_auth_info(wechat_appid, nick_name, auth_info):
    query = 'update appid_map set wechat_appid = %s, nick_name = %s, auth_info = %s where wechat_appid = %s and status = 1'
    params = (wechat_appid, nick_name, auth_info, wechat_appid)
    rlt = db.mysql_conn.execute_once(query, params)
    logger.debug("update_auth_info: %s %s %s" % (query, str(params), str(rlt)))
    return rlt


def select_auth_info_by_wx_appid(wechat_appid):
    query = 'select * from appid_map where wechat_appid = %s and status = 1'
    params = (wechat_appid, )
    rlt = db.mysql_conn.fetch_all(query, params)
    logger.debug("select_auth_info_by_wx_appid: %s %s %s" % (query, str(params), str(rlt)))
    return rlt


def real_delete_by(appid, pre_auth_code):
    query = 'delete from appid_map where appid = %s or pre_auth_code = %s'
    params = (appid, pre_auth_code)
    rlt = db.mysql_conn.execute_once(query, params)
    logger.debug("real_delete_by: %s %s %s" % (query, str(params), str(rlt)))
    return rlt


def create_user_base_info(**kwargs):
    keys = []
    values = []
    for key, value in kwargs.items():
        keys.append('`%s`' % key)
        values.append(value)
    keys = ','.join(keys)
    query = 'insert into user_base_info(%s) values (%s)' % (keys, ','.join(len(values) * ['%s']))
    params = tuple(values)
    try:
        row_id = db.mysql_conn.insert_and_get_id(query, params)
        logger.debug("create_user_base_info:%s %s %s" % (query, str(params), row_id))
    except Exception as e:
        # TODO
        row_id = None
    return row_id


def get_user_base_info(appid, data):
    rlt = None
    if appid:
        query = 'select nickname, openid, unionid, qr_scene_str from user_base_info where wechat_appid = %s and {} = %s and status = 1'
        query = query.format(list(data.keys())[0])
        params = (appid, list(data.values())[0])
        rlt = db.mysql_conn.fetch_one(query, params)
    logger.debug("get_user_base_info: %s %s %s" % (query, str(params), str(rlt)))
    return rlt


def update_user_base_info_by_openid(appid, open_id, item_values):
    update_num = 0
    query = f'update user_base_info set {item_values} where wechat_appid = %s and openid = %s'
    params = (appid, open_id)
    update_num = db.mysql_conn.execute_once(query, params)
    logger.debug("update_user_base_info_by_openid: %s %s %s" % (query, str(params), str(item_values)))
    return update_num
