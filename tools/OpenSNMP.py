# encoding: utf-8
# encoding: utf-8
import telnetlib
import threading
import time
import traceback

'''
用于给交换机批量开启SNMP
'''

switch_password = "123456"  # 密码


def conf_switch(ip):
    try:
        # 连接Telnet服务器
        # print('Connecting', ip, '...')
        tn = telnetlib.Telnet(ip, port=23, timeout=2)
        # tn.set_debuglevel(2)
        # 输入登录密码
        print('Connected. Logining...')
        tn.read_until('assword:'.encode('gbk'), 5)
        tn.write(switch_password.encode('gbk') + b'\n')
        # 登录完毕后执行命令
        tn.read_until('>'.encode('gbk'), 5)
        print('Login succeed! Configuring...')
        tn.write("sys\n".encode('gbk'))
        a = tn.read_until("]".encode('gbk'), 2)
        # print(a)
        tn.write("snmp-agent community read cipher gdgydx_pub\n".encode('gbk'))
        print('snmp-agent community read cipher gdgydx_pub')
        a = tn.read_until("]".encode('gbk'), 2)
        # print(a)
        tn.write("snmp-agent sys-info version all\n".encode('gbk'))
        print('snmp-agent sys-info version all')
        a = tn.read_until("]".encode('gbk'), 2)
        # print(a)
        # 保存
        tn.write("quit\n".encode('gbk'))
        print('quit')
        a = tn.read_until(">".encode('gbk'), 2)
        tn.write("save\n".encode('gbk'))
        print('save')
        a = tn.read_until("]".encode('gbk'), 10)
        # print(a)
        tn.write("y\n".encode('gbk'))
        print('y')
        a = tn.read_until(">".encode('gbk'), 10)
        # print(a)
        # 执行完毕后关闭连接
        tn.close()
        print(ip, 'configuration succeed!')
    except:
        a = traceback.format_exc()
        print(a[a.find('Error:') + 7:])


if __name__ == '__main__':
    #ips=["172.16.104.7","172.16.106.15","172.16.113.9","172.16.113.26","172.16.121.12"]
    ips=[]
    for a in range(101,115+1):
        ips.append("172.16."+str(a)+".253")
    for a in range(121,134+1):
        ips.append("172.16."+str(a)+".253")

    p=[]
    for a in ips:
        p.append(threading.Thread(target=conf_switch, name=a, args=(a,)))
    for a in p:
        a.start()
    for a in p:
        a.join()
