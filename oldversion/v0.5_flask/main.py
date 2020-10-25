# -*-coding: utf-8-*-

from gevent import monkey
monkey.patch_all()

import sys
import atexit
# import singleton
from gevent import pywsgi

import config
from app import app
from blueprints.wx_api import WXAPI
from blueprints.wx_service import WXSERVICE
# app.register_blueprint()
app.register_blueprint(WXAPI)
app.register_blueprint(WXSERVICE)

# atexit.register(singleton.save)

if __name__ == '__main__':
    # singleton.load()
    server = pywsgi.WSGIServer((config.HOST, config.PORT), app)
    sys.stderr.write("server started %s:%s\n" % (config.HOST, config.PORT))
    server.serve_forever()
