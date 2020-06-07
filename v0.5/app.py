#!flask/bin/python
# -*-coding: utf-8-*-

import traceback
import json
from flask import Flask, jsonify, abort, request, make_response
from flask_cors import CORS
from werkzeug.routing import BaseConverter

from log import logger

app = Flask(__name__, static_url_path='')
app.debug = True
app.use_debugger = False
app.use_reloader = False
app.config['PROPAGATE_EXCEPTIONS'] = True
app.url_map.strict_slashes = False
CORS(app)

import config

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app.url_map.converters['regex'] = RegexConverter


@app.errorhandler(Exception)
def handle_general_error(e):
    body = str(e) + '\t'
    body += traceback.format_exc()
    error_data = {
        'mail_to': 'server_monitor@feedback.com',
        'title': u'wx_third_part_platform Error',
        'body': body
    }
    logger.error(u'logstash###wx_third_part_platform###ERROR###{}'.format(json.dumps(error_data, ensure_ascii=False)))
    return jsonify(message="内部错误", status=1), 500


app.register_error_handler(500, handle_general_error)


@app.route('/3727918463.txt')
def wxfile():
    return app.send_static_file('3727918463.txt')


@app.route("/")
def main():
    return make_response(jsonify({'version': 'wx_third_part_platform-20190408'}))


@app.route("/favicon.ico")
def favicon():
    return app.send_static_file('favicon.ico')


@app.route("/monitor")
def hello():
    a = {"a": 1}
    return make_response(jsonify(a))
