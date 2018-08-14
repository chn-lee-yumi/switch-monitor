# encoding: utf-8
# =============网页参数=============
WEB_USERNAME = 'admin'  # 网页登录的用户名
WEB_PASSWORD = '12345'  # 网页登录的密码
WEB_PORT = 80  # http端口

# =============Ping模块参数=============
TCPING_TIMEOUT = 2  # tcping超时时间，秒

# =============监控参数=============
# DEAFULT_PING_INTERVAL = 30  # 扫描间隔，秒，默认30
# DEAFULT_CPU_INTERVAL = 1  # CPU扫描间隔，分钟，默认1
# SWITCH_DOWN_ALERT_TIMES = 6  # 接入交换机连续多少轮扫描都offline才报警，默认6
# THREE_TIER_SWITCH_DOWN_ALERT_TIMES = 3  # 汇聚交换机连续多少轮扫描都offline才报警，默认3
# SWITCH_OVERLOAD_ALERT_TIMES = 3  # 接入交换机连续多少轮扫描都overload才报警，默认3
# SWITCH_UP_AND_DOWN_ALERT_TIMES = 5  # 接入交换机连续挂了又复活多少次才报警，默认5
# DELAY_STAT_TIME = 30  # 延迟发统计信息的时间，秒，默认30
HELPDESK_TIME = 5  # 微信通知/发送工单的延迟，分钟
WEIXIN_STAT_TIME_H = 18  # 发送微信统计的时
WEIXIN_STAT_TIME_M = 0  # 发送微信统计的分
SW_REBOOT_TIME_H = 4  # 自动重启交换机的时
SW_REBOOT_TIME_M = 0  # 自动重启交换机的分
CPU_THRESHOLD = 80  # CPU过载阈值
MEM_THRESHOLD = 80  # 内存过高阈值
TEMP_THRESHOLD = 60  # 温度过高阈值
DATA_RECORD_INTERVAL = 5  # 历史记录保存间隔，单位分钟
DATA_RECORD_SAVED_DAYS = 2  # 历史记录保留天数

# =============SNMP参数=============
SNMP_READ_COMMUNITY = "123456"
SNMP_WRITE_COMMUNITY = "654321"

# =============交换机密码=============
SWITCH_PASSWORD = "3.141592653589793238"

# =============微信接入参数=============
corpid = "wxsakgheity3w9t"
corpsecret = ['', '', 'DFery43g45fW45tgg4th64hdsghiwhil, '', '', '',
              'URD45VB7jkg89gu8YNIUG78i87b89n8B8n890bUg']