# -*-coding: utf-8-*-
"""微信事件处理"""

import json
import copy
import urllib
import datetime

import config
from log import log_error
from lib.wx_service import WeChat_OAP
from lib.send_log import send_log
from lib.track import track
from lib import config as lib_config, get_hos_cfg
from dao import wx_service as dao_wxservice
from helper import api as helper_api


def wx_event(appid: str, data: dict) -> dict:
    """事件处理"""
    try:
        nonce = data.get("nonce")
        rsp = {"sign": 0, "msg": ""}
        client_dict = get_maps("client_dict", {"fake_appid": config.DEBUG_LOG["fake_appid"]})
        client = client_dict.get(appid)
        if client:
            clienter = client(appid)
            if appid == "waa111asdw43f3b5":
                # 强制性修改特殊信息
                clienter.nickname = TEST_ZYClient(appid).nickname
                clienter.Get_This_Guy_values["template_id"] = TEST_ZYClient(appid).Get_This_Guy_values["template_id"]
                try:
                    clienter.Get_This_Guy_values["pagepath"] = client_dict.get(config.DEBUG_LOG["fake_appid"])(
                        config.DEBUG_LOG["fake_appid"]).Get_This_Guy_values["pagepath"]
                    send_log(f'CLIENTER_INFO||{clienter.config_data}')
                except Exception as e:
                    log_error(f'clienter.Get_This_Guy_values[pagepath] error {config.DEBUG_LOG["fake_appid"]}')
                clienter.thumb_media_id = TEST_ZYClient(appid).thumb_media_id
                if config.DEBUG_LOG["fake_appid"] != appid:
                    send_log(f'Get_This_Guy_values||{clienter.Get_This_Guy_values}')
            rsp = clienter.do_some(data)
        else:
            event = data.get("Event")
            no_client_log = {"nonce": nonce}
            send_log(f'wx_event|no_client|{no_client_log}')
            rsp["msg"] = f'{event} from_callback'
        if not rsp:
            rsp = {"sign": 0, "msg": "worker error."}
            worker_error_log = {"nonce": nonce}
            log_error(f'wx_event|worker_error|{worker_error_log}')
        return rsp
    except Exception as e:
        send_log(e.__class__.__name__ + str(e), err=True)
        return rsp


def get_app_id(appid):
    """通过微信appid， 获取这样才好app_id"""
    app_id = dao_wxservice.get_app_id_by_wechat_id(appid) or lib_config.MAP_TEMP_APPID.get(appid) or ''
    return app_id


def track_Get_This_Guy(event, appid, openid):
    """埋点"""
    propertie = {"app_id": get_app_id(appid), "openid": openid}
    track(event, propertie)


class TEST_ZYClient(object):
    """这样才好"""

    def __init__(self, appid):
        global HOS_CONFIG_DICT
        self.appid = appid
        self.config_data = HOS_CONFIG_DICT.get(appid)
        self.nickname = self.config_data.get("nickname") or "这样才好"
        self.mini_card_title = self.config_data.get("mini_card_title") or self.nickname + "就诊用药指导"
        self.Get_This_Guy_values = self.config_data.get("Get_This_Guy") or {
            "pagepath":
            "/pages/prescription/base_info/index?app_id=5c99b1a09ea2ea68c824dad8&hos_name={hos_name}&open_id={open_id}",
            "template_id":
            "20NLai49_QTA8GGcxrFgy-4DqLuSZ0ALaOWiRvZRkSY",
            "first":
            "获取用药指导报告",
            "keyword2":
            "这样才好，处方用药指导报告",
            "remark":
            "请遵循用药指导，科学用药，祝您早日康复！"
        }
        self.thumb_media_id = self.config_data.get("thumb_media_id") or "Qtz6eIuA6ES21K7LJWEZqN77koFShIDkp10vsI_u2J8"
        self.subscribe_txt = self.config_data.get("subscribe_txt") or '您好'
        self.subscribe_news = self.config_data.get("subscribe_news") or '1'
        self.save_user_info = 0
        self.wechat_oap = WeChat_OAP("third_part_platform", appid)

    def do_some(self, data: dict) -> dict:
        nonce = data.get("nonce")
        event_type = data.get("Event") or ''
        event_key = data.get("EventKey") or ''
        worker_key = event_key or event_type
        if "Get_This_Guy" in worker_key:
            worker_key = "Get_This_Guy"
        worker = self.get_worker(worker_key) or self.get_worker(self.sorter(worker_key, event_type))
        rsp = {"sign": 0, "msg": ""}
        err = False
        if not worker:
            rsp["msg"] = "不支持此功能"
            if self.nickname == "这样才好" and event_key and event_type != "view_miniprogram":
                err = True
            no_worker_log = {"hos_name": self.nickname, "event_type": event_type, "event_key": event_key, "data": data, "nonce": nonce}
            send_log(f'do_some|no_worker|{no_worker_log}', err=err)
        else:
            # 处理事件
            rsp = worker(data)
            worker_rsp_log = {"nonce": nonce, "worker_name": worker.__name__, "data": data, "rsp": rsp}
            send_log(f'do_some|worker_run|{worker_rsp_log}')
        return rsp

    def sorter(self, str_eventkey, event_type):
        """
        将无处理器的事件重新分类

        若事件包含关注事件,需在事件实现中手动执行关注和取关处理
        """
        new_worker_key = str_eventkey
        if "wys_" in str_eventkey:
            # 医务端，获取医师信息，发送小程序模板消息
            new_worker_key = "Medical_Matter"
        elif event_type in ("subscribe", "unsubscribe", "SCAN"):
            # 保证关注事件/取关事件被执行
            # 关注后重新扫描关注二维码
            new_worker_key = event_type + "_Re"
        return new_worker_key

    def get_worker(self, event_key):
        # 类型对照
        worker = None
        event_dict = {
            "Crt_Menu": self.create_menu,
            "Get_Menu": self.get_menu,
            "Get_Menu_QrCode": self.Get_This_Guy_qrcode,
            "Scan_Wait_Tem": self.scan_wait_tem,
            "Send_Mini_Card": self.send_mini_card,
            "Get_This_Guy": self.Get_This_Guy,
            "qrscene_Get_This_Guy": self.Get_This_Guy,
            "Get_My_Info": self.get_my_info,
            "qrscene_Get_My_Info": self.get_my_info,
            "subscribe": self.do_subscribe,
            "unsubscribe": self.do_unsubscribe,
            "subscribe_Re": self.do_subscribe,
            "unsubscribe_Re": self.do_unsubscribe,
            "Get_Signature": self.get_signature,
            "Get_User_Info": self.get_user_info,
            "Medical_Matter": self.medical_matter,
            "SCAN_Re": self.subscribe_scan,
        }
        worker = event_dict.get(event_key)
        return worker

    def get_signature(self, data):
        """生成 signature LP预问诊相关"""
        rsp = {"sign": 0, "msg": ""}
        para = data.get("Data") or {}
        url = para.get("url") or ''
        jsapi_ticket = self.wechat_oap.get_jsapi_ticket()
        signature = self.wechat_oap.get_signature(jsapi_ticket, url)
        if signature:
            rsp["sign"] = 1
            rsp = {"ret": signature, **rsp}
        else:
            rsp["msg"] = "generate signature error."
        return rsp

    def do_unsubscribe(self, data):
        """用户取消关注处理"""
        rsp = {"sign": 1, "msg": ''}
        open_id = data["FromUserName"]
        if "save_user_info" in self.__dict__:
            # 更改该用户状态为0
            update_num = dao_wxservice.update_user_base_info_status_by_openid(self.appid, open_id, {
                "status": 0,
                "subscribe": 0
            })
            if not update_num:
                failed_data = {"appid": self.appid, "openid": open_id, "update_data": {"status": 0, "subscribe": 0}}
                send_log(f'update_user_base_info_status_by_openid|{failed_data}')
                rsp["sign"] = 0
                rsp["msg"] = "do_unsubscribe|update_error"
        return rsp

    def do_subscribe(self, data):
        """用户关注事件处理"""
        open_id = data["FromUserName"]
        rsp = {"sign": 1, "msg": ''}
        if "save_user_info" in self.__dict__:
            # 存储用户基本信息
            # 1 获取
            user_base_info = self.get_user_info({"Data": {"open_id": open_id}})
            if user_base_info["sign"]:
                # 2 存储
                user_base_info["wechat_appid"] = self.appid
                send_log(
                    f"save_user_info in self.__dict__ after get user_base_info is {user_base_info} and sign is {user_base_info['sign']}"
                )
                insert_id = dao_wxservice.save_user_base_info(user_base_info)
                if not insert_id:
                    send_log(f"SAVE USER_INFO ERROR|{user_base_info}")

        # 关注事件回复
        if self.subscribe_txt:
            # 关注回复文字(客服消息 和直接回复两种模式，在微信方，都只能当作一次响应。为了图文，只好干掉客服消息回复，全部由直接回复)
            # c_data = {"touser": open_id, "msgtype": "text", "text": {"content": self.subscribe_txt}}
            # rsp_data = self.wechat_oap.send_custom_msg(c_data)
            # if rsp_data.json().get("errcode"):
            rsp = {"sign": 1, "msg": self.subscribe_txt, "reply_txt": 1}
        if self.subscribe_news:
            # 关注回复图文(优先于文字，所以非if:else, 而是覆盖| 或许可以给回复文字加个异步)
            rsp = {"sign": 1, "msg": '', "reply_news": 1}
        return rsp

    def subscribe_scan(self, data):
        """
        关注后,重新扫描关注二维码
        """
        rsp = {"sign": 1, "msg": ''}
        if "save_user_info" in self.__dict__:
            # 刷新存储有用户基本信息中的,关注来源
            open_id = data["FromUserName"]
            qr_scene_str = data["EventKey"]
            update_data = {"subscribe_scene": "ADD_SCENE_QR_CODE", "qr_scene_str": qr_scene_str}

            had_this_guy = dao_wxservice.get_user_base_info(self.appid, {"openid": open_id or ''})
            if had_this_guy:
                update_num = dao_wxservice.update_user_base_info_subScene_qrStr_by_openid(
                    self.appid, open_id, update_data)
            else:
                update_num = 0
            if not update_num and not had_this_guy:
                user_base_info = self.get_user_info({"Data": {"open_id": open_id}}, use_api=True)
                if user_base_info["sign"]:
                    user_base_info["wechat_appid"] = self.appid
                    user_base_info.update(update_data)
                    insert_id = dao_wxservice.save_user_base_info(user_base_info)
                    if not insert_id:
                        failed_data = {"appid": self.appid, "openid": open_id, "update_data": update_data}
                        send_log(f'update_user_base_info_subScene_qrStr_by_openid|{failed_data}')
                        rsp["sign"] = 0
                        rsp["msg"] = "subscribe_scan|update_error"
        return rsp

    def medical_matter(self, data):
        """医务端服务，扫描医师二维码后推送相应模板消息"""
        rsp = {"sign": 0, "msg": ""}
        event = data.get("Event") or ''
        touser = data.get("FromUserName")
        event_key = data.get("EventKey") or ''
        event_key_list = event_key.split("wys_")
        if event == "subscribe":
            # 将捕获的`subscribe`事件, 手动执行
            self.do_subscribe(data)
        if len(event_key_list) == 2 and ((event == "SCAN" and event_key_list[0] == '') or
                                         (event == "subscribe" and event_key_list[0] == "qrscene_")):
            doctor_info = helper_api.get_doctor_info(event_key_list[1]) or ''
            doctor_name = ''
            if doctor_info:
                doctor_name = doctor_info["doctor"]["name"]
                doctor_info = f'{doctor_info["doctor"]["hospital"]} {doctor_info["doctor"]["title"]} {doctor_name}'
            base_info = dao_wxservice.get_user_base_info(self.appid, {"openid": touser})
            union_id = base_info.get("unionid") if base_info.get("nickname") else ''
            patient_info = helper_api.get_patient_info(union_id) or {}
            if patient_info:
                patient_info = patient_info["patient"]
            wys_values = copy.deepcopy(self.config_data.get("Medical_Matter"))
            if wys_values:
                date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                patient_name = patient_info.get("name") or base_info.get("nickname") or ''
                qpath = "https://z1.fit/x?pid={doctor_id}&into_function=disease_management&get_phone=1".format(
                    doctor_id=event_key_list[1])
                qpath = urllib.request.quote(qpath)
                template_data = {
                    "touser": touser,
                    "template_id": wys_values.get("template_id"),
                    "url": "",
                    "miniprogram": {
                        "appid": "wxacd37ff25cd2ed6a",
                        "pagepath": wys_values.get("pagepath").format(q=qpath),
                    },
                    "data": {
                        "first": {
                            "value": wys_values.get("first")
                        },
                        "keyword1": {
                            "value": wys_values["keyword1"].format(doctor_info=doctor_info)
                        },
                        "keyword2": {
                            "value": wys_values["keyword2"].format(patient_name=patient_name),
                        },
                        "keyword3": {
                            "value": wys_values["keyword3"].format(doctor_name=doctor_name)
                        },
                        "keyword4": {
                            "value": wys_values["keyword4"].format(date_time=date_time)
                        },
                        "remark": {
                            "value": wys_values.get("remark")
                        }
                    }
                }
            msg_data = self.wechat_oap.send_template_msg(template_data)
            rsp["sign"] = 1
        else:
            rsp["msg"] = "不支持此功能"
        return rsp

    def scan_wait_tem(self, data):
        # 处理二维码扫描事件
        rsp = {"sign": 0, "msg": ""}
        scan_code_info = data.get("ScanCodeInfo")
        scan_type = scan_code_info.get("ScanType") or ''
        scan_result = scan_code_info.get("ScanResult") or ''
        touser = data.get("FromUserName")
        if scan_result and scan_type == "qrcode" and "?" in scan_result and "=" in scan_result:
            try:
                _a, para = scan_result.split("?")
                para_name, para_ = para.split("=")
                params = {
                    "fpid": para_,
                    "app_id": "5d21e7dw",
                }
                resp = helper_api.get_WH_para(params)
                # 请求flask, 获取参数。 拼接链接，发送小程序卡片
                if "result" in resp:
                    data_send = {
                        "touser": touser,
                        "wx_url": resp["result"].get("wx_url"),
                    }
                    rsp_send = self.send_mini_card(data_send)
                    rsp["sign"] = 1
                else:
                    rsp["msg"] = "request emr/fpid: error. params: {}".format(str(params))
            except:
                pass
        if not rsp.get("sign"):
            rsp["sign"] = 2  # 反馈提示语
            rsp["msg"] = "您好，请扫描组织部落收据单上的二维码，获取用药指导."
        return rsp

    def send_mini_card(self, data):
        rsp = {"sign": 0, "msg": ''}

        if "touser" in data.keys():
            c_data = {
                "touser": data.get("touser"),
                "msgtype": "miniprogrampage",
                "miniprogrampage": {
                    "title": self.mini_card_title,
                    "appid": "wxacd37ff25cd2ed6a",
                    "pagepath": data.get("wx_url"),
                    "thumb_media_id": self.thumb_media_id,
                }
            }
        elif "Data" in data.keys():
            c_data = {
                "touser": data["Data"].get("open_id"),
                "msgtype": "miniprogrampage",
                "miniprogrampage": {
                    "title": data["Data"].get("title"),
                    "appid": "wxacd37ff25cd2ed6a",
                    "pagepath": data["Data"].get("pagepath"),
                    "thumb_media_id": data["Data"].get("thumb_media_id"),
                }
            }
        rsp_data = self.wechat_oap.send_custom_msg(c_data)
        rsp["sign"] = 1
        return rsp

    def Get_This_Guy(self, data):
        # 获取用药指导, 发送模板消息
        send_log(f'Get_This_Guy||{self.Get_This_Guy_values}')
        rsp = {"sign": 0, "msg": ""}
        touser = data.get("FromUserName")
        pagepath = self.Get_This_Guy_values.get("pagepath")
        had_user_info = "save_user_info" in self.__dict__
        referrer = ''
        format_dict = {
            "hos_name": self.nickname,
            "open_id": touser,
        }
        if had_user_info and "referrer" in pagepath:
            referrer = self.get_user_info({"Data": {"open_id": touser}}).get("qr_scene_str")
            format_dict["referrer"] = referrer or ''
        pagepath = pagepath.format(**format_dict)
        template_data = {
            "touser": touser,
            "template_id": self.Get_This_Guy_values.get("template_id"),
            "url": "",
            "miniprogram": {
                "appid": "wxacd37ff25cd2ed6a",
                "pagepath": pagepath,
            },
            "data": {
                "first": {
                    "value": self.Get_This_Guy_values.get("value")
                },
                "keyword1": {
                    "value": "{}".format(datetime.datetime.now().strftime("%Y-%m-%d"))
                },
                "keyword2": {
                    "value": self.Get_This_Guy_values.get("keyword2"),
                    "color": "#ff8828"
                },
                "keyword3": {
                    "value": ""
                },
                "remark": {
                    "value": self.Get_This_Guy_values.get("remark")
                }
            }
        }
        custom_msg = {"touser": touser, "msgtype": "text", "text": {"content": "点击下方通知，查看你的用药指导"}}
        self.wechat_oap.send_custom_msg(custom_msg)
        msg_data = self.wechat_oap.send_template_msg(template_data)
        rsp["msg"] = msg_data.get("msg")
        if not msg_data.get("status"):
            rsp["sign"] = 1
            track_Get_This_Guy("wx_Get_This_Guy_count", self.appid, touser)
        return rsp

    def get_menu(self, data=None):
        rsp = {"sign": 0, "msg": ""}
        params = data.get("Data")
        if params:
            msg_data = self.wechat_oap.get_cur_self_menu()
        else:
            msg_data = self.wechat_oap.get_menu()
        if not msg_data.get("status"):
            rsp["sign"] = 1
            del msg_data["status"]
            rsp = {**msg_data, **rsp}
        else:
            rsp["msg"] = msg_data["msg"]
        return rsp

    def get_user_info(self, data=None, use_api=False):
        """获取微信用户信息"""
        rsp = {"sign": 0, "msg": ""}
        params = data.get("Data")
        if "save_user_info" in self.__dict__ and not use_api:
            # 存储有信息则以数据库为准
            msg_data = dao_wxservice.get_user_base_info(self.appid, {"openid": params.get("open_id") or ''})
            if not msg_data:
                msg_data = self.wechat_oap.get_user_s_info(params.get("open_id") or '')
        else:
            msg_data = self.wechat_oap.get_user_s_info(params.get("open_id") or '')
        if msg_data.get("nickname"):
            rsp["sign"] = 1
            rsp = {**msg_data, **rsp}
        else:
            rsp["msg"] = msg_data.get("errmsg") or ''
        return rsp

    def create_menu(self, data):
        menu_dict = data.get("Data")
        rsp = {"sign": 0, "msg": ""}
        if not menu_dict:
            rsp["msg"] = "miss menu data"
        else:
            fail, msg_data = self.wechat_oap.create_menu(menu_dict)
            rsp["msg"] = msg_data.get("msg")
            if not msg_data.get("status"):
                rsp["sign"] = 1
        return rsp

    def Get_This_Guy_qrcode(self, data) -> dict:
        qrcode_url_dict = {"sign": 0, "msg": ""}
        data = data.get("Data")
        scene_str = data.get("scene_str") or ''
        qrcode_url_dict = self.wechat_oap.Get_This_Guy_qrcode(scene_str)
        return qrcode_url_dict

    def get_my_info(self, data) -> dict:
        rsp = {"sign": 0, "msg": "Get_My_Info"}
        open_id = data.get("FromUserName")
        user_s_info = self.wechat_oap.get_user_s_info(open_id)
        rsp["sign"] = 1
        rsp["info"] = "subscribe: {}, nickname: {}, openid: {}".format(
            user_s_info.get("subscribe") or '',
            user_s_info.get("nickname") or '',
            user_s_info.get("openid") or '')
        c_data = {"touser": open_id, "msgtype": "text", "text": {"content": rsp["info"]}}
        rsp_data = self.wechat_oap.send_custom_msg(c_data)
        return rsp


class WHClient(TEST_ZYClient):
    # 文化保护组织部落
    def __init__(self, appid):
        global HOS_CONFIG_DICT
        self.appid = appid
        self.config_data = HOS_CONFIG_DICT.get(appid)
        self.subscribe_txt = self.config_data.get("subscribe_txt") or ''
        self.subscribe_news = self.config_data.get("subscribe_news") or ''
        self.nickname = self.config_data.get("nickname") or "文化保护组织部落"
        self.mini_card_title = self.config_data.get("mini_card_title") or self.nickname + "就诊用药指导"
        self.thumb_media_id = self.config_data.get("thumb_media_id") or "E447A0J974ZwYpSKGzZrqs91nQHjDFD1Dx2PjiFdh4E"
        self.wechat_oap = WeChat_OAP("third_part_platform", appid)


class TMClient(TEST_ZYClient):
    # 同煤
    def __init__(self, appid):
        global HOS_CONFIG_DICT
        self.appid = appid
        self.config_data = HOS_CONFIG_DICT.get(appid)
        self.subscribe_txt = self.config_data.get("subscribe_txt") or ''
        self.subscribe_txt = ''
        self.save_user_info = self.config_data.get("save_user_info") or 1
        self.subscribe_news = self.config_data.get("subscribe_news") or '1'
        self.nickname = self.config_data.get("nickname") or "她们的题目不会做总组织部落"
        self.template_data = self.config_data.get("Get_This_Guy")
        self.wechat_oap = WeChat_OAP("third_part_platform", appid)

    def Get_This_Guy(self, data):
        # 获取用药指导, 发送模板消息
        rsp = {"sign": 0, "msg": ""}
        touser = data.get("FromUserName")
        referrer = self.get_user_info({"Data": {"open_id": touser}}).get("qr_scene_str") or ''
        template_data = {
            "touser": touser,
            "template_id": "OxZYTHqvncGX-2O3s7c9h4vaiYlE2TovQGgohUPgWdI",
            "url": "",
            "miniprogram": {
                "appid":
                "wxacd37ff25cd2ed6a",
                "pagepath":
                "/pages/prescription/base_info/index?app_id=5cddqd352215&hos_name={}&open_id={}&stat_source=template_menu_click_message&referrer_doctor={}".
                format(self.nickname, touser, referrer)
            },
            "data": {
                "first": {
                    "value": "获取用药指导报告"
                },
                "keyword1": {
                    "value": "{}".format(datetime.datetime.now().strftime("%Y-%m-%d"))
                },
                "keyword2": {
                    "value": "同煤集团总组织部落，处方用药指导报告",
                    "color": "#ff8828"
                },
                "keyword3": {
                    "value": ""
                },
                "remark": {
                    "value": "请遵循用药指导，科学用药，祝您早日康复！"
                }
            }
        }
        custom_msg = {"touser": touser, "msgtype": "text", "text": {"content": "点击下方通知，查看你的用药指导"}}
        self.wechat_oap.send_custom_msg(custom_msg)
        msg_data = self.wechat_oap.send_template_msg(template_data)
        rsp["msg"] = msg_data.get("msg")
        if not msg_data.get("status"):
            rsp["sign"] = 1
            track_Get_This_Guy("wx_Get_This_Guy_count", self.appid, touser)
        if not rsp:
            log_error("wx_event: {}", str(rsp))
        return rsp


class DPClient(TEST_ZYClient):
    # 重庆火锅冷吃兔组织部落
    def __init__(self, appid):
        global HOS_CONFIG_DICT
        self.appid = appid
        self.config_data = HOS_CONFIG_DICT.get(appid)
        self.nickname = self.config_data.get("nickname") or "重庆火锅冷吃兔组织部落"
        self.subscribe_txt = self.config_data.get("subscribe_txt") or ''
        self.subscribe_news = self.config_data.get("subscribe_news") or ''
        self.mini_card_title = self.config_data.get("mini_card_title") or self.nickname + "就诊用药指导"
        self.Get_This_Guy_values = self.config_data.get("Get_This_Guy") or {
            "pagepath":
            "/pages/prescription/phone_name_base_info/index?app_id=5cdqw12b6dwqb&hos_name={hos_name}&open_id={open_id}",
            "template_id":
            "OcS6llkUXeRjd2IUoDWWlhVS6yH6sAX6Lb9GdtiQT_w",
            "first":
            "获取用药指导报告",
            "keyword2":
            "重庆火锅冷吃兔组织部落，处方用药指导报告",
            "remark":
            "请遵循用药指导，科学用药，祝您早日康复！"
        }
        self.wechat_oap = WeChat_OAP("third_part_platform", appid)


class GZh_University_Client(TEST_ZYClient):
    # 贵州黄果树瀑布水帘洞
    def __init__(self, appid):
        global HOS_CONFIG_DICT
        self.appid = appid
        self.config_data = HOS_CONFIG_DICT.get(appid)
        self.nickname = self.config_data.get("nickname") or "贵州黄果树瀑布水帘洞"
        self.subscribe_txt = self.config_data.get("subscribe_txt") or ''
        self.subscribe_news = self.config_data.get("subscribe_news") or ''
        self.mini_card_title = self.config_data.get("mini_card_title") or self.nickname + "就诊用药指导"
        self.Get_This_Guy_values = self.config_data.get("Get_This_Guy")
        self.wechat_oap = WeChat_OAP("third_part_platform", appid)


class JNChildClient(TEST_ZYClient):
    def __init__(self, appid):
        global HOS_CONFIG_DICT
        self.appid = appid
        self.config_data = HOS_CONFIG_DICT.get(appid)
        self.nickname = self.config_data.get("nickname") or "九年义务教育组织部落"
        self.subscribe_txt = self.config_data.get(
            "subscribe_txt") or """欢迎关注济南市儿童组织部落公众号，点击下方菜单栏"就诊服务" 绑定就诊卡可在线"预约挂号" "充值缴费" "查询报告"、"组织部落信息" "接收用药指导"。 """
        self.subscribe_news = self.config_data.get("subscribe_news") or ''
        self.wechat_oap = WeChat_OAP("third_part_platform", appid)


class HNChildClient(TEST_ZYClient):
    def __init__(self, appid):
        global HOS_CONFIG_DICT
        self.appid = appid
        self.config_data = HOS_CONFIG_DICT.get(appid)
        self.nickname = self.config_data.get("nickname") or "还能再来一次组织部落"
        self.subscribe_txt = self.config_data.get("subscribe_txt") or ''
        self.subscribe_news = self.config_data.get("subscribe_news") or ''
        self.Get_This_Guy_values = self.config_data.get("Get_This_Guy") or {
            "pagepath":
            "/pages/prescription/hos_report_list/index?app_id=5d0375a4b60c4asdwq0d1343&hos_name={hos_name}&open_id={open_id}",
            "template_id":
            "TlTqjYO4gd-pCncB3goYVem2CMpbgpRPI48EptBtriU",
            "first":
            "获取用药指导报告",
            "keyword2":
            "还能再来一次组织部落，处方用药指导报告",
            "remark":
            "请遵循用药指导，科学用药，祝您早日康复！"
        }
        self.wechat_oap = WeChat_OAP("third_part_platform", appid)


class PGComityClient(TEST_ZYClient):
    # 平冈山武松打虎
    def __init__(self, appid):
        global HOS_CONFIG_DICT
        self.appid = appid
        self.config_data = HOS_CONFIG_DICT.get(appid)
        self.nickname = self.config_data.get("nickname") or "平冈山武松打虎"
        self.subscribe_txt = self.config_data.get("subscribe_txt") or ''
        self.subscribe_news = self.config_data.get("subscribe_news") or ''
        self.mini_card_title = self.config_data.get("mini_card_title") or self.nickname + "就诊用药指导"
        self.Get_This_Guy_values = self.config_data.get("Get_This_Guy") or {
            "pagepath":
            "/pages/prescription/phone_name_base_info/index?app_id=5d2adq1w2ea7eef24c238&hos_name={hos_name}&open_id={open_id}&stat_source=template_menu_click_message",
            "template_id":
            "CBmJc4HblJIuauEs07kZvMnvXRGlskV17CZxW49NhRA",
            "first":
            "获取用药指导报告",
            "keyword2":
            "平谷区社会通健康卡平台，处方用药指导报告",
            "remark":
            "请遵循用药指导，科学用药，祝您早日康复！"
        }
        self.wechat_oap = WeChat_OAP("third_part_platform", appid)


class HeBUniversityClient(TEST_ZYClient):
    # 海北玄武大殿
    def __init__(self, appid):
        global HOS_CONFIG_DICT
        self.appid = appid
        self.config_data = HOS_CONFIG_DICT.get(appid)
        self.nickname = self.config_data.get("nickname") or "海北玄武大殿"
        self.subscribe_txt = self.config_data.get("subscribe_txt") or ''
        self.subscribe_news = self.config_data.get("subscribe_news") or ''
        self.mini_card_title = self.config_data.get("mini_card_title") or self.nickname + "就诊用药指导"
        self.Get_This_Guy_values = self.config_data.get("Get_This_Guy") or {}
        self.wechat_oap = WeChat_OAP("third_part_platform", appid)


class ZYMedicalClient(TEST_ZYClient):
    # 这样才好医务端
    def __init__(self, appid):
        global HOS_CONFIG_DICT
        self.appid = appid
        self.config_data = HOS_CONFIG_DICT.get(appid)
        self.nickname = self.config_data.get("nickname") or "这样才好医务端"
        self.subscribe_txt = self.config_data.get("subscribe_txt") or ''
        self.subscribe_news = self.config_data.get("subscribe_news") or ''
        self.mini_card_title = self.config_data.get("mini_card_title") or self.nickname + "就诊用药指导"
        self.Get_This_Guy_values = self.config_data.get("Get_This_Guy") or {}
        self.save_user_info = self.config_data.get("save_user_info") or 1
        self.wechat_oap = WeChat_OAP("third_part_platform", appid)


class ZYHealthClient(TEST_ZYClient):
    # 这样健康
    def __init__(self, appid):
        global HOS_CONFIG_DICT
        self.appid = appid
        self.config_data = HOS_CONFIG_DICT.get(appid)
        self.nickname = self.config_data.get("nickname") or "这样健康"
        self.subscribe_txt = self.config_data.get("subscribe_txt") or ''
        self.subscribe_news = self.config_data.get("subscribe_news") or ''
        self.mini_card_title = self.config_data.get("mini_card_title") or self.nickname + "就诊用药指导"
        self.Get_This_Guy_values = self.config_data.get("Get_This_Guy") or {}
        self.save_user_info = self.config_data.get("save_user_info") or 1
        self.wechat_oap = WeChat_OAP("third_part_platform", appid)


def get_maps(map_name: str, params: dict = {}) -> dict:
    """更新该页maps: client_dict、hos_config并返回最新值"""
    maps_data = {}
    if map_name == "client_dict":
        client_dict = CLIENT_DICT
        if params and params.get("fake_appid") in client_dict.keys():
            appid = params["fake_appid"]
            client_dict["waa111asdw43f3b5"] = client_dict[appid]
        maps_data = client_dict
    elif map_name == "hos_config":
        maps_data = hos_config = HOS_CONFIG_DICT
        if params and params.get("appid") in hos_config.keys():
            appid = params["appid"]
            maps_data = hos_config[appid]
    return maps_data


def get_all_config(client_dict) -> dict:
    all_config_dict = {}
    for appid in client_dict.keys():
        all_config_dict[appid] = get_hos_cfg.get_config(appid)
    return all_config_dict


CLIENT_DICT = {
    #"waa111asdw43f3b5": TEST_ZYClient,
    "waa111asdw43f3b5": TEST_ZYClient,  # 这样才好伪装为其余组织部落
    "wx89521qasdadqw": TMClient,
    "wx135021dewcad05d": WHClient,
    "wx12e2asf21cfsda": DPClient,
    "sa2wddcscsb31469": JNChildClient,
    "2dewecbd47a141ec": HNChildClient,
    "asdasdc621c661": PGComityClient,
    "wx2ad47e142abe2ededs": HeBUniversityClient,
    "qwdcwvcd1fcb3647": ZYMedicalClient,
    "wx7ae5c0qwdwcd40a8": ZYHealthClient,
    "wdf2e34frv438743b": GZh_University_Client,
}

lib_config.HOS_CONFIG_DICT = get_all_config(CLIENT_DICT)
HOS_CONFIG_DICT = lib_config.HOS_CONFIG_DICT
for i in HOS_CONFIG_DICT.items():
    send_log(f'HOS_CONFIG_DICT||{i}')


def update_hos_config(appid) -> dict:
    """更新HOS_CONFIG_DICT"""
    global HOS_CONFIG_DICT
    lib_config.HOS_CONFIG_DICT[appid] = get_hos_cfg.get_config(appid)
    HOS_CONFIG_DICT = lib_config.HOS_CONFIG_DICT
    send_log(f'HOS_CONFIG_DICT||{appid}||{HOS_CONFIG_DICT[appid]}')
    return HOS_CONFIG_DICT[appid]


"""
# 测试
test_client = CLIENT_DICT["wx89521qasdadqw"]("wx89521qasdadqw")
"""
# print("\n\n\n\n", HOS_CONFIG_DICT)
