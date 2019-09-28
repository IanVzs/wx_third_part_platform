import requests
url = "http://127.0.0.1:8979/wx_service/send_template_msg"
data = {
    "app_id": "waa111asdw43f3b5",
}
requests.request("POST", url, json=data)
