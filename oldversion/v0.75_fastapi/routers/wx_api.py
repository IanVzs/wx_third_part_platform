"""
微信公众平台相关请求处理

相关该类统一处理方法在routers中进行定义
"""

from lib import wx_api
from route_class import APIRouter, Request, Response, TimedRoute

router = APIRouter(route_class=TimedRoute)

@router.get("/wx_api/msg")
async def wx_api_msg(signature: str, echostr: str, timestamp: str, nonce: str):
    return "inY0Q6KlMT3SzwCft9j6gYYbKqsy7u07x2WcwdPUPLG"

@router.post("/wx_api/msg")
async def wx_api_msg(signature: str, timestamp: str, nonce: str, openid: str, encrypt_type: str=None, msg_signature: str=None, request: Request=None):
    data = await request.body()
    result = wx_api.deal_wx_api(data, msg_signature, timestamp, nonce)
    return result
