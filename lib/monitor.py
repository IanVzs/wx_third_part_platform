# -*-coding: utf-8-*-
"""定时、后台任务"""

import json
from log import log_error
from lib.wx_service import WeChat_OAP
from lib import config as lib_config
from dao import wx_service as dao_wxservice, wx_api as dao_wxapi


class WechatOffAccPlatformMonitor:
    """微信公众号监视器"""

    def __init__(self):
        pass

    @staticmethod
    def make_wrarning(warning_msg, mail_to="server_monitor@zuasdhakqcheg.com"):
        """打日志，报警"""
        body = warning_msg
        warning_msg_dict = {'mail_to': mail_to, 'title': u'wx_third_part_platform|Monitor', 'body': body}
        log_error(u'logstash###wx_third_part_platform###WARNING###{}'.format(
            json.dumps(warning_msg_dict, ensure_ascii=False)))

    @staticmethod
    def menu_monitor_status():
        """监视菜单"""
        status_list = []
        appid_list = dao_wxservice.get_all_auth_appid()  # 全部授权公众号appid
        had_own_menu = []  # 含有我方配置的公众号appid
        for appid in appid_list:
            menu_info_cfg = None
            if appid in lib_config.HOS_CONFIG_DICT:
                menu_info_cfg = lib_config.HOS_CONFIG_DICT[appid].get("menu_info")
            if menu_info_cfg:
                if isinstance(menu_info_cfg, dict):
                    menu_info_cfg = [menu_info_cfg]
                for menu_info in menu_info_cfg:
                    had_own_menu.append(appid)
                    button_name = menu_info.get("name") or ''
                    button_position = menu_info.get("position") or []
                    button_info = menu_info.get("button") or {}

                    # 获取当前各个公众号的菜单表
                    wechat_oap = WeChat_OAP("third_part_platform", appid)
                    menu_data_currect = wechat_oap.get_menu()
                    menu_data_currect_self = wechat_oap.get_cur_self_menu()

                    # 取出当前公众号配置的按钮名称， 查看是否存在于当前菜单表中
                    if button_name in json.dumps(
                            menu_data_currect, ensure_ascii=False) or (button_name in json.dumps(
                                menu_data_currect_self, ensure_ascii=False)
                                                                       and "pages/diagnose/diagnose" not in json.dumps(
                                                                           menu_data_currect_self, ensure_ascii=False)):
                        # WechatOffAccPlatformMonitor.make_wrarning(menu_data_currect, "test")
                        status_list.append({"appid": appid, "status": 0})
                    else:
                        recovery_data = {
                            "app_id": appid,
                            "data": {
                                "action": "replace",
                                "sub_data": button_info,
                                "pos": button_position,
                            }
                        }
                        status_list.append({
                            "appid":
                            appid,
                            "nickname":
                            lib_config.HOS_CONFIG_DICT[appid].get("nickname"),
                            "status":
                            1,
                            "menu_currect":
                            f'https://wx.zuasdhakqcheg.com/wx_service/get_menu?app_id={appid}',
                            "menu_currect_self":
                            f'https://wx.zuasdhakqcheg.com/wx_service/get_menu?app_id={appid}&cur_self=1',
                            "notes":
                            "多个按钮时，不可以直接使用one_click_recovery进行恢复，只能一个按钮dict对应一个位置list一一恢复. 以及需要删除curl命令中的单引号转义符",
                            "one_click_recovery":
                            f"""curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X POST -d '{json.dumps(recovery_data, ensure_ascii=False)}' https://wx.zuasdhakqcheg.com/wx_service/create_menu"""
                        })

        return status_list

    @staticmethod
    def authorization_event(event_name, data):
        """授权事件监控， 公众号授权给第三方平台"""
        data = data
        app_id = ''
        nick_name = ''
        monitor_data = {}
        if event_name == "authorized":
            # 授权
            data["event_name"] = f'{data.get("AuthorizerAppid")}授权予《左手医生微信第三方平台》.'
            app_id = dao_wxapi.read_data(data.get("PreAuthCode") or '') or ''
        elif event_name == "unauthorized":
            # 取消授权
            data["event_name"] = f'{data.get("AuthorizerAppid")}取消对于《左手医生微信第三方平台》的授权.'
            nick_name = dao_wxservice.get_nick_name_by_wechat_id(data.get("AuthorizerAppid") or '')
        elif event_name == "updateauthorized":
            # 更新授权
            data["event_name"] = f'{data.get("AuthorizerAppid")}更新对于《左手医生微信第三方平台》的授权内容.'
            app_id = dao_wxservice.get_app_id_by_wechat_id(data.get("AuthorizerAppid") or '')
        else:
            # 异常操作？
            data["event_name"] = f'{data.get("AuthorizerAppid")}授权行为异常.'
        if app_id:
            # 授予 更新 权限
            monitor_data["see_detail_url"] = ('http://wx.zuasdhakqcheg.com/wx_service/get_auth_info?app_id=' + app_id)
        elif nick_name:
            # 取消授权
            monitor_data["nick_name"] = nick_name
        monitor_data["event_name"] = data["event_name"]
        WechatOffAccPlatformMonitor.make_wrarning(monitor_data, "assis_monitor@zuasdhakqcheg.com")
