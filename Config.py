# encoding: utf-8
# =============网页参数=============
USE_HTTPS = False  # 是否使用HTTPS（不使用HTTP）
ADMIN_USERNAME = 'admin'  # 管理员用户名
ADMIN_PASSWORD = '123456'  # 管理员密码
WEB_USERNAME = 'user'  # 网页登录的用户名
WEB_PASSWORD = '12345'  # 网页登录的密码
WEB_PORT = 80  # http端口

# =============扫描参数=============
TCPING_TIMEOUT = 2  # tcping超时时间，秒
SCAN_THREADS = 20  # 每个扫描进程的扫描线程数
SCAN_PROCESS = 4  # 扫描进程数

# =============监控参数=============
SEND_MSG_DELAY = 5  # 微信通知的延迟，分钟
WEIXIN_STAT_TIME_H = 18  # 发送微信统计的时
WEIXIN_STAT_TIME_M = 0  # 发送微信统计的分
SW_REBOOT_TIME_H = 4  # 自动重启交换机的时
SW_REBOOT_TIME_M = 0  # 自动重启交换机的分
CPU_THRESHOLD = 80  # CPU过载阈值
MEM_THRESHOLD = 80  # 内存过高阈值
TEMP_THRESHOLD = 60  # 温度过高阈值
IF_SPEED_THRESHOLD = 0.8  # 端口流量阈值
DATA_RECORD_SAVED_DAYS = 7  # 历史记录保留天数
SCAN_REBOOT_HOURS = 6  # 扫描进程重启时间间隔，小时。参考：使用lib模式，8G内存的机器需要8小时重启一次。

# =============SNMP参数=============
SNMP_MODE = "bin"  # SNMP模式，lib或bin。
# 如果是lib，则调用netsnmp的函数库（目前存在内存泄漏的问题，用替代方法，定时重启子进程，重启多次后就不再扫描（子进程变成僵尸进程的BUG））。
# 如果是bin，则调用netsnmp的可执行文件（效率较低）。
SNMP_READ_COMMUNITY = "public"
SNMP_WRITE_COMMUNITY = "private"

# =============交换机密码=============
SWITCH_PASSWORD = "123456"

# =============微信接入参数=============
WEIXIN_ENABLE = 1  # 是否启用微信接入，是为1，否为0
corpid = "wx09d7623hjg734"
corpsecret = ['', '', 'WsXbVPLqxcNMUY_Okfjrell723ERG2uREnCvZQ5IgwAOS8', '', '', '',
              'jKFitXrTpzWpxRdfsghkj34hGR3YTXiWjUzZOs1JpM']
