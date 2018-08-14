# encoding: utf-8
import platform
import subprocess
from Config import SNMP_READ_COMMUNITY, SNMP_WRITE_COMMUNITY

# TODO: SNMP模块现在在windows下会有奇怪的bug，popen的时候只要加了-O qv就没有回显，但在cmd中执行命令是有回显的。

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
SNMP_TIMEOUT = "1"
SNMP_RETRY_TIMES = "3"
SNMP_VER = "2c"
if platform.system() == "Windows":
    SNMP_WALK_BIN_PATH = ".\\bin\\snmpwalk"
    SNMP_SET_BIN_PATH = ".\\bin\\snmpset"
else:
    SNMP_WALK_BIN_PATH = "snmpwalk"
    SNMP_SET_BIN_PATH = "snmpset"

SNMP_OID_cpu_load_5min = "1.3.6.1.4.1.2011.6.1.1.1.4.0"

SNMP_OID_cpu_load_5min_3 = "1.3.6.1.4.1.25506.2.6.1.1.1.1.6.82"  # 是1min的，找不到5min
SNMP_OID_memory_used_rate = "1.3.6.1.4.1.25506.2.6.1.1.1.1.8.82"
# iso.3.6.1.4.1.25506.2.5.1.1.4.2.1.1.3.5373953.1.4
SNMP_OID_total_memory = "1.3.6.1.4.1.25506.2.6.1.1.1.1.10.82"
SNMP_OID_used_memory = "1.3.6.1.4.1.25506.2.6.1.1.1.1.11.2"
SNMP_OID_fan = ""
SNMP_OID_temperature = "1.3.6.1.4.1.2011.5.25.31.1.1.1.5"

# 以下是新内容
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
        a = subprocess.Popen(
            [SNMP_WALK_BIN_PATH, "-O", "qv", "-t", "1", "-r", "3", "-v", SNMP_VER, "-c", SNMP_READ_COMMUNITY, ip, oid],
            bufsize=0, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        b = a.stdout.read().decode('utf-8').strip('\n')
        if b == "": return "获取失败"
        if b.find("No Such Object") >= 0: return "设备不支持"
        if return_list == True:
            return max(map(int, b.split()))  # 仅返回最大值
        # 下面清空流，防止爆内存，参考http://blog.csdn.net/pugongying1988/article/details/54616797
        # 似乎没用？？？？？？？？？？？？？？？
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
        return b
    except:
        return "获取失败"


def SnmpSet(ip, model, info):
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
    if info == "test":  # ip="demo.snmplabs.com"
        b = subprocess.Popen(
            [SNMP_WALK_BIN_PATH, "-O", "qv", "-t", "5", "-r", "2", "-v", SNMP_VER, "-c", "index", "demo.snmplabs.com",
             "1.3.6.1.4.1.20408.999.1.1.1"], bufsize=0, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    else:
        oid = get_oid(model, info)
        b = subprocess.Popen(
            [SNMP_WALK_BIN_PATH, "-O", "qv", "-t", SNMP_TIMEOUT, "-r", SNMP_RETRY_TIMES, "-v", SNMP_VER, "-c",
             SNMP_COMMUNITY, ip, oid], shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    return b.stdout.read().decode('utf-8')[:-1]  # 去掉回车和换行符
'''

'''
def get_oid(model, info):
    conn = sqlite3.connect("data.db")
    conn.close()
'''

if __name__ == '__main__':  # SNMP测试
    # print(SnmpWalk("172.16.101.1", "S2700", "up_time"))
    ip = "172.16.254.1"
    oid = "1.3.6.1.2.1.2.2.1.9"
    a = subprocess.Popen(
        [SNMP_WALK_BIN_PATH, "-O", "qv", "-t", "1", "-r", "3", "-v", SNMP_VER, "-c", SNMP_READ_COMMUNITY, ip, oid],
        bufsize=0, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # a = subprocess.Popen(
    #    [SNMP_WALK_BIN_PATH, "-O", "qv", "-t", "5", "-r", "2", "-v", SNMP_VER, "-c", "index", "demo.snmplabs.com",
    #     "1.3.6.1.4.1.20408.999.1.1.1"], bufsize=0, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    #    stderr=subprocess.PIPE)
    '''a = subprocess.Popen(
    [SNMP_WALK_BIN_PATH, "-t", SNMP_TIMEOUT, "-r", SNMP_RETRY_TIMES, "-v", SNMP_VER, "-c",
     SNMP_READ_COMMUNITY, "172.16.254.1", "1.3.6.1.2.1.2.2.1.9"], bufsize=0, shell=False,stdin=subprocess.PIPE,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE)'''
    # a = subprocess.Popen(
    #    [SNMP_SET_BIN_PATH, "-O", "qv", "-t", "1", "-r", "3", "-v", SNMP_VER, "-c", SNMP_WRITE_COMMUNITY, "172.16.102.1", "1.3.6.1.4.1.2011.5.25.19.1.3.2.0", "i",
    #     "3"], bufsize=0, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # a = a.stdout.read().decode()

    print(a.stdout.read().decode())
    print("*" * 50)

    '''
    # 重启代码
    b = subprocess.Popen(
        [SNMP_SET_BIN_PATH, "-O", "qv", "-t", SNMP_TIMEOUT, "-r", SNMP_RETRY_TIMES, "-v", SNMP_VER, "-c",
         SNMP_WRITE_COMMUNITY, "172.16.102.1", "1.3.6.1.4.1.2011.5.25.19.1.3.2.0","int","3"], shell=False, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    '''

    '''
    USAGE: snmpwalk [OPTIONS] AGENT [OID]

      Version:  5.7
      Web:      http://www.net-snmp.org/
      Email:    net-snmp-coders@lists.sourceforge.net

    OPTIONS:
      -h, --help            display this help message
      -H                    display configuration file directives understood
      -v 1|2c|3             specifies SNMP version to use
      -V, --version         display package version number
    SNMP Version 1 or 2c specific
      -c COMMUNITY          set the community string
    SNMP Version 3 specific
      -a PROTOCOL           set authentication protocol (MD5|SHA)
      -A PASSPHRASE         set authentication protocol pass phrase
      -e ENGINE-ID          set security engine ID (e.g. 800000020109840301)
      -E ENGINE-ID          set context engine ID (e.g. 800000020109840301)
      -l LEVEL              set security level (noAuthNoPriv|authNoPriv|authPriv)
      -n CONTEXT            set context name (e.g. bridge1)
      -u USER-NAME          set security name (e.g. bert)
      -x PROTOCOL           set privacy protocol (DES)
      -X PASSPHRASE         set privacy protocol pass phrase
      -Z BOOTS,TIME         set destination engine boots/time
    General communication options
      -r RETRIES            set the number of retries
      -t TIMEOUT            set the request timeout (in seconds)
    Debugging
      -d                    dump input/output packets in hexadecimal
      -D[TOKEN[,...]]       turn on debugging output for the specified TOKENs
                               (ALL gives extremely verbose debugging output)
    General options
      -m MIB[:...]          load given list of MIBs (ALL loads everything)
      -M DIR[:...]          look in given list of directories for MIBs
        (default: c:/usr/share/snmp/mibs)
      -P MIBOPTS            Toggle various defaults controlling MIB parsing:
                              u:  allow the use of underlines in MIB symbols
                              c:  disallow the use of "--" to terminate comments
                              d:  save the DESCRIPTIONs of the MIB objects
                              e:  disable errors when MIB symbols conflict
                              w:  enable warnings when MIB symbols conflict
                              W:  enable detailed warnings when MIB symbols conflict
                              R:  replace MIB symbols from latest module
      -O OUTOPTS            Toggle various defaults controlling output display:
                              0:  print leading 0 for single-digit hex characters
                              a:  print all strings in ascii format
                              b:  do not break OID indexes down
                              e:  print enums numerically
                              E:  escape quotes in string indices
                              f:  print full OIDs on output
                              n:  print OIDs numerically
                              q:  quick print for easier parsing
                              Q:  quick print with equal-signs
                              s:  print only last symbolic element of OID
                              S:  print MIB module-id plus last element
                              t:  print timeticks unparsed as numeric integers
                              T:  print human-readable text along with hex strings
                              u:  print OIDs using UCD-style prefix suppression
                              U:  don't print units
                              v:  print values only (not OID = value)
                              x:  print all strings in hex format
                              X:  extended index format
      -I INOPTS             Toggle various defaults controlling input parsing:
                              b:  do best/regex matching to find a MIB node
                              h:  don't apply DISPLAY-HINTs
                              r:  do not check values for range/type legality
                              R:  do random access to OID labels
                              u:  top-level OIDs must have '.' prefix (UCD-style)
                              s SUFFIX:  Append all textual OIDs with SUFFIX before parsing
                              S PREFIX:  Prepend all textual OIDs with PREFIX before parsing
      -L LOGOPTS            Toggle various defaults controlling logging:
                              e:           log to standard error
                              o:           log to standard output
                              n:           don't log at all
                              f file:      log to the specified file
                              s facility:  log to syslog (via the specified facility)

                              (variants)
                              [EON] pri:   log to standard error, output or /dev/null for level 'pri' and above
                              [EON] p1-p2: log to standard error, output or /dev/null for levels 'p1' to 'p2'
                              [FS] pri token:    log to file/syslog for level 'pri' and above
                              [FS] p1-p2 token:  log to file/syslog for levels 'p1' to 'p2'
      -C APPOPTS            Set various application specific behaviours:
                              p:  print the number of variables found
                              i:  include given OID in the search range
                              I:  don't include the given OID, even if no results are returned
                              c:  do not check returned OIDs are increasing
                              t:  Display wall-clock time to complete the walk
                              T:  Display wall-clock time to complete each request
                              E {OID}:  End the walk at the specified OID
    '''
    '''
    USAGE: snmpset [OPTIONS] AGENT OID TYPE VALUE [OID TYPE VALUE]...

      Version:  5.5
      Web:      http://www.net-snmp.org/
      Email:    net-snmp-coders@lists.sourceforge.net

    OPTIONS:
      -h, --help            display this help message
      -H                    display configuration file directives understood
      -v 1|2c|3             specifies SNMP version to use
      -V, --version         display package version number
    SNMP Version 1 or 2c specific
      -c COMMUNITY          set the community string
    SNMP Version 3 specific
      -a PROTOCOL           set authentication protocol (MD5|SHA)
      -A PASSPHRASE         set authentication protocol pass phrase
      -e ENGINE-ID          set security engine ID (e.g. 800000020109840301)
      -E ENGINE-ID          set context engine ID (e.g. 800000020109840301)
      -l LEVEL              set security level (noAuthNoPriv|authNoPriv|authPriv)
      -n CONTEXT            set context name (e.g. bridge1)
      -u USER-NAME          set security name (e.g. bert)
      -x PROTOCOL           set privacy protocol (DES)
      -X PASSPHRASE         set privacy protocol pass phrase
      -Z BOOTS,TIME         set destination engine boots/time
    General communication options
      -r RETRIES            set the number of retries
      -t TIMEOUT            set the request timeout (in seconds)
    Debugging
      -d                    dump input/output packets in hexadecimal
      -D TOKEN[,...]        turn on debugging output for the specified TOKENs
                               (ALL gives extremely verbose debugging output)
    General options
      -m MIB[:...]          load given list of MIBs (ALL loads everything)
      -M DIR[:...]          look in given list of directories for MIBs
      -P MIBOPTS            Toggle various defaults controlling MIB parsing:
                              u:  allow the use of underlines in MIB symbols
                              c:  disallow the use of "--" to terminate comments
                              d:  save the DESCRIPTIONs of the MIB objects
                              e:  disable errors when MIB symbols conflict
                              w:  enable warnings when MIB symbols conflict
                              W:  enable detailed warnings when MIB symbols conflict
                              R:  replace MIB symbols from latest module
      -O OUTOPTS            Toggle various defaults controlling output display:
                              0:  print leading 0 for single-digit hex characters
                              a:  print all strings in ascii format
                              b:  do not break OID indexes down
                              e:  print enums numerically
                              E:  escape quotes in string indices
                              f:  print full OIDs on output
                              n:  print OIDs numerically
                              q:  quick print for easier parsing
                              Q:  quick print with equal-signs
                              s:  print only last symbolic element of OID
                              S:  print MIB module-id plus last element
                              t:  print timeticks unparsed as numeric integers
                              T:  print human-readable text along with hex strings
                              u:  print OIDs using UCD-style prefix suppression
                              U:  don't print units
                              v:  print values only (not OID = value)
                              x:  print all strings in hex format
                              X:  extended index format
      -I INOPTS             Toggle various defaults controlling input parsing:
                              b:  do best/regex matching to find a MIB node
                              h:  don't apply DISPLAY-HINTs
                              r:  do not check values for range/type legality
                              R:  do random access to OID labels
                              u:  top-level OIDs must have '.' prefix (UCD-style)
                              s SUFFIX:  Append all textual OIDs with SUFFIX before parsing
                              S PREFIX:  Prepend all textual OIDs with PREFIX before parsing
      -L LOGOPTS            Toggle various defaults controlling logging:
                              e:           log to standard error
                              o:           log to standard output
                              n:           don't log at all
                              f file:      log to the specified file
                              s facility:  log to syslog (via the specified facility)

                              (variants)
                              [EON] pri:   log to standard error, output or /dev/null for level 'pri' and above
                              [EON] p1-p2: log to standard error, output or /dev/null for levels 'p1' to 'p2'
                              [FS] pri token:    log to file/syslog for level 'pri' and above
                              [FS] p1-p2 token:  log to file/syslog for levels 'p1' to 'p2'
      -C APPOPTS            Set various application specific behaviours:
                              q:  don't print results on success

      TYPE: one of i, u, t, a, o, s, x, d, b
            i: INTEGER, u: unsigned INTEGER, t: TIMETICKS, a: IPADDRESS
            o: OBJID, s: STRING, x: HEX STRING, d: DECIMAL STRING, b: BITS
            U: unsigned int64, I: signed int64, F: float, D: double
    '''
