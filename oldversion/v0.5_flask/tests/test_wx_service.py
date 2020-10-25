# -*-coding: utf-8-*-

from log import *
access_token = "22_c1eUzP0QOqjJwdT6W9Hu3tPzSDVkfqK5J2gZo7k5tvyBd6lm5p6cKSp6CwDUyXh8JBaOLtE6kbBRfIakt5WIXJvB2uaQPCM4C2q41Vul1hV-_Yuqa7CtqkUO7f77950P1vXfi51AjdWR1Xl4XYBdAEDCDG"
test_data_dict = {
    "do_get_auth_info": {
        "app_id": "5c99b1adb60c48238d6d9f48",
    },
    #    "do_auth": {
    #        "app_id": "5c99b1adb60c48238d6d9f48",
    #        "pre_auth_code": "preauthcode@@@GMp8UGsz8gt30hD9tnyk9W5bruUQXg1RLKDOibduV5VYipBiDX",
    #    },
    #    "do_get_auth_info": {
    #        "app_id": "5c99b1adb60c48238d6d9f48",
    #    },
    #    "do_exchange": {
    #        "app_id": "5c99b1adb60c48238d6d9f48",
    #    },
    #    "do_get_menu": {
    #        "url": "https://api.weixin.qq.com/cgi-bin/menu/get?access_token={}".format(access_token),
    #        "data": 1
    #    },
    #    "do_create_menu": {
    #        "url": 'https://api.weixin.qq.com/cgi-bin/menu/create?access_token={}'.format(access_token),
    #        "data": {
    #            "action": "create",
    #            "menu_data": {
    #                "button": [{
    #                    'type': 'click',
    #                    'name': '用药指导',
    #                    'key': 'Get_This_Guy',
    #                    'sub_button': []
    #                }, {
    #                    'name':
    #                    'Menu',
    #                    'sub_button': [{
    #                        'type': 'view',
    #                        'name': '官网',
    #                        'url': 'https://www.zuasdhakqcheg.com/',
    #                        'sub_button': []
    #                    }, {
    #                        'type': 'miniprogram',
    #                        'name': '小程序',
    #                        'url': 'https://www.zuasdhakqcheg.com/',
    #                        'sub_button': [],
    #                        'appid': 'wxacd37ff25cd2ed6a',
    #                        'pagepath': 'pages'
    #                    }, {
    #                        'type': 'scancode_waitmsg',
    #                        'name': '扫一扫',
    #                        'key': 'Scan_Wait_Tem',
    #                        'sub_button': []
    #                    }, {
    #                        'type': 'scancode_push',
    #                        'name': '扫码',
    #                        'key': 'Scan_Push',
    #                        'sub_button': []
    #                    }]
    #                }]
    #            },
    #            "sub_data": {
    #                "type": "view",
    #                "name": "测试替换",
    #                "url": "https://www.zuasdhakqcheg.com",
    #                "sub_button": []
    #            },
    #            "pos": [1, 1]
    #        },
    #    },
    #    "do_fusion_menu": {
    #        "url": {
    #            'menu': {
    #                'button': [{
    #                    'type': 'click',
    #                    'name': '用药指导',
    #                    'key': 'Get_This_Guy',
    #                    'sub_button': []
    #                }, {
    #                    'name':
    #                    'Menu',
    #                    'sub_button': [{
    #                        'type': 'view',
    #                        'name': '官网',
    #                        'url': 'https://www.zuasdhakqcheg.com/',
    #                        'sub_button': []
    #                    }, {
    #                        'type': 'miniprogram',
    #                        'name': '小程序',
    #                        'url': 'https://www.zuasdhakqcheg.com/',
    #                        'sub_button': [],
    #                        'appid': 'wxacd37ff25cd2ed6a',
    #                        'pagepath': 'pages'
    #                    }, {
    #                        'type': 'scancode_waitmsg',
    #                        'name': '扫一扫',
    #                        'key': 'Scan_Wait_Tem',
    #                        'sub_button': []
    #                    }, {
    #                        'type': 'scancode_push',
    #                        'name': '扫码',
    #                        'key': 'Scan_Push',
    #                        'sub_button': []
    #                    }]
    #                }]
    #            }
    #        },
    #        #"data": {"action": "create", "menu_data": {"button": {}}}
    #        #"data": {"action": "add", "menu_data": {"button": {}}, "sub_data": {"type":"view","name":"测试增加","url":"https://www.zuasdhakqchegtest.com","sub_button":[]}, "pos": [1, 2]}
    #        "data": {
    #            "action": "replace",
    #            "menu_data": {
    #                "button": {}
    #            },
    #            "sub_data": {
    #                "type": "view",
    #                "name": "测试增加",
    #                "url": "https://www.zuasdhakqchegtest.com",
    #                "sub_button": []
    #            },
    #            "pos": [2, 1]
    #        }
    #    },
}


def do_test(classs):
    for name, value in classs.__dict__.items():
        if isinstance(value, type(lambda x: 0)) and name in test_data_dict:
            if classs.__name__ == "WeChat_OAP":
                fail, wrapped = value(
                    classs("third_part_platform", "appid_test"), test_data_dict[name]["url"],
                    test_data_dict[name]["data"])
            else:
                fail, wrapped = value(test_data_dict[name], True)
            if not fail:
                print(name, "success")
                log_info(name + ":::" + str(wrapped))
            else:
                print(name, "faild")
                log_error(name + "..." + str({"fail_list": fail}))
