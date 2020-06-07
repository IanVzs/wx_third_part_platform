"""微信公众平台相关请求处理"""
from app_setting import app



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


@app.post("/wx_api/msg")
async def wx_api_msg():
    print(appid)
    import ipdb; ipdb.set_trace()
    postdata, msg_signature, timestamp, nonce, auth_code, ex = get_paras()

    return "hi"
