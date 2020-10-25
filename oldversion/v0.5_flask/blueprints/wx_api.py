# -*-coding: utf-8-*-

import json
import time
import gevent
import datetime
import xmltodict
import requests
from flask import Blueprint, jsonify, abort, request, make_response
from flask import Response, render_template

import config
from log import *
from lib.send_log import send_log
from lib import config as lib_config
from lib.monitor import WechatOffAccPlatformMonitor
from dao import wx_service as dao_wxservice
from lib import access, authorization, access3, wx_workers
from dao import wx_api as dao_wxapi

WXAPI = Blueprint('wxapi', __name__)


def get_paras():
    """加密数据解析"""
    postdata = request.data.decode('utf-8')
    url_para_dict = dict(request.args)
    msg_signature = request.args.get("msg_signature")
    nonce = request.args.get("nonce")
    timestamp = request.args.get("timestamp")
    # 授权回调的参数
    auth_code = request.args.get("auth_code")
    ex = request.args.get("expires_in")
    return postdata, msg_signature, timestamp, nonce, auth_code, ex


def do_authorization(data_dict):
    """授权事件处理"""
    if "AppId" in data_dict:
        try:
            appid = data_dict.get("AppId")  # 第三方平台Appid
            authorizer_appid = data_dict.get("AuthorizerAppid")  # 公众号appid
            pre_auth_code = data_dict.get("PreAuthCode")
            authorization_code = data_dict.get("AuthorizationCode")
            dao_wxapi.save("auth_code", authorization_code)
            dao_wxapi.save(authorization_code, pre_auth_code)

            com_access_token = dao_wxapi.read_data("com_access_token")
            if not com_access_token:
                send_log("com_access_token error", err=True)
            if data_dict.get("InfoType") != "component_verify_ticket":
                WechatOffAccPlatformMonitor.authorization_event(data_dict.get("InfoType"), data_dict)
            if data_dict.get("InfoType") == "authorized":
                # 授权成功
                send_log("AuthorizedInfo: " + str(data_dict))
                rsp_dict = authorization.authorizer_access_token(authorization_code)
                if rsp_dict.get("sign"):
                    rsp_dict["msg"] = "授权成功"
                else:
                    rsp_dict["msg"] = "授权失败"
                    log_error("授权失败|授权信息: {}".format(str(data_dict)))

            elif data_dict.get("InfoType") == "unauthorized":
                # 取消授权
                send_log("UnauthorizedInfo: " + str(data_dict))
                # server_account_info 和 appid_map 中状态置0。
                rsp_dict = authorization.unauthorized(authorizer_appid)
                if rsp_dict["sign"]:
                    rsp_dict["msg"] = "已取消授权"

            elif data_dict.get("InfoType") == "updateauthorized":
                # 更新授权
                send_log("UpdateauthorizedInfo: " + str(data_dict))
                rsp_dict = authorization.authorizer_access_token(authorization_code, False)
                if rsp_dict["sign"]:
                    update_list = authorization.refresh_info()
        except Exception as e:
            send_log(e.__class__.__name__ + '|' + str(e), err=True)

    return 1


@WXAPI.route('/wx_api', methods=['POST', 'GET'])
#@profiler.profileit
def ticket():
    """微信公众号后台自动调用，每十分钟一次"""
    try:
        postdata, msg_signature, timestamp, nonce, auth_code, ex = get_paras()
        postdata = access.decryption(postdata, msg_signature, timestamp, nonce)
        data_dict = postdata.get("xml")
        ticket = data_dict.get("ComponentVerifyTicket")
        dao_wxapi.save("nonce", nonce)
        if ticket:
            dao_wxapi.save("ticket", ticket)

            # 使用ticket更新com_access_token
            authorization.com_access_token()

        # 授权处理
        sign = do_authorization(data_dict)  # 授权事件处理

    except Exception as e:
        send_log(e.__class__.__name__ + '|' + str(e), err=True)
    return Response('success')


def post_custom_text_msg(touser, content, stoken):
    """send custom text msg"""
    url = 'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=%s' % stoken
    payload = {"touser": touser, "msgtype": "text", "text": {"content": content}}
    headers = {'content-type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    logger.info('post_custom_text_msg return: ' + response.text)


def send_text_cont(fromu, tou, cont, nonce):
    """send all text msg"""
    reply_xml = """
    <xml>
    <ToUserName><![CDATA[%s]]></ToUserName>
    <FromUserName><![CDATA[%s]]></FromUserName>
    <CreateTime>%d</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[%s]]></Content>
    </xml>""" % (fromu, tou, int(time.time()), cont)
    encryper = access3.WXBizMsgCrypt(lib_config.TOKEN, lib_config.ENCODINGAESKEY, lib_config.WXAPPID)
    # ret, encrypt_xml = encryper.encrypt_msg(reply_msg=reply_xml, nonce=nonce)
    ret, encrypt_xml = encryper.EncryptMsg(reply_xml, nonce)
    send_text_log = {"ret": ret, "reply_xml": reply_xml, "encrypt_xml": encrypt_xml, "nonce": nonce, "fromu": fromu, "tou": tou}
    send_log(f"send_text_cont|{send_text_log}")
    return Response(encrypt_xml, mimetype='text/xml')


def send_pic_cont(fromu, tou, nonce, appid):
    """send all text msg"""
    reply_xml = ''
    news_data = {
        'xml': {
            'ToUserName': '',
            'FromUserName': '',
            'CreateTime': '',
            'MsgType': 'news',
            'ArticleCount': '',
            'Articles': {
                'item': []
            }
        }
    }
    if appid in lib_config.HOS_CONFIG_DICT and "NEWS_DATA" in lib_config.HOS_CONFIG_DICT[appid]:
        NEWS_DATA = lib_config.HOS_CONFIG_DICT[appid]["NEWS_DATA"]

        news_data["xml"]["ToUserName"] = fromu
        news_data["xml"]["FromUserName"] = tou
        news_data["xml"]["CreateTime"] = int(time.time())
        news_data["xml"]["ArticleCount"] = len(NEWS_DATA)
        news_data["xml"]["Articles"]["item"] = NEWS_DATA

        reply_xml = xmltodict.unparse(news_data)

    elif tou == "gh_a46bnkejrve":
        reply_xml = """
        <xml>
            <ToUserName><![CDATA[{toUser}]]></ToUserName>
            <FromUserName><![CDATA[{fromUser}]]></FromUserName>
            <CreateTime>{crTime}</CreateTime>                                                                                                                                                   <MsgType><![CDATA[news]]></MsgType>
            <ArticleCount>2</ArticleCount>
            <Articles>
                <item>
                    <Title><![CDATA[{title1}]]></Title>
                    <Description><![CDATA[{description1}]]></Description>
                    <PicUrl><![CDATA[{picurl}]]></PicUrl>
                    <Url><![CDATA[{url1}]]></Url>
                </item>
                <item>
                    <Title><![CDATA[{title2}]]></Title>
                    <Description><![CDATA[{description2}]]></Description>
                    <PicUrl><![CDATA[{picur2}]]></PicUrl>
                    <Url><![CDATA[{url2}]]></Url>
                </item>
            </Articles>
        </xml>""".format(
            **{
                "toUser":
                fromu,
                "fromUser":
                tou,
                "crTime":
                int(time.time()),
                "title1":
                "标题1",
                "title2":
                "「用药指导」上线啦！10秒读懂怎么用",
                "description1":
                "",
                "description2":
                "",
                "picurl":
                "http://mmbiz.qpic.cn/mmbiz_jpg/YFhgtzRnDryjQHnTkmfHKO1J4OnaLv7sl0gdrtfyuihjngvhujskmYzP1er64A/0?wx_fmt=jpeg",
                "picur2":
                "http://mmbiz.qpic.cn/mmbiz_jpg/YFhgtzRnDrwlMKBRZYpMRcFiaqgdiacsjeftyuhnjskqHN1H1zNRh9QicaSMoTqXt3oian26GQyxNEB85Ssg/0?wx_fmt=jpeg",
                "url1":
                "https://mp.weixin.qq.com/s?__biz=MzUzMDg0NTA2Mg==&mid=100000005&idx=1&sn=c0cbwuendewncfdea42a26f67156&chksm=7a4addec4d3d54fa32c0b52b32b92be68fdf99c52ba50c8851a6833bc13f3d5ef78fa58a2d69#rd",
                "url2":
                "http://mp.weixin.qq.com/s?__biz=MzUzMDg0NTA2Mg==&mid=10000000ughijejwncvrb26985b0eb0b60e48c&chksm=7a4addec4d3d54faebfaae51e0c6e9507132c038dcf35443ecefaace77e46fa6d8ecda662ace#rd",
            })
    elif tou == "gh_6ba3asaeef0":
        reply_xml = """
        <xml>
            <ToUserName><![CDATA[{toUser}]]></ToUserName>
            <FromUserName><![CDATA[{fromUser}]]></FromUserName>
            <CreateTime>{crTime}</CreateTime>                                                                                                                                                   <MsgType><![CDATA[news]]></MsgType>
            <ArticleCount>3</ArticleCount>
            <Articles>
                <item>
                    <Title><![CDATA[{title1}]]></Title>
                    <Description><![CDATA[{description1}]]></Description>
                    <PicUrl><![CDATA[{picurl}]]></PicUrl>
                    <Url><![CDATA[{url1}]]></Url>
                </item>
                <item>
                    <Title><![CDATA[{title2}]]></Title>
                    <Description><![CDATA[{description2}]]></Description>
                    <PicUrl><![CDATA[{picur2}]]></PicUrl>
                    <Url><![CDATA[{url2}]]></Url>
                </item>
                <item>
                    <Title><![CDATA[{title3}]]></Title>
                    <Description><![CDATA[{description3}]]></Description>
                    <PicUrl><![CDATA[{picur3}]]></PicUrl>
                    <Url><![CDATA[{url3}]]></Url>
                </item>
            </Articles>
        </xml>""".format(
            **{
                "toUser":
                fromu,
                "fromUser":
                tou,
                "crTime":
                int(time.time()),
                "title1":
                "精致组织部落丨创新“互联网+医疗”，打造“指尖上的组织部落”——新版微信公众号上线啦",
                "title2":
               "请查收！你的专属「用药指导」",
                "title3":
                "住院费用明细，扫码全知道",
                "description1":
                "在手机上动动指尖，挂号、缴费、查看报告就能便捷完成，省去了排队等候、反复奔波的辛苦;",
                "description2":
                "平时去组织部落看病，我们听到医生说的最多话就是：遵医嘱、按时服药、规律服药、规律治疗、定期复查等。",
                "description3":
                "组织部落费用一直都是大家很关心的问题，我院全新上线了「扫腕带查清单」功能，只要扫一扫腕带上的二维码，所有费用一目了然。",
                "picurl":
                "http://mmbiz.qpic.cn/mmbiz_jpg/J9nmfvFevLzusUibk9fcdvfb52icgcTZE7VPx1UYaHMs8yIDDDc7rI8D0icrWOdkfQUg/0?wx_fmt=jpeg",
                "picur2":
                "http://mmbiz.qpic.cn/mmbiz_jpg/J9nmfvFevLzusUibk9TcbbdcpR9vXEaULkTuyeeZOxbR8HTP2WzM40Kic7al1fibVfUg/0?wx_fmt=jpeg",
                "picur3":
                "http://mmbiz.qpic.cn/mmbiz_jpg/J9nmfvFevLzusUibk9TcbqAYXdcwe2fgvb6sEJ2ZpoVPCURHdPEhPwnSIWKLwQf9SpFyA/0?wx_fmt=jpeg",
                "url1":
                "http://mp.weixin.qq.com/s?__biz=MzI5MjEyMTExOQ==&mid=506776731&idx=1&sn=c2bf0414cdsfer34fg175204c1b8968&chksm=77c653eb40b1dafd391f334ee1a8a35ab68bf78b321d97805839f7a1013e369e27c3601ea426#rd",
                "url2":
                "http://mp.weixin.qq.com/s?__biz=MzI5MjEyMTExOQ==&mid=506776731&idx=2&sn=5bbb93dvew3rvede4f15f65b&chksm=77c653eb40b1dafda1987feee0f1403979d5891adfedc4678a4ff47bab9ad41f316ad6319b6f#rd",
                "url3":
                "http://mp.weixin.qq.com/s?__biz=MzI5MjEyMTExOQ==&mid=506776731&idx=3&sn=16eadf39ewegbdve9105cc04d52b6&chksm=77c653eb40b1dafdcf778075e4e44d07365c3e68f36266cd3e1bf92beb4d38007f7dbcbeb5c6#rd",
            })
    encryper = access3.WXBizMsgCrypt(lib_config.TOKEN, lib_config.ENCODINGAESKEY, lib_config.WXAPPID)
    #ret, encrypt_xml = encryper.encrypt_msg(reply_msg=reply_xml, nonce=nonce)
    ret, encrypt_xml = encryper.EncryptMsg(reply_xml, nonce)
    log_dict = {"ret": ret, "reply_xml": reply_xml, "nonce": nonce, "fromu": fromu, "tou": tou}
    send_log(f'send_pic_cont|{log_dict}')
    return Response(encrypt_xml, mimetype='text/xml')


def send_bank_response(nonce=None):
    """send bank msg"""
    bank_log = {"nonce": nonce}
    send_log(f"send_bank_response|{bank_log}")
    return Response('')


@WXAPI.route('/wx_api/msg/<appid>', methods=['POST', 'GET'])
#@profiler.profileit
def msg(appid):
    """接受用户消息和事件"""
    logger.info("msg_or_event: " + appid)
    postdata, msg_signature, timestamp, nonce, auth_code, ex = get_paras()
    postdata = access.decryption(postdata, msg_signature, timestamp, nonce)
    log_info("User Msg:" + json.dumps(postdata))

    if postdata:
        data_dict = postdata.get("xml")
        data_dict["nonce"] = nonce
        source_appid = data_dict.get("ToUserName")
        user_openid = data_dict.get("FromUserName")
        msg_id = data_dict.get("MsgId")
        msg_type = data_dict.get("MsgType")
        creat_time = data_dict.get("CreateTime")
        if appid != "wx570bc396a51b8ff8":
            try:
                auth_token_access = dao_wxapi.read_info(appid)["authorizer_access_token"]
            except:
                log_error("get auth_token_access error: appid{}".format(appid))
                return Response('')
        response = {}
        if "MsgId" in data_dict and not msg_id:
            # 微信多次请求
            return Response("success")
        # 全网发布测试
        if msg_type == "event":
            rsp = wx_workers.wx_event(appid, data_dict)
            #if rsp["sign"] == 2:
            # sign == 2 时，对用户进行反馈
            if not rsp["sign"] and appid == "waa111asdw43f3b5":
                # 这样才好返回失败原因debug
                return send_text_cont(fromu=user_openid, tou=source_appid, cont=rsp["msg"], nonce=nonce)
            elif rsp.get("reply_news"):
                # 优先发送图文
                return send_pic_cont(fromu=user_openid, tou=source_appid, nonce=nonce, appid=appid)
            elif rsp.get("reply_txt"):
                return send_text_cont(fromu=user_openid, tou=source_appid, cont=rsp["msg"], nonce=nonce)

        elif msg_type == "text":
            msg_content = data_dict.get("Content")
            log_info('got the content %s' % msg_content)
            if msg_content == "TESTCOMPONENT_MSG_TYPE_TEXT":
                reply_cont = msg_content + "_callback"
                return send_text_cont(fromu=user_openid, tou=source_appid, cont=reply_cont, nonce=nonce)
            elif msg_content and msg_content.startswith('QUERY_AUTH_CODE'):
                # 测试
                query_auth_code = msg_content.split(':')[1]
                com_access_token = dao_wxapi.read_data("com_access_token")
                auth_code = query_auth_code
                if appid:
                    info = dao_wxapi.read_info(appid)
                    send_log(f'{appid}###info: {info}')
                    if "authorizer_access_token" in info:
                        authorizer_access_token = dao_wxapi.read_info(appid)["authorizer_access_token"]
                        post_cont = auth_code + '_from_api'
                        gevent.spawn(post_custom_text_msg, **{
                            "touser": user_openid,
                            "content": post_cont,
                            "stoken": authorizer_access_token
                        }).join()
                return send_bank_response()

        if msg_type == "text":
            msg_content = data_dict.get("Content")
            rsp_data_dict = postdata

            url = config.URL_MSGCUSTOM.format(auth_token_access)
            if "id" in msg_content or "ID" in msg_content or "同煤数据" in msg_content:
                # 便捷获取openid
                reply_cont = ''
                if "debug" in msg_content:
                    try:
                        debug_setting = msg_content.split("::")[-1]
                        debug_setting_dict = json.loads(debug_setting)
                        config.DEBUG_LOG["touser"] = user_openid
                        config.DEBUG_LOG["switch"] = debug_setting_dict.get("switch") or 0
                        config.DEBUG_LOG["log_key"] = debug_setting_dict.get("log_key") or 'WOW'
                        config.DEBUG_LOG[
                            "fake_appid"] = debug_setting_dict.get("fake_appid") or config.DEBUG_LOG["fake_appid"]
                        msg_list = [str(i) for i in config.DEBUG_LOG.values()]
                        msg_str = ','.join(msg_list)
                        reply_cont = msg_str
                    except:
                        reply_cont = """id,debug::{"log_key": "Authorization", "switch": 1}"""
                elif "app" in msg_content:
                    reply_cont = appid
                    if "source" in msg_content:
                        reply_cont = source_appid
                elif "学我" in msg_content or "follow" in msg_content:
                    reply_cont = msg_content
                elif "数据卡了" in msg_content and source_appid == "gh_1adc6e723b39":
                    reply_cont = "https://web.zusadeng.com/p-record?app_id=5dw 29ea2ea76d3529ad5"
                else:
                    reply_cont = user_openid
                return send_text_cont(fromu=user_openid, tou=source_appid, cont=reply_cont, nonce=nonce)
            logger.info("Send msg custom from {} to {}".format(user_openid, appid))
        elif msg_type == "voice":
            return send_bank_response(nonce=nonce)
        elif msg_type == "image":
            return send_bank_response(nonce=nonce)
        elif msg_type == "link":
            return send_bank_response(nonce=nonce)
    else:
        none_log = {"appid": appid, "msg_signature": msg_signature, "nonce": nonce, "auth_code": auth_code, "ex": ex}
        send_log(f"MSG|postdata is None|{none_log}", err=True)

    return Response('success')


@WXAPI.route('/wx_api/redirect', methods=['POST', 'GET'])
#@profiler.profileit
def redirect():
    """授权回调"""
    log_info('', request)
    #  授权完成后的回调页面， 可在授权完成后展示授权信息.或进行页面跳转之类。
    # TODO
    return Response("Success")


def do_auth(inputs: dict, test: bool = False) -> dict:
    """授权前置步骤"""
    fail = []
    log_info("GET INPUT", inputs)
    app_id = inputs.get("app_id")
    rsp = {"sign": 0, "msg": ''}
    if app_id:
        # 存入数据库占位, 授权完成后调取信息补位
        if inputs.get("pre_auth_code") or test:
            placeholder = {
                "pre_auth_code": inputs["pre_auth_code"],
                "appid": app_id,
                "nick_name": "_placeholder",
                "wechat_appid": "_placeholder"
            }
            save_rsp = dao_wxservice.save(placeholder)
            dao_wxapi.save(inputs["pre_auth_code"], app_id)
            send_log("AuthorizationStart: placeholder: {}, save_rsp: {}".format(str(placeholder), str(save_rsp)))
            rsp = save_rsp
    else:
        rsp["msg"] = "params loss: app_id"
        fail.append(rsp["msg"])
    return fail, rsp


@WXAPI.route('/wx_api/auth', methods=['GET'])
#@profiler.profileit
def auth(_from=None):
    # 授权入口
    # 需appid, pre_auth_code, redirect_url
    # 选填 auth_type(1/2/3), biz_appid

    log_info('', request)
    inputs = {}
    fail = []
    inputs["app_id"] = request.args.get("app_id")
    appid = config.WXAPPID
    pre_auth_code = authorization.pre_auth_code()
    pre_auth_code_save = dao_wxapi.read_data("pre_auth_code")
    if pre_auth_code != pre_auth_code_save:
        log_error("pre_auth_code Error: pre_auth_code_new: {}, pre_auth_code_save: {}".format(
            pre_auth_code, pre_auth_code_save))
    redirect_url = config.URL_REDIRECT + '?pre_auth_code=' + pre_auth_code

    url_wxauth = config.URL_WXAUTH
    url_auth = url_wxauth.format(appid, pre_auth_code, redirect_url, 3)
    # 1 仅允许公众号 2 小程序 3 小程序&公众号
    if not fail:
        inputs["pre_auth_code"] = pre_auth_code
        fail, sv_rsp = do_auth(inputs)
        """
        if _from == "wx_service":
            rsp = {"url_auth": url_auth, "pre_auth_code": pre_auth_code}
        """
        if sv_rsp.get("sign"):
            return render_template("index.html", url=url_auth)
    return "check and try again."


@WXAPI.route('/wx_api/refreshtoken', methods=['GET'])
#@profiler.profileit
def refreshtoken():
    authorization.refresh_token()
    return Response("success")
