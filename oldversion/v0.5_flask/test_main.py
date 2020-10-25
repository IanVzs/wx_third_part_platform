# -*-coding: utf-8-*-

from blueprints import wx_service
from blueprints import wx_api
from lib import authorization
from lib.wx_service import WeChat_OAP
from lib.wx_workers import TEST_ZYClient

from tests import test_wx_service, test_authorizer

test_wx_service.do_test(wx_api)
test_wx_service.do_test(wx_service)
#test_wx_service.do_test(WeChat_OAP)
test_authorizer.do_test(authorization)
