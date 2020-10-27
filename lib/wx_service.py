# -*-coding: utf-8-*-
"""
    微信服务号中业务功能，如，发送模板消息
"""

# ------------------------------------------------------

import json
import time
import random
import string
import hashlib
import requests
import datetime
from lib import config as lib_config
import urllib.parse


def check_access_token(func):
    def wrapper(self, *args, **kwargs):
        time_now = datetime.datetime.now()
        if time_now < self.access_token_expired_time:
            return func(self, *args, **kwargs)
        else:
            self.get_access_token(self.mode)
            self.format_url()
            return func(self, *args, **kwargs)

    return wrapper


class WeChat_OAP():
    def __init__(self, mode, appid=None):
        self.mode = mode
        if self.mode == "self_service" and (not appid):
            self.app_id = lib_config.WXAPPID
            self.appsecret = lib_config.AppSecret
        elif self.mode == "third_part_platform" and appid:
            self.app_id = appid
        else:
            log_error("WeChat_OAP init error. mode is {}, appid is {}".format(self.mode, str(appid)))
        self.ret = {'nonceStr': '', 'jsapi_ticket': '', 'timestamp': 0, 'url': ''}

        self.mini_app_ID = lib_config.MINI_APP_ID
        self.url_unde_get_access_token = lib_config.URL_GET_ACCESS_TOKEN
        self.url_unde_post_send_template_msg = lib_config.URL_POST_SEND_TEMPLATE_MSG
        self.url_unde_get_template_list = lib_config.URL_GET_TEMPLATE_LIST
        self.url_unde_get_openID_list = lib_config.URL_GET_OPENID_LIST
        self.url_unde_get_user_s_info = lib_config.URL_GET_USER_S_INFO
        self.url_unde_post_bind = lib_config.URL_POST_BIND
        self.url_unde_post_create_menu = lib_config.URL_POST_CREATE_MENU
        self.url_unde_get_get_menu = lib_config.URL_GET_MENU
        self.url_unde_get_cur_self_menu = lib_config.URL_GET_CUR_SELF_MENU
        self.url_unde_post_send_custom_msg = lib_config.URL_SEND_CUSTOM
        self.url_unde_get_med_gui_qrcode = lib_config.URL_GET_QRCODE_TICKET
        self.url_unde_get_jsapi_ticket = lib_config.URL_GET_JSAPI_TICKET
        self.access_token_expired_time = datetime.datetime(1988, 1, 1)

    def __create_nonce_str(self):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(15))

    def __create_timestamp(self):
        return int(time.time())

    def get_access_token(self, mode, appid=None):
        """
        明文传输，服务号本身使用appid和appsecret进行更新
        """
        """
        # 第三方平台自身维护，访问预留的刷新令刷新接口
        """
        if self.mode == "self_service":
            app_id = self.app_id
            appsecret = self.appsecret
            self.url_get_access_token = self.url_unde_get_access_token.format(app_id, appsecret)
            rsp = requests.request("GET", self.url_get_access_token)
            expires_in = rsp.json().get('expires_in')  # 凭证有效时长
            self.access_token = rsp.json().get('access_token')  # 接口调用凭证
            if self.access_token:
                log_info("updated access_token for wechat_oap")
            else:
                log_error("updated access_token failed, the appid is {}, appsecret is {}".format(appid, appsecret))
        elif self.mode == "third_part_platform":
            self.access_token = dao_wxapi.read_info(self.app_id)["authorizer_access_token"]
        self.access_token_expired_time = datetime.datetime.now() + datetime.timedelta(minutes=30)
        return self.access_token

    def format_url(self):
        self.url_post_send_template_msg = self.url_unde_post_send_template_msg.format(self.access_token)
        self.url_get_template_list = self.url_unde_get_template_list.format(self.access_token)
        self.url_get_openID_list = self.url_unde_get_openID_list.format(self.access_token, '')
        self.url_post_bind = self.url_unde_post_bind.format(self.access_token)
        # 从该用户开始获取(每次拉取限数量，所以分批次)
        self.url_post_create_menu = self.url_unde_post_create_menu.format(self.access_token)
        self.url_get_menu = self.url_unde_get_get_menu.format(self.access_token)
        self.url_get_cur_self_menu = self.url_unde_get_cur_self_menu.format(self.access_token)
        self.url_post_send_custom_msg = self.url_unde_post_send_custom_msg.format(self.access_token)
        self.url_get_med_gui_qrcode = self.url_unde_get_med_gui_qrcode.format(self.access_token)
        self.url_get_jsapi_ticket = self.url_unde_get_jsapi_ticket.format(self.access_token)

    @check_access_token
    def get_open_id_list(self):
        rsp_get_openID_list = requests.request("GET", self.url_get_openID_list).json()
        """
        openID 在字典`openid`字段中
        其余含：`total`, `count`, `data`{`openid :type list`, `next_openid`}
        """
        return rsp_get_openID_list

    def get_open_id(self):
        open_id = "owzB5wEaS2Hm1V50DU031Rr1B9zE"  # nikename: Ian
        # open_id = "owzB5wHnT7bpyv7MPzxJru4V0gCQ"  # nickname: 霍华荣
        return open_id

    @check_access_token
    def get_user_s_info(self, open_id):
        self.url_get_user_s_info = self.url_unde_get_user_s_info.format(self.access_token, open_id)
        rsp_user_s_info = requests.request("GET", self.url_get_user_s_info)
        user_s_info = rsp_user_s_info.json()
        return user_s_info

    def get_user_base_info(self, data):
        open_id = data.get("FromUserName")
        base_info = None
        if open_id:
            try:
                base_info = self.get_user_s_info(open_id)
            except Exception as err:
                base_info = None
        return base_info

    @check_access_token
    def get_template_list(self):
        rsp_get_template_list = requests.request("GET", self.url_get_template_list).json()
        template_list = rsp_get_template_list['template_list']
        """
        列表中template元素为字典，
        key有`template_id`, `title`, `primary_industry`, `deputy_industry`,
            `content :type dict`, `example`
        """
        """
        数据 说明
        参数    是否必填    说明
        touser  是  接收者openid
        template_id 是  模板ID
        url 否  模板跳转链接（海外帐号没有跳转能力）
        miniprogram 否  跳小程序所需数据，不需跳小程序可不用传该数据
        appid   是  所需跳转到的小程序appid（该小程序appid必须与发模板消息的公众号是绑定关联关系，暂不支持小游戏）
        pagepath    否  所需跳转到小程序的具体页面路径，支持带参数,（示例index?foo=bar），要求该小程序已发布，暂不支持小游戏
        data    是  模板数据
        color   否  模板内容字体颜色，不填默认为黑色
        """
        return template_list

    def get_template_id(self):
        template_list = self.get_template_list()
        template_id = template_list[1]["template_id"]  # 获取模版ID
        return template_id

    @check_access_token
    def send_custom_msg(self, data):
        rsp_data = requests.post(url=self.url_post_send_custom_msg, data=json.dumps(data, ensure_ascii=False).encode())
        log_info("send_custom_msg: inputs: [POST, url: {}, json: {}], outputs: [rsp_json: {}],".format(
            self.url_post_send_custom_msg, str(data), str(rsp_data.json())))
        return rsp_data

    @check_access_token
    def send_template_msg(self, data):
        rsp_data = {}
        rsp_send_template_msg = requests.request("POST", self.url_post_send_template_msg, json=data)
        log_info("send_template_msg: inputs: [POST, url: {}, json: {}], outputs: [rsp_json: {}],".format(
            self.url_post_send_template_msg, data, rsp_send_template_msg.json()))
        msgid = rsp_send_template_msg.json().get("msgid")
        if not msgid:
            errcode = rsp_send_template_msg.json().get("errcode")
            errmsg = rsp_send_template_msg.json().get("errmsg")
            msgid = errmsg
            log_error("template_msg send failed, wx_errcode: {}, errmsg: {} token_time: {}".format(
                errcode, errmsg, self.access_token_expired_time))
            # TODO
            if "template_id" in errmsg:
                template_invalid_warning = {
                    "wechat_appid": self.app_id,
                    "template_id": data.get("template_id"),
                    "error": errmsg,
                    "msg": "该模板失效, 请相关人员立即核实!!"
                }
                log_error(f'logstash###wx_third_part_platform###WARNING###{template_invalid_warning}')
            self.access_token_expired_time = datetime.datetime(1988, 1, 1)
            rsp_data = {"status": 1, "msg": errmsg}
        else:
            rsp_data = {"status": 0, "msg": msgid}
        return rsp_data

    def do_fusion_menu(self, pre_data, data):
        fail = []
        rsp = {"status": 1, "msg": ''}
        action = data.get("action")
        menu = {}
        if action == "create":
            menu = data.get("menu_data")  # dict
            rsp["status"] = 1
            rsp = {**rsp, **{"menu": menu}}
        elif action == "add":
            pos = data.get("pos")  # list(int) [一级, 二级]
            sub = data.get("sub_data")  # dict
            if len(pre_data["menu"]["button"]) < pos[0]:
                # 已有一级菜单小于期望位置， 则新增
                pre_data["menu"]["button"].append(sub)
                menu = pre_data
                rsp["status"] = 0
                rsp = {**rsp, **menu}
            else:
                pre_sub = pre_data["menu"]["button"][pos[0] - 1]["sub_button"]
                if len(pre_sub) < pos[1]:
                    pre_sub.append(sub)
                else:
                    pre_sub.insert(pos[1] - 1, sub)
                menu = pre_data
                rsp["status"] = 0
                rsp = {**rsp, **menu}
        elif action == "replace":
            pos = data.get("pos")  # list(int) [一级, 二级]
            sub = data.get("sub_data")  # dict
            if len(pre_data["menu"]["button"]) < pos[0]:
                rsp["msg"] = "num out range!"
                fail.append(rsp["msg"])
            else:
                pre_sub = pre_data["menu"]["button"][pos[0] - 1]["sub_button"]
                if len(pre_sub) < pos[1]:
                    rsp["msg"] = "num out range!"
                    fail.append(rsp["msg"])
                else:
                    pre_sub.insert(pos[1] - 1, sub)
                    pre_data["menu"]["button"][pos[0] - 1]["sub_button"] = pre_sub[:pos[1]] + pre_sub[pos[1] + 1:]
                    menu = pre_data
                    rsp["status"] = 0
                    rsp = {**rsp, **menu}
        return fail, rsp

    def do_create_menu(self, url, data):
        fail = []
        rsp_data = {}

        pre_menu = self.get_menu()
        if not pre_menu.get("status"):
            fail, new_menu = self.do_fusion_menu(pre_menu.get("data"), data)
            if not fail:
                self.url_post_create_menu = url
                rsp_create_menu_msg = requests.post(
                    self.url_post_create_menu, data=json.dumps(new_menu.get("menu"), ensure_ascii=False).encode())
                log_info("create_menu: inputs: [POST, url: {}, json: {}], outputs: [rsp_json: {}],".format(
                    self.url_post_create_menu, new_menu, rsp_create_menu_msg.json()))
                errcode = rsp_create_menu_msg.json().get("errcode")
                if errcode:
                    errcode = rsp_create_menu_msg.json().get("errcode")
                    errmsg = rsp_create_menu_msg.json().get("errmsg")
                    log_error("create menu failed, wx_errcode: {}, errmsg: {} token_time: {}".format(
                        errcode, errmsg, self.access_token_expired_time))
                    self.access_token_expired_time = datetime.datetime(1988, 1, 1)
                    rsp_data = {"status": 1, "msg": errmsg}
                    fail.append(errmsg)
                else:
                    rsp_data = {"status": 0, "msg": "ok"}
            else:
                rsp_data = new_menu
        else:
            rsp_data = pre_menu
            fail.append(rsp_data.get("msg"))
        return fail, rsp_data

    @check_access_token
    def create_menu(self, data):
        rsp_data = self.do_create_menu(self.url_post_create_menu, data)
        return rsp_data

    def do_get_menu(self, url, test=False):
        fail = []
        rsp_data = {}
        self.url_get_menu = url
        rsp_get_menu_msg = requests.request("GET", self.url_get_menu)
        log_info("get_menu: inputs: url:{}, outputs: rsp_get_menu_msg: {}".format(self.url_get_menu,
                                                                                  rsp_get_menu_msg.json()))
        errcode = rsp_get_menu_msg.json().get("errcode")
        if errcode:
            errcode = rsp_get_menu_msg.json().get("errcode")
            errmsg = rsp_get_menu_msg.json().get("errmsg")
            log_error("get menu failed, wx_errcode: {}, errmsg: {} token_time: {}".format(
                errcode, errmsg, self.access_token_expired_time))
            self.access_token_expired_time = datetime.datetime(1988, 1, 1)
            rsp_data = {"status": 1, "msg": errmsg}
            fail.append(errmsg)
        else:
            rsp_data = {"status": 0, "msg": "ok", "data": rsp_get_menu_msg.json()}
        return fail, rsp_data

    @check_access_token
    def get_menu(self):
        """ret: {"status": 0, "msg": "ok", "data": {"menu": {"button": [] } } }"""
        fail, rsp_data = self.do_get_menu(self.url_get_menu)
        return rsp_data

    def do_get_cur_self_menu(self, url, test=False):
        fail = []
        rsp_data = {}
        self.url_get_cur_self_menu = url
        rsp_get_menu_msg = requests.request("GET", self.url_get_cur_self_menu)
        rsp_get_menu_msg = rsp_get_menu_msg.json()
        log_info("get_cur_self_menu: inputs: url:{}, outputs: rsp_get_menu_msg: {}".format(
            self.url_get_menu, rsp_get_menu_msg))
        errcode = rsp_get_menu_msg.get("errcode")
        if errcode:
            errcode = rsp_get_menu_msg.get("errcode")
            errmsg = rsp_get_menu_msg.get("errmsg")
            log_error("get menu failed, wx_errcode: {}, errmsg: {} token_time: {}".format(
                errcode, errmsg, self.access_token_expired_time))
            self.access_token_expired_time = datetime.datetime(1988, 1, 1)
            rsp_data = {"status": 1, "msg": errmsg}
            fail.append(errmsg)
        else:
            new_menu_data = {}
            if rsp_get_menu_msg.get("is_menu_open") and rsp_get_menu_msg.get("selfmenu_info"):
                new_menu_data["menu"] = {"button": []}
                for _md in (rsp_get_menu_msg["selfmenu_info"].get("button") or []):
                    sub_button = []
                    if "sub_button" in _md:
                        _md["sub_button"] = _md["sub_button"]["list"]
                    new_menu_data["menu"]["button"].append(_md)
            rsp_data = {"status": 0, "msg": "ok", "data": new_menu_data}
        return fail, rsp_data

    @check_access_token
    def get_cur_self_menu(self):
        fail, rsp_data = self.do_get_cur_self_menu(self.url_get_cur_self_menu)
        return rsp_data

    def do_get_med_gui_qrcode(self, url, scene_str):
        rsp_data = {"sign": 0, "msg": ''}
        if scene_str == "Get_My_Info":
            action_name = "QR_STR_SCENE"
        else:
            action_name = "QR_LIMIT_STR_SCENE"
        data = {
            "expire_seconds": 604800,
            "action_name": action_name,
            "action_info": {
                "scene": {
                    "scene_str": scene_str or "Get_Med_Gui"
                }
            }
        }
        rsp_get_qrcode = requests.request("POST", url, json=data)
        json_data = rsp_get_qrcode.json()
        if "ticket" in json_data:
            rsp_data["qrcode_url"] = "https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket={}".format(json_data["ticket"])
            rsp_data["sign"] = 1
        else:
            rsp_data["msg"] = "get qrcode error."
        return rsp_data

    @check_access_token
    def get_med_gui_qrcode(self, scene_str):
        rsp_data = self.do_get_med_gui_qrcode(self.url_get_med_gui_qrcode, scene_str)
        return rsp_data

    def get_signature(self, jsapi_ticket, url):
        self.ret["jsapi_ticket"] = jsapi_ticket
        decoded_url = urllib.parse.unquote(url)
        log_info("get_signature: %s %s" % (url, decoded_url))
        self.ret["url"] = decoded_url
        self.ret["timestamp"] = self.__create_timestamp()
        self.ret["nonceStr"] = self.__create_nonce_str()
        string = '&'.join(['%s=%s' % (key.lower(), self.ret[key]) for key in sorted(self.ret)])
        self.ret['signature'] = hashlib.sha1(string.encode()).hexdigest()
        return self.ret

    @check_access_token
    def get_jsapi_ticket(self):
        rsp_data = requests.get(self.url_get_jsapi_ticket).json()
        jsapi_ticket = rsp_data.get("ticket") or ""
        log_info("Get_Jsapi_Ticket", rsp_data)
        return jsapi_ticket


if __name__ == '__main__':
    app_id = "testhospital"
    open_id = wechat_oap.get_open_id()
    user_id = "215"
    user_s_info = wechat_oap.get_user_s_info(open_id)

    template_id = wechat_oap.get_template_id()
    template_data = wechat_oap.get_data_for_template(open_id, app_id, user_id, template_id, None)
    rsp_send_template_msg = wechat_oap.send_template_msg(template_data)
    print(rsp_send_template_msg.json())
    print("All Done!")
