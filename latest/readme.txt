LICENSE：GPLv3



环境：Python3
依赖包：requests、flask

Debian系统安装运行：
apt-get install python3 snmp
pip3 install requests
pip3 install flask
python3 SwitchMonitor.py

Windows系统安装运行：
上python.org下载安装python3
pip install requests
pip install flask
python SwitchMonitor.py

必须要修改的参数：
Config: web_username
Config: web_password
mod_reboot_switch: switch_password 交换机密码
mod_weixin: corpid 微信开放平台corpid
mod_weixin: corpsecret 微信开放平台corpsecret
mod_snmp: SNMP_COMMUNITY

默认监控参数：（详见Config.py）
交换机掉线5分钟后发送微信通知以及提交工单。
每天下午18点发送统计信息。每天凌晨4点自动重启过载的交换机。
CPU过载阈值：80%
内存过高阈值：80%
温度过高阈值：60℃
