# encoding: utf-8
import netsnmp
from Config import SNMP_READ_COMMUNITY, SNMP_WRITE_COMMUNITY

'''
该模块用于使用SNMP获取交换机信息，调用了snmpwalk.exe，若是linux系统，修改一下SNMP_BIN_PATH即可。
##########Popen出错的检查一下SNMP_BIN_PATH##########
用法：snmp(ip, info)
ip为交换机的ip地址，如"172.16.101.4"
info为字符串，如"cpu_load_5min"、"memory_used_rate"、"total_memory"等等，具体看下面的代码。
返回字符串。
'''

'''
通用：
sysDescr    系统描述    1.3.6.1.2.1.1.1    系统的文字描述。包括系统中硬件类型、软件操作系统以及网络软件的名称和版本。
sysUpTime   运行时间    1.3.6.1.2.1.1.3    从系统网管部分启动以来运行的时间，单位为百分之一秒。
sysName     系统名称    1.3.6.1.2.1.1.5    （也就是交换机名称）
ifTable     接口信息    1.3.6.1.2.1.2.2.1

S2700：
hwCpuDevTable   CPU信息   1.3.6.1.4.1.2011.6.3.4.1    5s、1min、5min
hwEntityStateTable  实体状态    1.3.6.1.4.1.2011.5.25.31.1.1.1.1    详细看文档 5-实体CPU使用率 7-实体内存使用率 11-实体温度
hwSysReloadAction   重启  1.3.6.1.4.1.2011.5.25.19.1.3.2.0    写入3（类型为int），立即重启交换机


E152B：
实体状态 1.3.6.1.4.1.25506.2.6.1.1.1.1      6-实体CPU使用率 8-实体内存使用率 12-实体温度

E152:

'''

# I don't import SNMP library because none of them can run well in windows.
# 交换机型号：S2700、E152B

SNMP_OID_cpu_load_5min = "1.3.6.1.4.1.2011.6.1.1.1.4.0"
SNMP_OID_cpu_load_5min_3 = "1.3.6.1.4.1.25506.2.6.1.1.1.1.6.82"  # 是1min的，找不到5min
SNMP_OID_memory_used_rate = "1.3.6.1.4.1.25506.2.6.1.1.1.1.8.82"
# iso.3.6.1.4.1.25506.2.5.1.1.4.2.1.1.3.5373953.1.4
SNMP_OID_total_memory = "1.3.6.1.4.1.25506.2.6.1.1.1.1.10.82"
SNMP_OID_used_memory = "1.3.6.1.4.1.25506.2.6.1.1.1.1.11.2"
SNMP_OID_fan = ""
SNMP_OID_temperature = "1.3.6.1.4.1.2011.5.25.31.1.1.1.5"

S2700_cpu_load_5s = "1.3.6.1.4.1.2011.6.3.4.1.2"
S2700_cpu_load_1min = "1.3.6.1.4.1.2011.6.3.4.1.3"
S2700_cpu_load_5min = "1.3.6.1.4.1.2011.6.3.4.1.4"
S2700_reboot = "1.3.6.1.4.1.2011.5.25.19.1.3.2.0"
S2700_cpu_load_now = "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.5"  # 实体CPU使用率
S2700_mem_usage_now = "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.7"  # 实体内存使用率
S2700_up_time = "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.10"  # 实体启动时间
S2700_temperature = "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11"  # 实体温度

# iso.3.6.1.2.1.1 交换机信息
# 1.3.6.1.2.1.1.5 设备名

# 接口OID
OID_IF = "1.3.6.1.2.1.2.2.1"
OID_IP = "1.3.6.1.4.1.2011.5.25.41.1.2.1.1"  # 接口IP
OID_IF_INDEX = "1.3.6.1.2.1.2.2.1.1"  # 接口索引


# iso.3.6.1.2.1.2.2.1.2.x 接口名
# iso.3.6.1.2.1.2.2.1.8.x 接口状态，1为up，0为down
# iso.3.6.1.2.1.2.2.1.10.x 入方向总字节数
# iso.3.6.1.2.1.2.2.1.16.x 出方向总字节数
# TODO：加入错误包统计

# TODO: 根据型号使用对应oid，oid从数据库（新建一个名字为mib的数据表）读取。（网页要提供修改oid的页面）

def SnmpWalk(ip, model, info):
    return_list = False
    oid = ''
    if info == "cpu_load" and model.find("S") == 0:
        oid = "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.5"  # 华为实体CPU使用率
        return_list = True
    if info == "cpu_load" and model.find("E") == 0:
        oid = "1.3.6.1.4.1.25506.2.6.1.1.1.1.6"  # 华三实体CPU使用率
        return_list = True
    if info == "mem_used" and model.find("S") == 0:
        oid = "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.7"  # 华为实体内存使用率
        return_list = True
    if info == "mem_used" and model.find("E") == 0:
        oid = "1.3.6.1.4.1.25506.2.6.1.1.1.1.8"  # 华三实体内存使用率
        return_list = True
    if info == "mem_used" and model.find("S8610") == 0:
        oid = "1.3.6.1.4.1.4881.1.1.10.2.35.1.1.1.3.1"  # 锐捷实体内存使用率
    if info == "temp" and model.find("S") == 0:
        oid = "1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11"  # 华为实体温度
        return_list = True
    if info == "temp" and model.find("E") == 0:
        oid = "1.3.6.1.4.1.25506.2.6.1.1.1.1.12"  # 华三实体温度
        return_list = True
    if info == "temp" and model.find("S8610") == 0:
        oid = "1.3.6.1.4.1.4881.1.1.10.2.1.1.16"  # 锐捷实体温度
    if info == "up_time": oid = "1.3.6.1.2.1.1.3"  # 运行时间
    if info == "if_name": oid = "1.3.6.1.2.1.2.2.1.2"  # 接口名字
    if info == "if_index": oid = "1.3.6.1.2.1.2.2.1.1"
    if info == "if_status": oid = "1.3.6.1.2.1.2.2.1.8"  # 接口状态 up(1),down(2),testing(3),unknown(4),dormant(5),notPresent(6),lowerLayerDown(7)
    if info == "if_ip": oid = "1.3.6.1.4.1.2011.5.25.41.1.2.1.1.1"  # 接口IP
    if info == "if_ipindex": oid = "1.3.6.1.4.1.2011.5.25.41.1.2.1.1.2"  # 接口索引
    if info == "if_ipmask": oid = "1.3.6.1.4.1.2011.5.25.41.1.2.1.1.3"  # 接口子网掩码
    if info == "if_in": oid = "1.3.6.1.2.1.31.1.1.1.6"  # 该接口入方向通过的总字节数 1.3.6.1.2.1.2.2.1.10（32位） 1.3.6.1.2.1.31.1.1.1.6 (增强版，64位)
    if info == "if_out": oid = "1.3.6.1.2.1.31.1.1.1.10"  # 该接口出方向通过的总字节数 1.3.6.1.2.1.2.2.1.16（32位） 1.3.6.1.2.1.31.1.1.1.10 (增强版，64位)
    if info == "if_uptime": oid = "1.3.6.1.2.1.2.2.1.9"  # 1.3.6.1.2.1.2.2.1.9.6 端口uptime
    if info == "if_descr": oid = "1.3.6.1.2.1.31.1.1.1.18"  # 接口描述
    if info == "name": oid = "1.3.6.1.2.1.1.5"  # 设备名

    try:
        b = netsnmp.snmpwalk('.' + oid, DestHost=ip, Version=2, Community=SNMP_READ_COMMUNITY)
        if len(b) == 0:
            return "获取失败"
        if return_list == True:
            return max(map(lambda x: int(x.decode('utf-8')), b))
        if len(b) == 1:
            return b[0].decode('utf-8')
        return list(map(lambda x: x.decode('utf-8'), b))
    except:
        try:
            b = netsnmp.snmpwalk('.' + oid, DestHost=ip, Version=2, Community=SNMP_READ_COMMUNITY)
            if len(b) == 0:
                return "获取失败"
            if return_list == True:
                return max(map(lambda x: int(x.decode('utf-8')), b))
            if len(b) == 1:
                return b[0].decode('utf-8')
            return list(map(lambda x: x.decode('utf-8'), b))
        except:
            return "获取失败"


def SnmpSet(ip, model, info):
    pass
    '''
    if info == "reboot" and model == "S2700":
        oid = "1.3.6.1.4.1.2011.5.25.19.1.3.2.0"
        type = 'i'
        value = "3"
    try:
        a = subprocess.Popen(
            [SNMP_SET_BIN_PATH, "-O", "qv", "-t", "1", "-r", "3", "-v", SNMP_VER, "-c", SNMP_WRITE_COMMUNITY, ip, oid,
             type, value], bufsize=0, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        # snmpwalk -v 2c -c gdgydx_pub 172.16.111.1 1.3.6.1.2.1.2.2.1.2
        # snmpwalk -v 2c -c gdgydx_pub 172.16.111.1 1.3.6.1.2.1.2.2.1.10
        b = a.stdout.read().decode('utf-8').strip('\n')
        # 下面清空流，防止爆内存，参考http://blog.csdn.net/pugongying1988/article/details/54616797
        if a.stdin:
            a.stdin.close()
        if a.stdout:
            a.stdout.close()
        if a.stderr:
            a.stderr.close()
        try:
            a.kill()
        except OSError:
            pass
        # 下面返回数据
        if b == "": return "获取失败"
        if b.find("No Such Object") >= 0: return "设备不支持"
        return b
    except:
        return "设置失败"
    '''


if __name__ == '__main__':  # SNMP测试
    print(SnmpWalk("172.16.102.253", "S2700", "if_name"))
