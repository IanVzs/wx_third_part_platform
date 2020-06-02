import requests
url = "http://127.0.0.1:8979/wx_service/get_auth_access_token"
data = {
    "app_id": "waa111asdw43f3b5",
}
requests.request("POST", url, json=data)
