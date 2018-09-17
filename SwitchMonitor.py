#!/usr/bin/python3
#  encoding: utf-8
import time

'''
说明：该脚本用于启动交换机监控。
'''

from Controller import start_switch_monitor, start_web

start_switch_monitor()
start_web()

while 1:
    time.sleep(99999)
