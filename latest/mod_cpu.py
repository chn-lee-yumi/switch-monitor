# encoding: utf-8
import telnetlib
from mod_snmp import *

'''
该模块用于获取交换机CPU信息
用法：cpu=getcpuinfo(ip)
ip为交换机的ip地址，如"172.16.101.4"
返回字符串，如"15%"
'''

switch_password = "123456"  # 密码
time_limit = 1  # 连接成功后超过这个时间还没获取到CPU数据的就放弃，秒


def getcpuinfo(ip):
    cpu = snmp(ip, "cpu_load_5min")  # 优先使用SNMP
    if cpu == "No Such Object available on this agent at this OID" or cpu == "":  # SNMP获取失败再使用telnet
        try:
            # 连接Telnet服务器
            tn = telnetlib.Telnet(ip, port=23, timeout=2)
            # 输入登录密码
            b = tn.read_until('assword:'.encode('gbk'), time_limit)
            if b == b"": return "0%"  # 有一台机（172.16.111.4）连上了什么数据也没有，专治这机
            tn.write(switch_password.encode('gbk') + b'\n')
            # 登录完毕后执行命令
            tn.read_until('>'.encode('gbk'), time_limit)
            command = "dis cpu\n"
            tn.write(command.encode('gbk'))
            cpu = tn.read_until(" in last 5 minutes".encode('gbk'), time_limit).decode('gbk')
            # 执行完毕后关闭连接
            tn.close()
            # 接下来获取cpu使用率信息
            if cpu.find("five minutes: ") > 0:  # 新机
                cpu = cpu[cpu.find("five minutes: ") + 14:cpu.find("five minutes: ") + 17]
                if cpu[:-1].find("%") == 1: cpu = cpu[:-1]  # 去掉个位数最后的空格
                return cpu
            else:  # 旧机
                cpu = cpu[-21:-18]  # 把百分号后面的都截掉
                if cpu.find(' ') == 0: cpu = cpu[1:]  # CPU使用率为个位数时，截掉前面的空格
                return cpu  # 返回字符串，带百分号的
        except:  # 连接失败返回"0%"
            return "0%"
    else:
        return cpu + "%"


if __name__ == '__main__':
    cpu = getcpuinfo("172.16.101.4")
    print(cpu)
