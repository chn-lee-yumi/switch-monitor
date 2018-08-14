# 广东工业大学交换机监控
- 2016年“数字校园”学生科技项目。（已结题，但仍在持续更新）  
- 由于权限问题，目前只监控大学城校区学生宿舍的交换机和生活区核心交换机。未对教学区和其它校区的交换机进行适配。  
- 最新版本为5.1.0。  
- 使用GPLv3开源协议。

# 部署说明
## 设备
- 推荐配置：
 - CPU：4核
 - 内存：1GB
- 可运行在树莓派2B上。
## 系统环境
- Windows和Linux均可
- 环境：Python3
- 依赖包：requests、flask
## Debian系统部署
```shell
apt-get install python3 snmp
pip3 install requests
pip3 install flask
python3 SwitchMonitor.py # 运行
```
## Windows系统部署
- 从python.org下载安装python3
- 在cmd输入下面命令
```shell
pip install requests
pip install flask
python SwitchMonitor.py # 运行
```
## 参数说明
- 必须要修改的参数：（Config.py）
 - web_username：网页用户名
 - web_password：网页登录密码
 - switch_password：交换机密码
 - corpid：微信开放平台corpid
 - corpsecret：微信开放平台corpsecret
 - SNMP_COMMUNITY：SNMP读写密码
- 默认报警参数（详见Config.py）
 - 交换机掉线5分钟后发送微信通知以及提交工单。
 - 每天下午18点发送统计信息。每天凌晨4点自动重启过载的交换机。
 - CPU过载阈值：80%
 - 内存过高阈值：80%
 - 温度过高阈值：60℃

# 更新日志
- v5.1.0：
 - 整合部分参数到配置文件
 - 性能调优，加快启动速度，减少CPU占用。
 - 现在交换机端口历史流量页面修改单位后不会重新获取数据，提高了相应速度。
 - 修复一些小BUG
- v5.0.0:
 - 重构代码。
