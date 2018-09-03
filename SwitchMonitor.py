#!/usr/bin/python3
#  encoding: utf-8

'''
说明：该脚本用于启动交换机监控。
'''

from Controller import start_switch_monitor

start_switch_monitor()

'''
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from Controller import app

http_server = HTTPServer(WSGIContainer(app))
http_server.listen(80)
IOLoop.instance().start()
'''
