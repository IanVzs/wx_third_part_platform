# -*-coding: utf-8-*-

from log import *

test_data_dict = {
    # func_name : {inputs}
    "do_authorizer_access_token": {
        "dict_data": {
            "authorization_info": {
                "authorizer_appid":
                "waa111asdw43f3b5",
                "authorizer_access_token":
                "QXjUqNqfYVH0yBE1iI_7vuN_9gQbpjfK7hYwJ3P7xOa88a89-Aga5x1NMYJyB8G2yKt1KCl0nPC3W9GJzw0Zzq_dBxc8pxIGUNi_bFes0qM",
                "expires_in":
                7200,
                "authorizer_refresh_token":
                "dTo-YCXPL4llX-u1W1pPpnp8Hgm4wpJtlR6iV0doKdY",
                "func_info": [{
                    "funcscope_category": {
                        "id": 1
                    }
                }, {
                    "funcscope_category": {
                        "id": 2
                    }
                }, {
                    "funcscope_category": {
                        "id": 3
                    }
                }]
            }
        },
        "auth_code": 'preauthcode@@@GMp8UGsz8gt30hD9tnyk9W5bruUQXg1RLKDOibduV5VYipBiDX',
        "test_data": {
            "authorizer_info": {
                "nick_name": "这样才好",
                "head_img": "http://wx.qlogo.cn/mmopen/GPy",
                "service_type_info": {
                    "id": 2
                },
                "verify_type_info": {
                    "id": 0
                },
                "user_name": "gh_eb5e3a772040",
                "principal_name": "呼拉拉拉拉",
                "business_info": {
                    "open_store": 0,
                    "open_scan": 0,
                    "open_pay": 0,
                    "open_card": 0,
                    "open_shake": 0
                },
                "alias": "paytest01",
                "qrcode_url": "URL",
            },
            "authorization_info": {
                "authorization_appid":
                "waa111asdw43f3b5",
                "func_info": [{
                    "funcscope_category": {
                        "id": 1
                    }
                }, {
                    "funcscope_category": {
                        "id": 2
                    }
                }, {
                    "funcscope_category": {
                        "id": 3
                    }
                }]
            }
        },
    },
    "do_refresh_info": {
        "info_dict_data": {
            "authorizer_info": {
                "nick_name": "这样才好",
                "head_img": "http://wx.qlogo.cn/mmopen/GPy",
                "service_type_info": {
                    "id": 2
                },
                "verify_type_info": {
                    "id": 0
                },
                "user_name": "gh_eb5e3a772040",
                "principal_name": "呼拉拉拉拉",
                "business_info": {
                    "open_store": 0,
                    "open_scan": 0,
                    "open_pay": 0,
                    "open_card": 0,
                    "open_shake": 0
                },
                "alias": "paytest01",
                "qrcode_url": "nihaoawohenhao",
            },
            "authorization_info": {
                "authorizer_appid":
                "waa111asdw43f3b5",
                "func_info": [{
                    "funcscope_category": {
                        "id": 1
                    }
                }, {
                    "funcscope_category": {
                        "id": 2
                    }
                }, {
                    "funcscope_category": {
                        "id": 3
                    }
                }]
            }
        },
    }
}


def do_test(classs):
    for name, value in classs.__dict__.items():
        if isinstance(value, type(lambda x: 0)) and name in test_data_dict:
            rsp_dict = value(**test_data_dict[name])
            if rsp_dict.get("sign"):
                print(name, "success")
                log_info(name + ":::" + str(rsp_dict))
            else:
                print(name, "faild")
                log_error(name + "..." + str({"fail_msg": rsp_dict.get("msg")}))
