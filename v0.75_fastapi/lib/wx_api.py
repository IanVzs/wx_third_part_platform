import time
import xmltodict
from fastapi import Response

from lib import access, config as lib_config

def send_text_cont(fromu, tou, cont, nonce):
    """
    send all text msg
    user_openid
    source_appid
    msg
    nonce
    """
    reply_xml = """
    <xml>
    <ToUserName><![CDATA[%s]]></ToUserName>
    <FromUserName><![CDATA[%s]]></FromUserName>
    <CreateTime>%d</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[%s]]></Content>
    </xml>""" % (fromu, tou, int(time.time()), cont)
    encryper = access.WXBizMsgCrypt(lib_config.TOKEN, lib_config.ENCODINGAESKEY, lib_config.WXAPPID)
    # ret, encrypt_xml = encryper.encrypt_msg(reply_msg=reply_xml, nonce=nonce)
    ret, encrypt_xml = encryper.EncryptMsg(reply_xml, nonce)
    send_text_log = {"ret": ret, "reply_xml": reply_xml, "encrypt_xml": encrypt_xml, "nonce": nonce, "fromu": fromu, "tou": tou}
    return Response(encrypt_xml, media_type='text/xml')


def send_bank_response(nonce=None):
    """send bank msg"""
    bank_log = {"nonce": nonce}
    return Response('', media_type='text/xml')

def deal_wx_api(data, signature, timestamp, nonce):
    cryper = access.WXBizMsgCrypt(lib_config.TOKEN, lib_config.ENCODINGAESKEY, lib_config.WXAPPID)
    postdata = cryper.DecryptMsg(data, signature, timestamp, nonce)
    postdata = postdata[1] and xmltodict.parse(postdata[1])
    if postdata:
        data_dict = postdata.get("xml")
        data_dict["nonce"] = nonce
        source_appid = data_dict.get("ToUserName")
        user_openid = data_dict.get("FromUserName")
        msg_id = data_dict.get("MsgId")
        msg_type = data_dict.get("MsgType")
        creat_time = data_dict.get("CreateTime")

        if msg_type == "event":
            pass
            # rsp = wx_workers.wx_event(appid, data_dict)
        elif msg_type == "text":
            msg_content = data_dict.get("Content")
            return send_text_cont(user_openid, source_appid, msg_content, nonce)
    return send_bank_response(nonce)

if "__main__" == __name__:
    import sys
    sys.path.append("/home/ubuntu/wx_third_part_platform/v0.75")
    data = b'<xml>\n    <ToUserName><![CDATA[gh_23b2da4be370]]></ToUserName>\n    <Encrypt><![CDATA[9S0374d6l4pjSABgDoXwQtbVfnib6eg4MiS/XoWvjdtBbXSl2Pp+6QjKj3ldgjJ2iCtfmPse+332rSFjiWQzZHQiuIcndHd5JGuyCgH+A+hT+TbEc61jDg2f1f1aLQ36AvqPWPg5FXt9PrHDRJ1QiDPVHA6jxMtgLxBkQtaKVj1ersDmHakXVz3YC2ESm21TkI30yN3F8Zik6VaI5btCL0JhOnAlIfQHDCcIb8xQ5HSQPVjg0sCqr5TM0SAkdqYYd1w8u708mdao3ZSuvSahy4MNoo8+ieGqCzJJZjFxkOfL3XaZ1NDNMHhmsVkPFDJEV289lEZIdPgo8wGK20n8nLSdU+VQRDatwZ6ZU4x6BS46AXWo9K1+YR1v+jGlR6ZCUB4W+7NMYGUb5z9a+OXRqsqNrfVxE+8F59lAWCtwl2o=]]></Encrypt>\n</xml>\n'
    signature = "e748161f90c61b52bb90056e7a3e711e7b076ae9"
    timestamp = "1591524733"
    nonce = "1917867674"
    cryper = access.WXBizMsgCrypt(lib_config.TOKEN, lib_config.ENCODINGAESKEY, lib_config.WXAPPID)
    postdata = cryper.DecryptMsg(data, signature, timestamp, nonce)
    print(postdata)
