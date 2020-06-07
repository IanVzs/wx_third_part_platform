import aiohttp
from fastapi import FastAPI, Request, Response
#from app_setting import app

from lib import wx_api

app = FastAPI()

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

@app.get("/")
async def read_main():
    async with aiohttp.ClientSession() as session:
        a = await fetch(session, 'http://127.0.0.1/favicon.ico')
    return {"msg": "wx_third_part_platform v0.75"}

@app.get("/favicon.ico")
async def favicon_ico():
    return "hi"

@app.get("/wx_api/msg")
async def wx_api_msg(signature: str, echostr: str, timestamp: str, nonce: str):
    return "inY0Q6KlMT3SzwCft9j6gYYbKqsy7u07x2WcwdPUPLG"
@app.post("/wx_api/msg")
async def wx_api_msg(signature: str, timestamp: str, nonce: str, openid: str, encrypt_type: str=None, msg_signature: str=None, request: Request=None):
    data = await request.body()
    from lib import wx_api
    result = wx_api.deal_wx_api(data, msg_signature, timestamp, nonce)
    return result
