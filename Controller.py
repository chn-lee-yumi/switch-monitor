# encoding: utf-8

# TODO：port_list也改成csv格式读取

import sqlite3
import threading
import platform
from multiprocessing import cpu_count
from flask import *
from mod_ping import *
from mod_reboot_switch import *
from mod_snmp import *
from mod_weixin import *

from Config import WEB_USERNAME, WEB_PASSWORD, WEB_PORT, HELPDESK_TIME, WEIXIN_STAT_TIME_H, WEIXIN_STAT_TIME_M, \
    SW_REBOOT_TIME_H, SW_REBOOT_TIME_M, CPU_THRESHOLD, MEM_THRESHOLD, TEMP_THRESHOLD, DATA_RECORD_INTERVAL, \
    DATA_RECORD_SAVED_DAYS

PING_SCAN_THREADS = 10
SNMP_SCAN_THREADS = 60  # 完成一轮收集所需时间： 70:1'49 80:1'48

global switches, buildings_list, switch_ping_num, switch_snmp_num

lock_data = threading.Lock()  # data.db
lock_data_history = threading.Lock()  # data_history.db
lock_flow_history = threading.Lock()  # flow_history.db
lock_switch_ping_num = threading.Lock()
lock_switch_snmp_num = threading.Lock()


def start_switch_monitor():
    # !!!!!!!!!!!!!!!!!!!!这是主线程!!!!!!!!!!!!!!!!!!!!
    global switches, buildings_list, switch_ping_num, switch_snmp_num

    print("\n")
    print("*" * 50)
    print("当前系统：", platform.system(), platform.architecture()[0], platform.machine())
    print("当前运行平台：", platform.platform())
    print("当前Python版本：", platform.python_version())
    print("CPU核心数：", cpu_count())
    print("*" * 50)

    # 初始化微信接入
    refresh_token()  # 刷新微信token

    # 从文件读取交换机列表 TODO:直接从数据库读取交换机列表，用户可以上传csv或网页设置来修改交换机列表
    file_object = open('switches_list.csv', mode='r', encoding='utf-8')
    try:
        file_object.readline()  # 第一行是标题，我们不需要
        switches_list = file_object.read()
    finally:
        file_object.close()
    switches_list = switches_list.split("\n")  # 每行是一台交换机，包含IP、型号、楼栋、描述

    # 初始化交换机数据
    switches = []  # 用来存放交换机对象的列表
    buildings_list = []  # 用来存放楼栋名称的列表
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    tmp_time = time.time()
    cursor.execute('PRAGMA synchronous = OFF')  # 初始化时关闭写同步提高速度
    try:
        # 检查数据库有没有switches这个表，这个表用于存放交换机的IP、型号、楼栋、描述、掉线时间
        cursor.execute("select * from sqlite_master where type = 'table' and name = 'switches'")
        values = cursor.fetchall()
        if len(values) == 0:
            print("未发现数据表，开始创建数据表。")
            cursor.execute(
                '''
                CREATE TABLE switches
                (
                ip varchar(15),
                model varchar(10),
                building varchar(10),
                desc varchar(20),
                down_time int(10)
                )
               '''
            )
            print("数据表创建完成，初始化数据，需要1~3分钟……")
        else:
            print("发现数据表，读取数据……")
        # 读取数据（遍历所有交换机，检查是否在数据库，不在则添加，在则读取），创建交换机对象
        for a in range(0, len(switches_list)):
            info = switches_list[a].split(",")  # IP、型号、楼栋、描述、掉线时间
            cursor.execute("SELECT ip FROM switches WHERE ip='" + info[0] + "'")
            values = cursor.fetchall()
            if len(values) == 0:  # 交换机不存在则创建
                info.append('在线')
                cursor.execute(
                    "insert into switches values ('" + info[0] + "', '" + info[1] + "', '" + info[2] + "', '" + info[
                        3] + "', '" + info[4] + "')")
                conn.commit()
            else:  # 存在则读取其掉线时间
                cursor.execute("SELECT down_time FROM switches WHERE ip='" + info[0] + "'")
                conn.commit()
                info.append(cursor.fetchall()[0][0])
            # 创建交换机对象
            switches.append(Switch(info[0], info[1], info[2], info[3], info[4]))
            # 生成楼栋列表
            if info[2] not in buildings_list:
                buildings_list.append(info[2])
    finally:
        cursor.close()
        conn.close()
    print("初始化用时：", time.time() - tmp_time)

    # 检查历史记录数据库
    conn = sqlite3.connect("data_history.db")
    cursor = conn.cursor()
    tmp_time = time.time()
    cursor.execute('PRAGMA synchronous = OFF')  # 初始化时关闭写同步提高速度，无数据表时启动时间缩短为约1/3
    try:
        for switch in switches:
            cursor.execute("select * from sqlite_master where type = 'table' and name = '" + switch.ip + "'")
            values = cursor.fetchall()
            if len(values) == 0:  # 数据历史记录里没有此ip，新建一个
                cursor.execute(
                    "CREATE TABLE '" + switch.ip + "' (timestamp int(10),cpu char(5),mem char(5),temp char(5))")
    finally:
        conn.commit()
        cursor.close()
        conn.close()
    print("初始化历史记录数据库用时：", time.time() - tmp_time)

    # 初始化监控端口列表 TODO:参考交换机列表的读取
    global port_list
    file_object = open('port_list.txt', mode='r', encoding='utf-8')
    try:
        port_list = file_object.read().split()
    finally:
        file_object.close()

    # 检查流量速率记录数据库
    conn = sqlite3.connect("flow_history.db")
    cursor = conn.cursor()
    tmp_time = time.time()
    cursor.execute('PRAGMA synchronous = OFF')  # 初始化时关闭写同步提高速度
    try:
        for port in port_list:
            cursor.execute("select * from sqlite_master where type = 'table' and name = '" + port + "'")  # 检查有没有此端口的表
            values = cursor.fetchall()
            if len(values) == 0:
                # 没有此端口的表，新建一个
                cursor.execute(
                    "CREATE TABLE '" + port + "' (timestamp int(10),in_speed int(20),out_speed int(20))")
    finally:
        conn.commit()
        cursor.close()
        conn.close()
    print("初始化流量速率数据库用时：", time.time() - tmp_time)

    # 启动web界面。注：生产环境部署参考http://docs.jinkan.org/docs/flask/deploying/index.html
    threading.Thread(target=startweb, name="线程_flask").start()

    # 启动扫描子进程
    switch_ping_num = 0
    switch_snmp_num = 0
    for a in range(0, PING_SCAN_THREADS):
        threading.Thread(target=scan_ping, name="Ping扫描线程" + str(a)).start()
    for a in range(0, SNMP_SCAN_THREADS):
        threading.Thread(target=scan_snmp, name="SNMP扫描线程" + str(a)).start()

    # 启动数据监控器
    threading.Thread(target=data_supervisor, name="线程_数据监控器").start()

    # 启动数据记录器
    threading.Thread(target=data_history_recoder, name="线程_数据记录器").start()

    # 完成
    print("初始化完成。监控程序已启动。")
    print("*" * 50)
    write_log("INFO: 监控启动")
    send_weixin_msg(time.strftime('[%Y-%m-%d %H:%M:%S] ', time.localtime()) + "\n""监控启动", 2)

    # 调试命令
    time.sleep(2)
    while 1:
        try:
            cmd = input("\033[1;35mDebug Command: \033[0m")  # print(switches)
            if cmd == 'exit':
                print("\033[1;36mExit debug.\033[0m\n")
                break
            if cmd == 'help': print("exit: exit debug.\n")
            exec(cmd)
        except:
            print('Input error.')


class Switch(object):
    # 交换机对象
    def __init__(self, ip, model, building_belong, desc, down_time):  # IP、型号、楼栋、描述、掉线时间
        self.ip = ip
        self.model = model
        self.building_belong = building_belong
        self.desc = desc
        self.down_time = down_time
        # 要获取的信息：CPU使用率、内存使用率、温度、启动时间、接口各种信息
        self.info_time = "等待获取"
        self.last_info_time = 0
        self.cpu_load = "等待获取"  # 监控重开时都显示等待获取
        self.mem_used = "等待获取"
        self.temp = "等待获取"
        self.up_time = "等待获取"
        self.name = "等待获取"
        self.if_status = []
        self.if_name = []
        self.if_descr = []
        self.if_uptime = []
        self.if_index = []
        self.if_ip = []
        self.if_ipindex = []
        self.if_ipmask = []
        self.if_in = []
        self.if_out = []
        self.if_in_speed = []
        self.if_out_speed = []


def scan_ping():  # 在线扫描线程
    global switch_ping_num
    while 1:
        # 获取一台交换机
        lock_switch_ping_num.acquire()
        switch = switches[switch_ping_num]
        switch_ping_num += 1
        if switch_ping_num == len(switches): switch_ping_num = 0
        lock_switch_ping_num.release()
        # 检查在线情况
        if checkswitch(switch.ip) == True:
            if switch.down_time != "在线":
                switch.down_time = "在线"
                write_db(switch.ip, "down_time", "在线")
        else:
            if switch.down_time == "在线":
                tmp_time = time.time()
                switch.down_time = tmp_time
                write_db(switch.ip, "down_time", "%d" % tmp_time)
        # time.sleep(0.1)  # 降低CPU使用率


def scan_snmp():  # SNMP扫描线程
    global switch_snmp_num
    time.sleep(3)
    while 1:
        # 获取一台交换机
        lock_switch_snmp_num.acquire()
        switch = switches[switch_snmp_num]
        switch_snmp_num += 1
        if switch_snmp_num == len(switches): switch_snmp_num = 0
        lock_switch_snmp_num.release()
        # 要获取的信息：CPU使用率、内存使用率、风扇、温度、启动时间、接口状态
        if switch.down_time == "在线":
            if switch.info_time != "等待获取":
                switch.last_info_time = switch.info_time
            switch.info_time = time.time()
            switch.up_time = SnmpWalk(switch.ip, switch.model, "up_time")
            if switch.up_time != "获取失败":  # 如果up_time能正确获取才获取其它信息。如果up_time不能正确获取，其它信息也不可能获取到。
                # 首先获取if_name，且只用获取一次
                if len(switch.if_name) == 0:  # if_name只用获取一次
                    switch.if_index = SnmpWalk(switch.ip, switch.model, "if_index")
                    switch.if_descr = SnmpWalk(switch.ip, switch.model, "if_descr")
                    switch.if_uptime = SnmpWalk(switch.ip, switch.model, "if_uptime")
                    switch.if_ip = SnmpWalk(switch.ip, switch.model, "if_ip")
                    switch.if_ipindex = SnmpWalk(switch.ip, switch.model, "if_ipindex")
                    switch.if_ipmask = SnmpWalk(switch.ip, switch.model, "if_ipmask")
                    switch.name = SnmpWalk(switch.ip, switch.model, "name")
                    for a in range(0, 5):
                        tmp_if_name = SnmpWalk(switch.ip, switch.model, "if_name")
                        if len(SnmpWalk(switch.ip, switch.model, "if_name")) == len(tmp_if_name):
                            switch.if_name = tmp_if_name
                            break
                # 获取其它数据
                switch.cpu_load = SnmpWalk(switch.ip, switch.model, "cpu_load")
                switch.mem_used = SnmpWalk(switch.ip, switch.model, "mem_used")
                switch.temp = SnmpWalk(switch.ip, switch.model, "temp")
                switch.if_status = SnmpWalk(switch.ip, switch.model, "if_status")
                last_if_in = switch.if_in
                last_if_out = switch.if_out
                switch.if_in = SnmpWalk(switch.ip, switch.model, "if_in")
                switch.if_out = SnmpWalk(switch.ip, switch.model, "if_out")
                if_in_speed = []
                if_out_speed = []
                # 下面这部分代码用于计算接口当前速率
                for a in range(0, len(switch.if_name)):
                    if len(last_if_in) != 0:  # 第一次获取时不进行速率计算
                        if last_if_in != '获取失败' and switch.if_in != '获取失败':  # 数据获取正常才进行计算
                            for b in range(0, 5):  # 有时候会获取不完整导致异常，这里检查数据是否完整，如不完整，重新获取
                                if len(switch.if_in) == len(switch.if_name): break
                                switch.if_in = SnmpWalk(switch.ip, switch.model, "if_in")
                            if len(switch.if_in) == len(switch.if_name):
                                if int(switch.if_in[a]) - int(last_if_in[a]) < 0:
                                    switch.if_in[a] = int(switch.if_in[a]) + 2 ** 64
                                if_in_speed.append(int((int(switch.if_in[a]) - int(last_if_in[a])) / (
                                        int(switch.info_time) - int(
                                    switch.last_info_time))))  # TODO：计算好像不大准确，出来的图形很多刺
                            else:  # 如果数据不完整，直接改成获取失败
                                switch.if_in = '获取失败'
                            switch.if_in_speed = if_in_speed
                    if len(last_if_out) != 0:
                        if last_if_out != '获取失败' and switch.if_out != '获取失败':
                            for b in range(0, 5):
                                if len(switch.if_out) == len(switch.if_name): break
                                switch.if_out = SnmpWalk(switch.ip, switch.model, "if_out")
                            if len(switch.if_out) == len(switch.if_name):
                                if int(switch.if_out[a]) - int(last_if_out[a]) < 0:
                                    switch.if_out[a] = int(switch.if_out[a]) + 2 ** 64
                                if_out_speed.append(int((int(switch.if_out[a]) - int(last_if_out[a])) / (
                                        int(switch.info_time) - int(switch.last_info_time))))
                            else:
                                switch.if_out = '获取失败'
                            switch.if_out_speed = if_out_speed


def data_supervisor():  # 监控线程。
    time.sleep(180)  # 启动程序180s后再启动监控线程
    devices_alerted = []
    while (1):
        for switch in switches:
            try:
                if switch.down_time == "在线":
                    if switch.ip in devices_alerted:
                        devices_alerted.remove(switch.ip)
                        send_weixin_msg("[监控消息]交换机复活啦！\n" + "IP:" + switch.building_belong + switch.ip, 6)  # 发送消息
                        write_log(switch.ip + "上线")
                elif (time.time() - switch.down_time) / 60 >= HELPDESK_TIME and not (
                        switch.ip in devices_alerted):
                    send_weixin_msg("[监控消息]交换机炸了！\n" + switch.building_belong + switch.ip, 6)  # 发送消息
                    # send_incident(switch.building_belong, switch.ip)  # 发送工单
                    write_log(switch.ip + "掉线")
                    devices_alerted.append(switch.ip)
            except:
                print(switch.ip, " switch.down_time ", switch.down_time)
                write_log(switch.ip + " switch.down_time " + switch.down_time)
        time.sleep(1)
        if time.localtime()[3] == WEIXIN_STAT_TIME_H and time.localtime()[4] == WEIXIN_STAT_TIME_M:  # 每天发送统计信息
            send_weixin_stat()
            time.sleep(60)
        if time.localtime()[3] == SW_REBOOT_TIME_H and time.localtime()[4] == SW_REBOOT_TIME_M:  # 每天重启过载交换机
            reboot_overload_sw()


def send_weixin_stat():
    msg = "[监控消息]今日交换机状态统计\n"
    down = 0
    cpu_overload = 0
    men_overload = 0
    high_temp = 0
    for switch in switches:
        if switch.down_time != "在线":
            msg += switch.building_belong + switch.ip + "(" + switch.model + ") 掉线时间" + time.strftime(
                '%m-%d %H:%M] ', time.localtime(switch.down_time)) + "\n"
            down += 1
        try:  # 如果内容是“获取失败”或“设备不支持”就会发生异常，所以用try...except来忽略
            if switch.cpu_load >= CPU_THRESHOLD:
                print(switch.cpu_load)
                msg += switch.building_belong + switch.ip + "(" + switch.model + ") CPU使用率：" + str(
                    switch.cpu_load) + "%\n"
                cpu_overload += 1
        except:
            pass
        try:
            if switch.mem_used >= MEM_THRESHOLD:
                msg += switch.building_belong + switch.ip + "(" + switch.model + ") 内存使用率：" + str(
                    switch.mem_used) + "%\n"
                men_overload += 1
        except:
            pass
        try:
            if switch.temp >= TEMP_THRESHOLD:
                msg += switch.building_belong + switch.ip + "(" + switch.model + ") 温度过高：" + str(
                    switch.temp) + "℃\n"
                high_temp += 1
        except:
            pass
    msg += "共" + str(down) + "台交换机掉线\n"
    msg += "共" + str(cpu_overload) + "台交换机CPU使用率过高\n"
    msg += "共" + str(men_overload) + "台交换机内存使用率过高\n"
    msg += "共" + str(high_temp) + "台交换机过热"
    send_weixin_msg(msg, 6)


def reboot_overload_sw():  # 每天自动重启过载交换机
    ips = []
    for switch in switches:
        try:  # 如果内容是“获取失败”或“设备不支持”就会发生异常，所以用try...except来忽略
            if switch.cpu_load >= 80: ips.append(switch.ip)
        except:
            pass
        try:
            if switch.mem_used >= 80: ips.append(switch.ip)
        except:
            pass
        try:
            if switch.temp >= 70: ips.append(switch.ip)
        except:
            pass
    reboot_switches(ips)


def data_history_recoder():
    # 定时把数据写入一次数据库（每隔DATA_RECORD_INTERVAL分钟）
    time.sleep(90)  # 启动程序90s后再启动数据记录线程
    global port_list
    global lock_data_history
    global lock_flow_history
    while (1):
        # 秒==0，分%DATA_RECORD_INTERVAL==0。每DATA_RECORD_INTERVAL分钟
        # while (time.localtime()[5] != 0 or time.localtime()[4] % DATA_RECORD_INTERVAL != 0):
        while (time.localtime()[5] != 0):  # 每分钟
            time.sleep(0.5)
        write_log("alive")
        lock_data_history.acquire()
        conn = sqlite3.connect("data_history.db")
        cursor = conn.cursor()
        lock_flow_history.acquire()
        conn_flow = sqlite3.connect("flow_history.db")
        cursor_flow = conn_flow.cursor()
        # 整点清理data_record_days*24小时前的记录。
        if time.localtime()[4] == 0:  # 分==0
            tmp_time = time.time()
            timestamp = str(int(time.time()) - DATA_RECORD_SAVED_DAYS * 24 * 60 * 60)
            try:
                for switch in switches:
                    cursor.execute("DELETE FROM '" + switch.ip + "' WHERE timestamp <= " + timestamp)
            finally:
                pass
            try:
                for port in port_list:
                    cursor_flow.execute("DELETE FROM '" + port + "' WHERE timestamp <= " + timestamp)
            finally:
                pass
            print("清除一小时数据所用时间：", time.time() - tmp_time)
        # 下面开始写入当前时间的数据
        tmp_time = time.time()
        timestamp = str(int(time.time()))
        try:
            for switch in switches:
                cursor.execute("INSERT INTO '" + switch.ip + "' VALUES ('" + timestamp + "', '" + str(
                    switch.cpu_load) + "', '" + str(switch.mem_used) + "', '" + str(switch.temp) + "')")
        finally:
            conn.commit()
            cursor.close()
            conn.close()
            lock_data_history.release()
        print("把历史数据写入数据库所用时间：", time.time() - tmp_time)
        tmp_time = time.time()
        timestamp = str(int(time.time()))
        try:
            for port in port_list:
                switch_info = port.split(',')
                if len(switch_info) == 2:  # 排除空行或不正常的行
                    switch_ip = switch_info[0]
                    switch_port = switch_info[1]
                    for switch in switches:
                        if switch.ip == switch_ip:
                            try:
                                port_index = switch.if_name.index(switch_port)
                                if port_index != -1 and len(switch.if_out_speed) != 0:
                                    cursor_flow.execute(
                                        "INSERT INTO '" + port + "' VALUES ('" + timestamp + "', '" + str(
                                            switch.if_in_speed[port_index]) + "', '" + str(
                                            switch.if_out_speed[port_index]) + "')")
                                else:
                                    write_log("Port not found: " + port)
                            except:
                                pass
                else:
                    pass
        finally:
            conn_flow.commit()
            cursor_flow.close()
            conn_flow.close()
            lock_flow_history.release()
        print("把流量历史数据写入数据库所用时间：", time.time() - tmp_time)


def write_db(ip, column, data):
    global lock_data
    lock_data.acquire()
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE switches SET " + column + " = '" + data + "' WHERE ip = '" + ip + "'")
        conn.commit()
    finally:
        cursor.close()
        conn.close()
        lock_data.release()


def write_log(text):
    file_object = open('log.txt', mode='a', encoding='utf-8')
    try:
        file_object.write(time.strftime('[%Y-%m-%d %H:%M:%S] ', time.localtime()) + text + "\n")
    finally:
        file_object.close()


app = Flask(__name__)
app.secret_key = 'nia_sbA0Zr98j/3yX R~XHH!jmN]LWX/,?RT(*&^%$_W'


def startweb():
    app.run(host='0.0.0.0', port=WEB_PORT)


# 主页
@app.route('/')
def index():
    global cpu_state
    global switch_down_stat
    if 'username' in session:
        return render_template('home_page.html', username=escape(session['username']))
    return redirect(url_for('login'))


# 登录页
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form_username = request.form['username']
        form_password = request.form['password']
        # 调戏不知道用户名的人（仅供娱乐）
        if form_username == 'admin' and form_password != 'admin': return '系统还未初始化，请使用超级用户登录。用户名：root，初始密码：1am213.'
        if form_username == 'root' and form_password != '1am213.': return '超级用户密码错误！初始密码：1am213.'
        if form_username == 'root' and form_password == '1am213': return '超级用户密码错误！初始密码：1am213. 请注意3后面有一个小数点！'
        if form_username == 'root' and form_password == '1am213.': return '<h1>You just input "I Am 2B." Yes! You Are 2B!!! 你个2B！</h1>'
        # 调戏完毕
        if form_username == WEB_USERNAME and form_password == WEB_PASSWORD:
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', info="用户名或密码错！")
    return render_template('login.html')


# 注销
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


# 设备信息页
@app.route('/buildings')
def buildings():
    if 'username' in session:
        return render_template('buildings.html')
    else:
        return "未登录！"


# 设备具体信息页
@app.route('/devices')
def devices():
    if 'username' in session:
        return render_template('devices.html')
    else:
        return "未登录！"


# 端口监控信息页
@app.route('/ports')
def ports():
    if 'username' in session:
        return render_template('ports.html')
    else:
        return "未登录！"


# 端口流量信息页
@app.route('/port')
def port():
    if 'username' in session:
        return render_template('port.html')
    else:
        return "未登录！"


# 工具页
@app.route('/tools')
def tools():
    if 'username' in session:
        return render_template('tools.html')
    else:
        return "未登录！"


# 设置页
@app.route('/settings')
def settings():
    if 'username' in session:
        return render_template('settings.html')
    else:
        return "未登录！"


# API，返回楼栋名称列表
@app.route('/api/buildings_list')
def api_buildings_list():
    global buildings_list
    return json.dumps(buildings_list, ensure_ascii=False)


# API，返回楼栋信息
@app.route('/api/building/<building_name>')
def api_building_name(building_name):
    info = []
    for switch in switches:
        if switch.building_belong == building_name:
            info.append({"ip": switch.ip, "model": switch.model, "desc": switch.desc, "down_time": switch.down_time,
                         "name": switch.name, "cpu_load": switch.cpu_load, "mem_used": switch.mem_used,
                         "temp": switch.temp, "up_time": switch.up_time, "info_time": switch.info_time})
    return json.dumps(info, ensure_ascii=False)


# API，返回报警信息
@app.route('/api/warnings')
def api_warnings():
    info = []
    for switch in switches:
        if switch.down_time != "在线":
            info.append(
                {"ip": switch.ip, "model": switch.model, "warning": "devices_down", "down_time": switch.down_time})
        try:  # 如果内容是“获取失败”或“设备不支持”就会发生异常，所以用try...except来忽略
            if int(switch.cpu_load) >= 80:
                info.append({"ip": switch.ip, "model": switch.model, "warning": "cpu_overload",
                             "cpu_load": switch.cpu_load})
        except:
            pass
        try:
            if int(switch.mem_used) >= 80:
                info.append({"ip": switch.ip, "model": switch.model, "warning": "mem_overload",
                             "mem_used": switch.mem_used})
        except:
            pass
        try:
            if int(switch.mem_used) >= 70:
                info.append({"ip": switch.ip, "model": switch.model, "warning": "heat", "temp": switch.temp})
        except:
            pass
    return json.dumps(info, ensure_ascii=False)


# API，返回CPU统计数据
@app.route('/api/<attr>')
def api_stat(attr):
    global port_list
    if attr == "ports":
        info = port_list
    else:
        info = []
        for switch in switches:
            if attr == "down_time": info.append(switch.down_time)
            if attr == "cpu_load": info.append(switch.cpu_load)
            if attr == "mem_used": info.append(switch.mem_used)
            if attr == "temp": info.append(switch.temp)
    return json.dumps(info, ensure_ascii=False)


# API，返回设备信息
@app.route('/api/devices/<ip>')
def api_devices(ip):
    info = {}
    for switch in switches:
        if switch.ip == ip:
            if_ip = []
            for index in switch.if_index:
                if index in switch.if_ipindex:
                    if_ip.append(switch.if_ip[switch.if_ipindex.index(index)] + " / " + switch.if_ipmask[
                        switch.if_ipindex.index(index)])
                else:
                    if_ip.append(' ')
            info = {"if_name": switch.if_name, "if_descr": switch.if_descr, "if_status": switch.if_status,
                    "if_uptime": switch.if_uptime, "if_ip": if_ip, "if_in": switch.if_in, "if_out": switch.if_out,
                    "if_in_speed": switch.if_in_speed, "if_out_speed": switch.if_out_speed}
    return json.dumps(info, ensure_ascii=False)


# API,返回历史数据信息
@app.route('/api/history/<ip>')
def api_history(ip):
    lock_data_history.acquire()
    conn = sqlite3.connect("data_history.db")
    cursor = conn.cursor()
    tmp_time = time.time()
    try:
        cursor.execute("SELECT * FROM '" + ip + "'")
        values = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
        lock_data_history.release()
    his_dict = {}
    for a in values:
        his_dict[a[0]] = {'cpu': a[1], 'mem': a[2], 'temp': a[3]}
    print("查询历史数据消耗时间：", time.time() - tmp_time)
    return json.dumps(his_dict, ensure_ascii=False)


# API,返回流量速率历史数据信息
@app.route('/api/flow_history/<port>')
def api_flow_history(port):
    port = port.replace("_", "/")
    lock_flow_history.acquire()
    conn = sqlite3.connect("flow_history.db")
    cursor = conn.cursor()
    tmp_time = time.time()
    try:
        cursor.execute("SELECT * FROM '" + port + "'")
        values = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
        lock_flow_history.release()
    his_dict = {}
    for a in values:
        his_dict[a[0]] = {'in': a[1], 'out': a[2]}
    print("查询流量历史数据消耗时间：", time.time() - tmp_time)
    return json.dumps(his_dict, ensure_ascii=False)


# API，设置工单提交时间
@app.route('/api/settings/helpdesk_time', methods=['GET', 'POST'])
def helpdesk_time():
    global HELPDESK_TIME
    if 'username' in session:
        if request.method == 'POST':
            HELPDESK_TIME = int(request.form['time'])
        info = {"time": HELPDESK_TIME}
        return json.dumps(info, ensure_ascii=False)
    else:
        return "未登录！"


# API，设置微信统计发送时间
@app.route('/api/settings/weixin_stat_time', methods=['GET', 'POST'])
def weixin_stat_time():
    global WEIXIN_STAT_TIME_H
    global WEIXIN_STAT_TIME_M
    if 'username' in session:
        if request.method == 'POST':
            WEIXIN_STAT_TIME_H = int(request.form['time_h'])
            WEIXIN_STAT_TIME_M = int(request.form['time_m'])
        info = {"time_h": WEIXIN_STAT_TIME_H, "time_m": WEIXIN_STAT_TIME_M}
        return json.dumps(info, ensure_ascii=False)
    else:
        return "未登录！"


# API，设置自动重启时间
@app.route('/api/settings/sw_reboot_time', methods=['GET', 'POST'])
def sw_reboot_time():
    global SW_REBOOT_TIME_H
    global SW_REBOOT_TIME_M
    if 'username' in session:
        if request.method == 'POST':
            SW_REBOOT_TIME_H = int(request.form['time_h'])
            SW_REBOOT_TIME_M = int(request.form['time_m'])
        info = {"time_h": SW_REBOOT_TIME_H, "time_m": SW_REBOOT_TIME_M}
        return json.dumps(info, ensure_ascii=False)
    else:
        return "未登录！"


# API，重启交换机
@app.route('/api/tools/reboot_switches', methods=['POST'])
def reboot_sw():
    if 'username' in session:
        ip = request.form['ip']
        reboot_switch_snmp(ip)
        return "监控消息：已发送重启命令！请稍后查看交换机状态。"  # TODO：显示重启进度
    else:
        return "未登录！"


# API，发送微信统计。
@app.route('/api/tools/send_wx_stat')
def send_wx_stat():
    if 'username' in session:
        send_weixin_stat()
        return 0
    else:
        return "未登录！"


if __name__ == '__main__':
    start_switch_monitor()
