import socket

from Config import *

socket.setdefaulttimeout(TCPING_TIMEOUT)


def tcpingip(ip):
    # 错误码表：
    # http://blog.chinaunix.net/uid-116213-id-3376727.html
    # http://www.cnblogs.com/onroad/archive/2009/08/10/1543164.html
    a = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    b = a.connect_ex((ip, 999))  # 随便连接个端口
    a.close()
    if b == 10061 or b == 111 or b == 0: return True  # 拒绝连接(win)或拒绝连接(linux)或连接成功
    return False


def checkswitch(ip):  # 检测交换机在线情况的函数，这里用TCP检测两次
    if tcpingip(ip): return True
    return tcpingip(ip)
