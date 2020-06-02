#!/usr/bin/env python
# -*-coding: utf-8-*-
""" 
    python3对公众平台发送给公众账号的消息加解密代码.支持中文.
"""
# ------------------------------------------------------------------------

import base64
import string
import random
import hashlib
import time
import struct

import binascii
from Crypto.Cipher import AES
import xml.etree.cElementTree as ET
import socket
import xmltodict

try:
    from . import ierror
    from . import config
except:
    import ierror
    import config
""" AES加解密用 pycrypto """


class FormatException(Exception):
    pass


def throw_exception(message, exception_class=FormatException):
    """my define raise exception function"""
    raise exception_class(message)


class SHA1:
    """计算公众平台的消息签名接口"""

    def getSHA1(self, token, timestamp, nonce, encrypt):
        """用SHA1算法生成安全签名
        @param token:  票据
        @param timestamp: 时间戳
        @param encrypt: 密文
        @param nonce: 随机字符串
        @return: 安全签名
        """
        try:
            token = token.decode()
            sortlist = [token, timestamp, nonce, encrypt]
            sortlist.sort()
            sha = hashlib.sha1()
            sha.update("".join(sortlist).encode("utf8"))
            return ierror.WXBizMsgCrypt_OK, sha.hexdigest()
        except Exception as e:
            print(e)
            return ierror.WXBizMsgCrypt_ComputeSignature_Error, None


class XMLParse(object):
    """提供提取消息格式中的密文及生成回复消息格式的接口"""

    # xml消息模板
    AES_TEXT_RESPONSE_TEMPLATE = """<xml>
        <Encrypt><![CDATA[%(msg_encrypt)s]]></Encrypt>
        <MsgSignature><![CDATA[%(msg_signaturet)s]]></MsgSignature>
        <TimeStamp>%(timestamp)s</TimeStamp>
        <Nonce><![CDATA[%(nonce)s]]></Nonce>
        </xml>"""

    def extract(self, xmltext):
        """提取出xml数据包中的加密消息
        @param xmltext: 待提取的xml字符串
        @return: 提取出的加密消息字符串
        """
        try:
            xml_tree = ET.fromstring(xmltext)
            encrypt = xml_tree.find("Encrypt")
            # touser_name = xml_tree.find("ToUserName")
            return ierror.WXBizMsgCrypt_OK, encrypt.text
        except Exception as e:
            return ierror.WXBizMsgCrypt_ParseXml_Error, ''

    def generate(self, encrypt, signature, timestamp, nonce):
        """生成xml消息
        @param encrypt: 加密后的消息密文
        @param signature: 安全签名
        @param timestamp: 时间戳
        @param nonce: 随机字符串
        @return: 生成的xml字符串
        """
        resp_dict = {
            'msg_encrypt': encrypt,
            'msg_signaturet': signature,
            'timestamp': timestamp,
            'nonce': nonce,
        }
        resp_xml = self.AES_TEXT_RESPONSE_TEMPLATE % resp_dict
        return resp_xml


class PKCS7Encoder(object):
    """提供基于PKCS7算法的加解密接口"""

    block_size = 32

    def encode(self, text):
        """ 对需要加密的明文进行填充补位
        @param text: 需要进行填充补位操作的明文
        @return: 补齐明文字符串
        """
        text_length = len(text)
        # 计算需要填充的位数
        amount_to_pad = self.block_size - (text_length % self.block_size)
        if amount_to_pad == 0:
            amount_to_pad = self.block_size
        # 获得补位所用的字符
        pad = chr(amount_to_pad).encode()
        return text + pad * amount_to_pad

    def decode(self, decrypted):
        """删除解密后明文的补位字符
        @param decrypted: 解密后的明文
        @return: 删除补位字符后的明文
        """
        pad = ord(decrypted[-1])
        if pad < 1 or pad > 32:
            pad = 0
        return decrypted[:-pad]


class Prpcrypt(object):
    """提供接收和推送给公众平台消息的加解密接口"""

    def __init__(self, key):
        # self.key = base64.b64decode(key+"=")
        self.key = key
        # 设置加解密模式为AES的CBC模式
        self.mode = AES.MODE_CBC

    def encrypt(self, text, appid):
        """对明文进行加密
        @param text: 需要加密的明文
        @return: 加密得到的字符串
        """
        # 16位随机字符串添加到明文开头
        len_str = struct.pack("I", socket.htonl(len(text.encode())))
        # text = self.get_random_str() + binascii.b2a_hex(len_str).decode() + text + appid
        text = self.get_random_str() + len_str + text.encode() + appid
        # 使用自定义的填充方式对明文进行补位填充
        pkcs7 = PKCS7Encoder()
        text = pkcs7.encode(text)
        # 加密
        cryptor = AES.new(self.key, self.mode, self.key[:16])
        try:
            ciphertext = cryptor.encrypt(text)
            # 使用BASE64对加密后的字符串进行编码
            return ierror.WXBizMsgCrypt_OK, base64.b64encode(ciphertext).decode('utf8')
        except Exception as e:
            return ierror.WXBizMsgCrypt_EncryptAES_Error, None

    def decrypt(self, text, appid):
        """对解密后的明文进行补位删除
        @param text: 密文
        @return: 删除填充补位后的明文
        """
        try:
            cryptor = AES.new(self.key, self.mode, self.key[:16])
            # 使用BASE64对密文进行解码，然后AES-CBC解密
            plain_text = cryptor.decrypt(base64.b64decode(text))
        except Exception as e:
            print(e)
            return ierror.WXBizMsgCrypt_DecryptAES_Error, None
        try:
            # pad = ord(plain_text[-1])
            pad = plain_text[-1]
            # 去掉补位字符串
            # pkcs7 = PKCS7Encoder()
            # plain_text = pkcs7.encode(plain_text)
            # 去除16位随机字符串
            content = plain_text[16:-pad]
            xml_len = socket.ntohl(struct.unpack("I", content[:4])[0])
            xml_content = content[4:xml_len + 4]
            from_appid = content[xml_len + 4:]
        except Exception as e:
            return ierror.WXBizMsgCrypt_IllegalBuffer, None
        if from_appid != appid:
            return ierror.WXBizMsgCrypt_ValidateAppid_Error, None
        return 0, xml_content.decode()

    def get_random_str(self):
        """ 随机生成16位字符串
        @return: 16位字符串
        """
        rule = string.ascii_letters + string.digits
        str = random.sample(rule, 16)
        return "".join(str).encode()


class WXBizMsgCrypt(object):
    # 构造函数
    # @param sToken: 公众平台上，开发者设置的Token
    # @param sEncodingAESKey: 公众平台上，开发者设置的EncodingAESKey
    # @param sAppId: 企业号的AppId
    # def __init__(self, sToken, sEncodingAESKey, sAppId):
    def __init__(self):
        sToken = config.TOKEN
        sEncodingAESKey = config.ENCODINGAESKEY
        sAppId = config.WXAPPID
        try:
            self.key = base64.b64decode(sEncodingAESKey + "=")
            assert len(self.key) == 32
        except Exception:
            throw_exception("[error]: EncodingAESKey unvalid !", FormatException)
            # return ierror.WXBizMsgCrypt_IllegalAesKey)
        self.token = sToken.encode()
        self.appid = sAppId.encode()

    def EncryptMsg(self, sReplyMsg, sNonce, timestamp=None):
        # 将公众号回复用户的消息加密打包
        # @param sReplyMsg: 企业号待回复用户的消息，xml格式的字符串
        # @param sTimeStamp: 时间戳，可以自己生成，也可以用URL参数的timestamp,如为None则自动用当前时间
        # @param sNonce: 随机串，可以自己生成，也可以用URL参数的nonce
        # sEncryptMsg: 加密后的可以直接回复用户的密文，包括msg_signature, timestamp, nonce, encrypt的xml格式的字符串,
        # return：成功0，sEncryptMsg,失败返回对应的错误码None
        pc = Prpcrypt(self.key)
        ret, encrypt = pc.encrypt(sReplyMsg, self.appid)
        if ret != 0:
            return ret, None
        if timestamp is None:
            timestamp = str(int(time.time()))
        # 生成安全签名
        sha1 = SHA1()
        ret, signature = sha1.getSHA1(self.token, timestamp, sNonce, encrypt)

        if ret != 0:
            return ret, None
        xmlParse = XMLParse()
        return ret, xmlParse.generate(encrypt, signature, timestamp, sNonce)

    def DecryptMsg(self, sPostData, sMsgSignature, sTimeStamp, sNonce):
        # 检验消息的真实性，并且获取解密后的明文
        # @param sMsgSignature: 签名串，对应URL参数的msg_signature
        # @param sTimeStamp: 时间戳，对应URL参数的timestamp
        # @param sNonce: 随机串，对应URL参数的nonce
        # @param sPostData: 密文，对应POST请求的数据
        #  xml_content: 解密后的原文，当return返回0时有效
        # @return: 成功0，失败返回对应的错误码
        # 验证安全签名
        xmlParse = XMLParse()
        ret, encrypt = xmlParse.extract(sPostData)
        if ret != 0:
            return ret, None
        sha1 = SHA1()
        ret, signature = sha1.getSHA1(self.token, sTimeStamp, sNonce, encrypt)
        if ret != 0:
            return ret, None
        if not signature == sMsgSignature:
            return ierror.WXBizMsgCrypt_ValidateSignature_Error, None
        pc = Prpcrypt(self.key)
        ret, xml_content = pc.decrypt(encrypt, self.appid)
        return ret, xml_content


def send():
    encryption()
    pass


def get_paras(decryp_xml, dsp_str=None):
    data_value = None
    data_dict = xmltodict.parse(decryp_xml)
    if dsp_str:
        data_value = data_dict['xml'].get(dsp_str)
    else:
        data_value = data_dict
    return data_value


def encryption(to_xml, nonce):
    # 加密
    encryptor = WXBizMsgCrypt()
    ret, encrypt_xml = encryptor.EncryptMsg(to_xml, nonce)
    xml_tree = ET.fromstring(encrypt_xml)
    return ret, encrypt_xml


def decryption(from_xml, msg_sign, timestamp, nonce, dsp_str=None):
    # 解密
    data_value = None
    decryptor = WXBizMsgCrypt()
    ret, decryp_xml = decryptor.DecryptMsg(from_xml, msg_sign, timestamp, nonce)
    if ret == 0:
        data_value = get_paras(decryp_xml, dsp_str)

    return data_value


if __name__ == "__main__":
    nonce = "1320562132"  # 随机数
    #-----------加密----------
    to_xml = """ <xml><ToUserName><![CDATA[oia2TjjewbmiOUlr6X-1crbLOvLw]]></ToUserName><FromUserName><![CDATA[gh_7f083739789a]]></FromUserName><CreateTime>1407743423</CreateTime><MsgType>  <![CDATA[video]]></MsgType><Video><MediaId><![CDATA[eYJ1MbwPRJtOvIEabaxHs7TX2D-HV71s79GUxqdUkjm6Gs2Ed1KF3ulAOA9H1xG0]]></MediaId><Title><![CDATA[testCallBackReplyVideo]]></Title><Descript  ion><![CDATA[testCallBackReplyVideo]]></Description></Video></xml>"""
    ret1, encrypt_xml = encryption(to_xml, nonce)
    #------------解密-------------
    timestamp = "1409735669"
    msg_sign = "5d197aaffba7e9b25a30732f161a50dee96bd5fa"
    from_xml = """<xml><ToUserName><![CDATA[gh_10f6c3c3ac5a]]></ToUserName><FromUserName><![CDATA[oyORnuP8q7ou2gfYjqLzSIWZf0rs]]></FromUserName><CreateTime>1409735668</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[abcdteT]]></Content><MsgId>6054768590064713728</MsgId><Encrypt><![CDATA[hyzAe4OzmOMbd6TvGdIOO6uBmdJoD0Fk53REIHvxYtJlE2B655HuD0m8KUePWB3+LrPXo87wzQ1QLvbeUgmBM4x6F8PGHQHFVAFmOD2LdJF9FrXpbUAh0B5GIItb52sn896wVsMSHGuPE328HnRGBcrS7C41IzDWyWNlZkyyXwon8T332jisa+h6tEDYsVticbSnyU8dKOIbgU6ux5VTjg3yt+WGzjlpKn6NPhRjpA912xMezR4kw6KWwMrCVKSVCZciVGCgavjIQ6X8tCOp3yZbGpy0VxpAe+77TszTfRd5RJSVO/HTnifJpXgCSUdUue1v6h0EIBYYI1BD1DlD+C0CR8e6OewpusjZ4uBl9FyJvnhvQl+q5rv1ixrcpCumEPo5MJSgM9ehVsNPfUM669WuMyVWQLCzpu9GhglF2PE=]]></Encrypt></xml>"""
    from_xml = """<xml>\n        <Encrypt><![CDATA[blcChS9jVwSKxKG/o1CXLPj0AZvDOfpVr0ko3+Pe2Ap0LTKnsF32xAtLXI+SdtAWIkKoLtkGnTE27J5TnT4xCEFbyN56oinszyvLnl2fjuDznqlFSuW95QbSiHlwrq/juatLfoppuy+yhH/a9HnmBDHAQz5JDMr+3ir6s884BqKGcuSyT4A9licCgT01uyXlFSLKEX6/0LUFbXEFfBbAorLkGuBD7U8Dda+SrkQSbD/57tbaEMt5q1bodyE1Q/ETsbAXkO8f1CcZdtbhaHyPomnptlgjJh1s2gw+O5PICLXns2rl5bDV5ra2JQe5qvLzNT0v4REAXhs+eXjEaqzzpDKf6wuIDHRHUYHCqVFIoHSyy6JN3BdsUdRIrxiXViRe73IYEJZ+qd3YBuNbJZWAGsNhkOiK3aWR2zvOoamGWbY=]]></Encrypt>\n        <MsgSignature><![CDATA[924eb9d7ce6f869d8ef8984ccae432094b22e606]]></MsgSignature>\n        <TimeStamp>1554272036</TimeStamp>\n        <Nonce><![CDATA[1320562132]]></Nonce>\n        </xml>"""
    from_xml = """<xml><Encrypt><![CDATA[blcChS9jVwSKxKG/o1CXLPj0AZvDOfpVr0ko3+Pe2Ap0LTKnsF32xAtLXI+SdtAWIkKoLtkGnTE27J5TnT4xCEFbyN56oinszyvLnl2fjuDznqlFSuW95QbSiHlwrq/juatLfoppuy+yhH/a9HnmBDHAQz5JDMr+3ir6s884BqKGcuSyT4A9licCgT01uyXlFSLKEX6/0LUFbXEFfBbAorLkGuBD7U8Dda+SrkQSbD/57tbaEMt5q1bodyE1Q/ETsbAXkO8f1CcZdtbhaHyPomnptlgjJh1s2gw+O5PICLXns2rl5bDV5ra2JQe5qvLzNT0v4REAXhs+eXjEaqzzpDKf6wuIDHRHUYHCqVFIoHSyy6JN3BdsUdRIrxiXViRe73IYEJZ+qd3YBuNbJZWAGsNhkOiK3aWR2zvOoamGWbY=]]></Encrypt></xml>"""
    msg_sign = "924eb9d7ce6f869d8ef8984ccae432094b22e606"
    timestamp = "1554272036"
    nonce = "1320562132"
    ret2, decryp_xml = decryption(from_xml, msg_sign, timestamp, nonce, "helloword")
    print(ret1, ret2, encrypt_xml, '\n\n\n', decryp_xml)
