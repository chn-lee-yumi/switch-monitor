# encoding: utf-8
# =============网页参数=============
WEB_USERNAME = 'admin'  # 网页登录的用户名
WEB_PASSWORD = '12345'  # 网页登录的密码
WEB_PORT = 80  # http端口

# =============扫描参数=============
TCPING_TIMEOUT = 2  # tcping超时时间，秒
SCAN_THREADS = 65
SCAN_PROCESS = 4

# =============监控参数=============
HELPDESK_TIME = 5  # 微信通知的延迟，分钟
WEIXIN_STAT_TIME_H = 18  # 发送微信统计的时
WEIXIN_STAT_TIME_M = 0  # 发送微信统计的分
SW_REBOOT_TIME_H = 4  # 自动重启交换机的时
SW_REBOOT_TIME_M = 0  # 自动重启交换机的分
CPU_THRESHOLD = 80  # CPU过载阈值
MEM_THRESHOLD = 80  # 内存过高阈值
TEMP_THRESHOLD = 60  # 温度过高阈值
DATA_RECORD_INTERVAL = 1  # 历史记录保存间隔，单位分钟
DATA_RECORD_SAVED_DAYS = 2  # 历史记录保留天数

# =============SNMP参数=============
SNMP_READ_COMMUNITY = "public"
SNMP_WRITE_COMMUNITY = "private"

# =============交换机密码=============
SWITCH_PASSWORD = "123456"

# =============微信接入参数=============
corpid = "wx09d7623hjg734"
corpsecret = ['', '', 'WsXbVPLqxcNMUY_Okfjrell723ERG2uREnCvZQ5IgwAOS8', '', '', '',
              'jKFitXrTpzWpxRdfsghkj34hGR3YTXiWjUzZOs1JpM']
