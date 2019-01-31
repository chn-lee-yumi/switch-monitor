# 广东工业大学交换机监控

- 2016年“数字校园”学生科技项目。~~（已结题，但仍在持续更新）~~（因即将毕业，以后应该不再更新。代码留给网管队技术组维护。）
- 由于权限问题，目前只监控大学城校区学生宿舍的交换机和生活区核心交换机。未对教学区和其它校区的交换机进行适配。  
- 使用GPLv3开源协议。
- 最新版本：v5.7.0
- 2019年1月31日记：现在代码已用Java重写，前端也移植到了别的框架。同时有了微信小程序版本的监控系统。该仓库应该不会有更新了。学校新建了两栋楼，现在要监控的交换机数量为810台。

# 留下的坑

- 在尝试使用uwsgi部署的时候，执行到扫描线程的`pick = pickle.dumps(switch)`时会卡住，原因未知。故**生产环境部署无法成功**。
- 目前部署在学校的云主机上，系统为CentOS，采用apache反向代理来访问交换机监控（开启了HTTPS）。（见`SwitchMonitor_ApacheReverseProxy.conf`）
- lib扫描模式内存溢出的问题暂时没有完美的解决办法，所以现在学校部署的参数是使用bin扫描模式（达到1分钟轮询约需要4核E7-4820）。

# 部署说明

## 设备

- 推荐配置：
  - CPU：amd64，2核，>2GHz
  - 内存：1GB

- 设备和性能
   - 云主机，E7-4820 v3，1核，达到轮询一次60s的性能时CPU使用率约75%（lib扫描模式，v5.4.0）
   - 在树莓派2B+超频到1020MHz的情况下，CPU满载可以达到轮询一次60s的性能（lib扫描模式，v5.3.0）（该设备存在CPU瓶颈）
   - 在树莓派3B默认频率1200MHz的情况下，达到轮询一次60s的性能时CPU使用率约50%（lib扫描模式，v5.3.0）
   - 最短轮询时间取决于交换机的CPU。当扫描线程数等于交换机总数的时候，有大量交换机CPU过载，轮询间隔约15s。
   
- 注：
   - `SwitchMonitor.service`文件自行选用，用法见文件自身注释。

## 系统环境

- 操作系统：Linux
- 环境：Python3
- 依赖包：flask、python3-netsnmp、psutil、requests

## Debian系统部署（开发环境）

```shell
# 需要root权限
apt-get install python3 python3-pip snmp
pip3 install flask python3-netsnmp psutil requests
cd SwitchMonitor # 切换到监控所在目录
python3 SwitchMonitor.py # 运行
```

## CentOS系统部署（开发环境）

```shell
# 需要root权限
yum install python34 python34-pip python34-devel net-snmp-utils
pip3 install flask python3-netsnmp psutil requests
cd SwitchMonitor # 切换到监控所在目录
python3.4 SwitchMonitor.py # 运行
```

## 生成环境部署（Debian+Nginx）

```shell
# 假设Nginx已经安装好了
# 需要root权限
apt-get install python3 python3-pip snmp
apt-get install uwsgi uwsgi-plugin-python3
pip3 install virtualenv
cp -r SwitchMonitor /var/www # 复制监控目录
cd /var/www/SwitchMonitor
# 配置虚拟环境
virtualenv venv
. venv/bin/activate
pip3 install flask python3-netsnmp psutil requests
# 复制配置文件（如果存在default配置文件，需要先删除）
ln -s /var/www/SwitchMonitor/SwitchMonitor_Nginx.conf /etc/nginx/conf.d/
# 启动uwsgi，uid=1000
uwsgi --ini /var/www/SwitchMonitor/SwitchMonitor_uwsgi.ini --uid 1000 -s /tmp/SwitchMonitor.sock --plugin python3
# 重新加载Nginx配置
nginx -s reload
```

## 生成环境部署（CentOS+Nginx）

```shell
# 假设Nginx已经安装好了
# 需要root权限
yum install python34 python34-pip python34-devel net-snmp-utils
yum install uwsgi uwsgi-plugin-python3
pip3 install virtualenv
cp -r SwitchMonitor /var/www # 复制监控目录
cd /var/www/SwitchMonitor
# 配置虚拟环境
virtualenv venv
. venv/bin/activate
pip3 install flask python3-netsnmp psutil requests
# 复制配置文件（如果存在default配置文件，需要先删除）
ln -s /var/www/SwitchMonitor/SwitchMonitor_Nginx.conf /etc/nginx/conf.d/
# 启动uwsgi，uid=1000
uwsgi --ini /var/www/SwitchMonitor/SwitchMonitor_uwsgi.ini --uid 1000 -s /tmp/SwitchMonitor.sock --plugin python3 --enable-threads
# 重新加载Nginx配置
nginx -s reload
```

## 参数说明

- 必须要修改的参数：（Config.py）
  - WEB_USERNAME：网页用户名
  - WEB_PASSWORD：网页登录密码
  - SWITCH_PASSWORD：交换机密码
  - corpid：微信开放平台corpid
  - corpsecret：微信开放平台corpsecret
  - SNMP_READ_COMMUNITY：SNMP读取密码
  - SNMP_WRITE_COMMUNITY：SNMP写入密码
- 默认报警参数（详见Config.py）
  - 交换机掉线5分钟后发送微信通知。
  - 每天下午18点发送统计信息。每天凌晨4点自动重启过载的交换机。
  - CPU过载阈值：80%
  - 内存过高阈值：80%
  - 温度过高阈值：60℃
- 其它较为重要的参数
   - SCAN_THREADS：每个扫描进程的扫描线程数
   - SCAN_PROCESS：扫描进程数
   - 参考值：对于学校751台交换机，达到60秒一个轮询需要的线程数为80（我的配置为20*4）

# 更新日志

- v5.7.0：
  - 前端页面美化（背景图片位于static\bg.jpg，可以自行修改或删除）
  - 增加日志查看和清除功能
  - 增加发送微信全体消息功能
  - 新增端口流量过大报警（测试功能，不纳入每日统计和微信报警，仅显示在网页上，因为流量时刻变化）
  - 现在普通账号也能进入配置页面，但是只能看，不能设置
  - 修复一些BUG
- v5.6.0：
  - 部分代码重构
  - 新增HTTPS/HTTP选项
  - 新增SNMP扫描方式选项（使用库或可执行文件。使用库有内存泄漏的问题，但是扫描效率高；使用可执行文件扫描效率低，但没有BUG。）
  - 新增管理员账号。只有管理员才能进入Web配置页面
  - 交换机端口页面增加端口带宽数据
  - 一些小优化
  - 修复一些BUG
- v5.5.0：
  - 部分代码重构
  - 新增微信是否启用的参数
  - 增加服务器自身内存监控功能（用于判断针对SNMP库的内存泄漏的替代解决方案是否出现异常）
  - 增加一键重启扫描进程的功能（针对SNMP库的内存泄漏的替代解决方案出BUG时的解决办法）
  - 修复一些BUG
- v5.4.1：
  - 优化图表显示
- v5.4.0：
  - 优化图表显示
  - 优化数据库写入和扫描任务发放的代码
  - 修复一些BUG
- v5.3.0：
  - 部分代码重构
  - 现在使用多进程进行扫描，充分发挥多核性能
  - 修复一些BUG
- v5.2.0：
  - 部分代码重构
  - 更新SNMP模块，提高速度
  - 优化网页交互体验
  - 修复一些BUG
- v5.1.0：
  - 整合部分参数到配置文件
  - 性能调优，加快启动速度，减少CPU占用。
  - 现在交换机端口历史流量页面修改单位后不会重新获取数据，提高了相应速度。
  - 修复一些小BUG
- v5.0.0:
  - 重构代码。
