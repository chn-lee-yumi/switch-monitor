# encoding: utf-8
import socket

'''
该模块用于检测某个ip是否在线
用法：a=tcpingip(ip)
若在线则返回True，否则返回False
'''

tcpingtimeout = 3  # tcping超时时间，秒
socket.setdefaulttimeout(tcpingtimeout)


def tcpingip(ip):
    a = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    b = a.connect_ex((ip, 6666))
    a.close()
    if b == 10061 or b == 0: return True  # 拒绝连接或连接成功
    return False
