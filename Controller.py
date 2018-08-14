# encoding: utf-8

# 部署所需计算资源参考：在学校环境下（约600台交换机）整个监控系统部署在树莓派2B@1GHz时，总CPU使用率约50%~60%，Load Average 约3.5

import sqlite3
import threading
from multiprocessing import cpu_count

from flask import *

from mod_helpdesk import *  # TODO：接入新的helpdesk  mod_new_helpdesk
from mod_ping import *
from mod_reboot_switch import *
from mod_snmp import *
from mod_weixin import *

from Config import WEB_USERNAME, WEB_PASSWORD, WEB_PORT, HELPDESK_TIME, WEIXIN_STAT_TIME_H, WEIXIN_STAT_TIME_M, \
    SW_REBOOT_TIME_H, SW_REBOOT_TIME_M, CPU_THRESHOLD, MEM_THRESHOLD, TEMP_THRESHOLD, DATA_RECORD_INTERVAL, \
    DATA_RECORD_SAVED_DAYS

lock = threading.Lock()  # data.db
lock2 = threading.Lock()  # data_history.db
lock3 = threading.Lock()  # flow_history.db


# PS： switches_list需要开头空一行。如果是windows系统，结尾还要空一行。
# TODO： switches_list采用csv格式

def start_switch_monitor():
    # !!!!!!!!!!!!!!!!!!!!这是主线程!!!!!!!!!!!!!!!!!!!!
    print("\n")
    print("*" * 50)
    print("当前系统：", platform.system(), platform.architecture()[0], platform.machine())
    print("当前运行平台：", platform.platform())
    print("当前Python版本：", platform.python_version())
    print("CPU核心数：", cpu_count())
    print("*" * 50)

    # 初始化微信接入
    refresh_token()  # 刷新微信token

    # 初始化交换机列表（从文件读取交换机列表）TODO:直接从数据库读取交换机列表，用户可以上传csv或网页设置来修改交换机列表
    file_object = open('switches_list.txt', mode='r', encoding='utf-8')
    try:
        switches_list = file_object.read()  # TODO：处理windows文本编辑器在文件前加奇怪符号导致第一栋楼无法读取的BUG。替代解决办法：开头空一行。
    finally:
        file_object.close()
    switches_list = switches_list.split("\n")  # TODO：修改读取文件格式为csv，并且末尾要有结束标记。文件包含：楼栋、交换机IP、厂商、型号、描述
    building_list = []
    for a in range(0, len(switches_list)):
        if switches_list[a].find("楼栋：") == 0:
            building_list.append(a)

    # 检查交换机列表和数据库，并初始化对象（每个楼栋启用一个“楼栋控制器”）
    global lock
    lock.acquire()
    global building_controller
    building_controller = {}
    global building_names
    building_names = []
    # 检查数据库
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    tmp_time = time.time()
    cursor.execute('PRAGMA synchronous = OFF')  # 初始化时关闭写同步提高速度
    try:
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
                desc varchar(20),
                down_time int(10)
                )
               '''
            )
            print("数据表创建完成，初始化数据，需要1~3分钟……")
        else:
            print("发现数据表，读取数据……")
        # 初始化楼栋控制器
        for a in range(0, len(building_list)):
            building_switches_ip = []
            building_switches_model = []
            building_switches_desc = []
            if a != len(building_list) - 1:  # 如果不是最后一个楼栋
                for b in range(building_list[a] + 1, building_list[a + 1]):  # 两段就这不同
                    switches_info = switches_list[b].split()
                    building_switches_ip.append(switches_info[0])
                    building_switches_model.append(switches_info[1])
                    if len(switches_info) == 2: switches_info.append("")
                    building_switches_desc.append(switches_info[2])
                    # print(switches_info)
                    # 如果数据表没有这个交换机ip，就新增进去
                    cursor.execute("SELECT ip FROM switches WHERE ip='" + switches_info[0] + "'")
                    values = cursor.fetchall()
                    if len(values) == 0:
                        cursor.execute("insert into switches values ('" + switches_info[0] + "', '" + switches_info[
                            1] + "', '" + switches_info[2] + "', '在线')")
            else:  # 如果是最后一个楼栋
                for b in range(building_list[a] + 1, len(switches_list) - 1):  # 两段就这不同
                    # ！！！！！！！上面，Linux需要len(switches_list)-1，Windows不用-1 ！！！！！！！！！！！！！！
                    # 问题可能在换行方式的不同（CR、LF）。
                    switches_info = switches_list[b].split()
                    building_switches_ip.append(switches_info[0])
                    building_switches_model.append(switches_info[1])
                    if len(switches_info) == 2: switches_info.append("")
                    building_switches_desc.append(switches_info[2])
                    # print(switches_info)
                    # 如果数据表没有这个交换机ip，就新增进去
                    cursor.execute("SELECT ip FROM switches WHERE ip='" + switches_info[0] + "'")
                    values = cursor.fetchall()
                    if len(values) == 0:
                        cursor.execute("insert into switches values ('" + switches_info[0] + "', '" + switches_info[
                            1] + "', '" + switches_info[2] + "', '在线')")
            building_controller[switches_list[building_list[a]][3:]] = BuildingController(
                "楼栋控制器_" + switches_list[building_list[a]][3:], switches_list[building_list[a]][3:],
                building_switches_ip, building_switches_model, building_switches_desc)
            building_names.append(switches_list[building_list[a]][3:])
    finally:
        conn.commit()
        cursor.close()
        conn.close()
        lock.release()
    print("初始化数据表用时：", time.time() - tmp_time)

    # 检查历史记录数据库
    conn = sqlite3.connect("data_history.db")
    cursor = conn.cursor()
    tmp_time = time.time()
    cursor.execute('PRAGMA synchronous = OFF')  # 初始化时关闭写同步提高速度，无数据表时启动时间缩短为约1/3
    try:
        for building_name in building_names:
            for switch in building_controller[building_name].switches:
                cursor.execute("select * from sqlite_master where type = 'table' and name = '" + switch.ip + "'")
                values = cursor.fetchall()
                if len(values) == 0:
                    # 数据历史记录里没有此ip，新建一个
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
            cmd = input("\033[1;35mDebug Command: \033[0m")  # print(building_controller['核心'].switches[0].if_out)
            if cmd == 'exit':
                print("\033[1;36mExit debug.\033[0m\n")
                break
            if cmd == 'help': print("exit: exit debug.\n")
            exec(cmd)
        except:
            print('Input error.')


class BuildingController(object):
    # 楼栋控制器
    def __init__(self, name, building_name, switches_ip, switches_model, switches_desc):
        self.name = name
        self.building_name = building_name
        self.switches_ip = switches_ip
        self.switches_desc = switches_desc
        # 楼栋控制器会创建本楼栋的交换机对象
        self.switches = []
        for a in range(0, len(switches_ip)):
            self.switches.append(
                Switch(switches_ip[a], building_name, switches_ip[a], switches_model[a], switches_desc[a]))
        # 然后用两条线程监控本楼栋交换机，一条监控在线状态，一条监控SNMP数据
        threading.Thread(target=scan_building_ping, args=(building_name,), name="扫描线程_ping_" + building_name).start()
        threading.Thread(target=scan_building_snmp, args=(building_name,), name="扫描线程_snmp_" + building_name).start()


class Switch(object):
    # 交换机
    def __init__(self, name, building_belong, ip, model, desc):
        self.name = name
        self.building_belong = building_belong
        self.ip = ip
        self.model = model
        self.desc = desc
        # 要获取的信息：（5分钟更新一次）CPU使用率、内存使用率、温度、启动时间
        # 要获取的信息：（5分钟更新一次）接口状态
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
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT down_time FROM switches WHERE ip='" + ip + "'")
            conn.commit()
            self.down_time = cursor.fetchall()[0][0]
        finally:
            cursor.close()
            conn.close()


def scan_building_ping(building_name):  # 在线扫描线程
    # 在学校环境下消耗的CPU资源（top命令查看，仅供参考）：树莓派2B@1GHz，python进程约占7.5%
    global building_controller
    time.sleep(3)  # 等3秒，等building_controller赋完值，不然会提示KeyError。其实1秒就够了，防止在低配电脑上造成意外，设置成3秒。
    while 1:
        time.sleep(2)  # 防止断网时CPU使用率100%，也能显著降低联网时的CPU使用率
        # 检查在线情况
        for switch in building_controller[building_name].switches:
            if checkswitch(switch.ip) == True:
                if switch.down_time != "在线":
                    switch.down_time = "在线"
                    write_db(switch.ip, "down_time", "在线")
            else:
                if switch.down_time == "在线":
                    tmp_time = time.time()
                    switch.down_time = tmp_time
                    write_db(switch.ip, "down_time", "%d" % tmp_time)
            time.sleep(0.1)  # 显著降低联网时的CPU使用率，经测试，0.05约占20%，0.1约占7.5%，0.2约占5%


def scan_building_snmp(building_name):  # SNMP扫描线程
    # 在学校环境下消耗的CPU资源（top命令查看，仅供参考）：树莓派2B@1GHz，python进程约占45%
    # 总CPU使用率约为40%（100-idle）。波动较大。Load Average 约2.8
    # TODO：改用池的方法而不是分楼栋，因为交换机数量不定
    global building_controller
    time.sleep(3)
    while 1:
        # 获取SNMP数据
        # 要获取的信息：CPU使用率、内存使用率、风扇、温度、启动时间、接口状态
        for switch in building_controller[building_name].switches:
            time.sleep(1)  # 轻微减少snmpwalk并发数量，降低CPU使用率和负载。如果在性能较好的服务器部署，可以注释掉。
            # 下面的代码用于低性能电脑，防止CPU爆满。测试：树莓派2B@1GHz，python进程约占30%，总CPU使用率约为30%。默认不开。
            # if cpu_count() <= 4: time.sleep(len(building_controller) / cpu_count()) # 大约减少了一半snmpwalk并发数量
            # 下面的代码用于收集数据
            if switch.down_time == "在线":
                if switch.info_time != "等待获取":
                    switch.last_info_time = switch.info_time
                switch.info_time = time.time()
                switch.up_time = SnmpWalk(switch.ip, switch.model, "up_time")
                if switch.up_time != "获取失败":  # 如果up_time能正确获取才获取其它信息。如果up_time不能正确获取，其它信息也不可能获取到。
                    # 首先获取if_name，且只用获取一次
                    if len(switch.if_name) == 0:  # if_name只用获取一次
                        switch.if_index = SnmpWalk(switch.ip, switch.model, "if_index").split()
                        switch.if_descr = SnmpWalk(switch.ip, switch.model, "if_descr").replace('"', '').split(
                            "\n")  # 去掉双引号
                        # switch.if_uptime = list(map(int, SnmpWalk(switch.ip, switch.model, "if_uptime").split()))  # 转为整型
                        switch.if_uptime = SnmpWalk(switch.ip, switch.model, "if_uptime").split()
                        switch.if_ip = SnmpWalk(switch.ip, switch.model, "if_ip").split()
                        switch.if_ipindex = SnmpWalk(switch.ip, switch.model, "if_ipindex").split()
                        switch.if_ipmask = SnmpWalk(switch.ip, switch.model, "if_ipmask").split()
                        switch.name = SnmpWalk(switch.ip, switch.model, "name")[1:-1]  # 截掉交换机名字的双引号
                        for a in range(0, 5):
                            tmp_if_name = SnmpWalk(switch.ip, switch.model, "if_name").replace('"', '').replace('\r',
                                                                                                                '').split(
                                "\n")
                            if len(SnmpWalk(switch.ip, switch.model, "if_name").replace('"', '').split("\n")) == len(
                                    tmp_if_name):
                                switch.if_name = tmp_if_name
                                break
                    # 获取其它数据
                    # up_time_string = switch.up_time.split(":") # 移到前端进行处理
                    # switch.up_time = "%s天%s小时%s分%s秒" % (
                    #     up_time_string[0], up_time_string[1], up_time_string[2], up_time_string[3])
                    switch.cpu_load = SnmpWalk(switch.ip, switch.model, "cpu_load")
                    switch.mem_used = SnmpWalk(switch.ip, switch.model, "mem_used")
                    switch.temp = SnmpWalk(switch.ip, switch.model, "temp")
                    switch.if_status = SnmpWalk(switch.ip, switch.model, "if_status").split()
                    last_if_in = switch.if_in
                    last_if_out = switch.if_out
                    switch.if_in = SnmpWalk(switch.ip, switch.model,
                                            "if_in").split()  # TODO：列表需加判断len是否正常，因为snmp会丢包（基于UDP）
                    switch.if_out = SnmpWalk(switch.ip, switch.model, "if_out").split()
                    if_in_speed = []
                    if_out_speed = []
                    # 下面这部分代码用于计算接口当前速率
                    for a in range(0, len(switch.if_name)):
                        if len(last_if_in) != 0:  # 第一次获取时不进行速率计算
                            if last_if_in[0] != '获取失败' and switch.if_in[0] != '获取失败':  # 数据获取正常才进行计算
                                for b in range(0, 5):  # 有时候会获取不完整导致异常，这里检查数据是否完整，如不完整，重新获取
                                    if len(switch.if_in) == len(switch.if_name): break
                                    switch.if_in = SnmpWalk(switch.ip, switch.model, "if_in").split()
                                if len(switch.if_in) == len(switch.if_name):
                                    if int(switch.if_in[a]) - int(last_if_in[a]) < 0:
                                        switch.if_in[a] = int(switch.if_in[a]) + 2 ** 64
                                    if_in_speed.append(int((int(switch.if_in[a]) - int(last_if_in[a])) / (
                                            int(switch.info_time) - int(
                                        switch.last_info_time))))  # TODO：计算好像不大准确，出来的图形很多刺
                                else:  # 如果数据不完整，直接改成获取失败
                                    switch.if_in = ['获取失败']
                                switch.if_in_speed = if_in_speed
                        if len(last_if_out) != 0:
                            if last_if_out[0] != '获取失败' and switch.if_out[0] != '获取失败':
                                for b in range(0, 5):
                                    if len(switch.if_out) == len(switch.if_name): break
                                    switch.if_out = SnmpWalk(switch.ip, switch.model, "if_out").split()
                                if len(switch.if_out) == len(switch.if_name):
                                    if int(switch.if_out[a]) - int(last_if_out[a]) < 0:
                                        switch.if_out[a] = int(switch.if_out[a]) + 2 ** 64
                                    if_out_speed.append(int((int(switch.if_out[a]) - int(last_if_out[a])) / (
                                            int(switch.info_time) - int(switch.last_info_time))))
                                else:
                                    switch.if_out = ['获取失败']
                                switch.if_out_speed = if_out_speed


def data_supervisor():  # 监控线程。TODO：增加helpdesk接入
    time.sleep(60)  # 启动程序60后再启动监控进程
    global building_names
    global building_controller
    devices_alerted = []
    while (1):
        for building_name in building_names:
            for switch in building_controller[building_name].switches:
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
    global building_names
    global building_controller
    msg = "[监控消息]今日交换机状态统计\n"
    down = 0
    cpu_overload = 0
    men_overload = 0
    high_temp = 0
    for building_name in building_names:
        for switch in building_controller[building_name].switches:
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
    global building_names
    global building_controller
    ips = []
    for building_name in building_names:
        for switch in building_controller[building_name].switches:
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
    global building_names
    global building_controller
    global lock2
    global port_list
    global lock3
    while (1):
        while (time.localtime()[5] != 0 or time.localtime()[
            4] % DATA_RECORD_INTERVAL != 0):  # 秒==0，分%DATA_RECORD_INTERVAL==0。每DATA_RECORD_INTERVAL分钟
            time.sleep(0.5)
        write_log("alive")
        lock2.acquire()
        conn = sqlite3.connect("data_history.db")
        cursor = conn.cursor()
        lock3.acquire()
        conn_flow = sqlite3.connect("flow_history.db")
        cursor_flow = conn_flow.cursor()
        # 整点清理data_record_days*24小时前的记录。
        if time.localtime()[4] == 0:  # 分==0
            tmp_time = time.time()
            timestamp = str(int(time.time()) - DATA_RECORD_SAVED_DAYS * 24 * 60 * 60)
            try:
                for building_name in building_names:
                    for switch in building_controller[building_name].switches:
                        cursor.execute(
                            "DELETE FROM '" + switch.ip + "' WHERE timestamp <= " + timestamp)
            finally:
                pass
            try:
                for port in port_list:
                    cursor_flow.execute(
                        "DELETE FROM '" + port + "' WHERE timestamp <= " + timestamp)
            finally:
                pass
            print("清除一小时数据所用时间：", time.time() - tmp_time)
        # 下面开始写入当前时间的数据
        timestamp = str(int(time.time()))
        try:
            for building_name in building_names:
                for switch in building_controller[building_name].switches:
                    cursor.execute(
                        "INSERT INTO '" + switch.ip + "' VALUES ('" + timestamp + "', '" + str(
                            switch.cpu_load) + "', '" + str(switch.mem_used) + "', '" + str(switch.temp) + "')")
        finally:
            conn.commit()
            cursor.close()
            conn.close()
            lock2.release()
        try:
            for port in port_list:
                switch_info = port.split(',')
                if len(switch_info) == 2:  # 排除空行或不正常的行
                    switch_ip = switch_info[0]
                    switch_port = switch_info[1]
                    for building_name in building_names:
                        for switch in building_controller[building_name].switches:
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
                                    # print("Error: port not found: " + switch_port)
                                    # print(switch.if_name)
                else:
                    pass
        finally:
            conn_flow.commit()
            cursor_flow.close()
            conn_flow.close()
            lock3.release()


def write_db(ip, column, data):
    global lock
    lock.acquire()
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE switches SET " + column + " = '" + data + "' WHERE ip = '" + ip + "'")
        conn.commit()
    finally:
        cursor.close()
        conn.close()
        lock.release()


def write_log(text):
    file_object = open('log.txt', mode='w+', encoding='utf-8')
    try:
        file_object.write(time.strftime('[%Y-%m-%d %H-%M-%S] ', time.localtime()) + text + "\n")
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
    global building_names
    if 'username' in session:
        options_html = ""
        for a in building_names:  # TODO:在HTML内用API获取，而不是在这里渲染
            options_html += "<option value=" + a + ">" + a + "</option>\n"
        return render_template('buildings.html', options=options_html)
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


# API，返回楼栋信息
@app.route('/api/building/<building_name>')
def api_building(building_name):
    global building_controller
    info = []
    for switch in building_controller[building_name].switches:
        info.append({"ip": switch.ip, "model": switch.model, "desc": switch.desc, "down_time": switch.down_time,
                     "name": switch.name, "cpu_load": switch.cpu_load, "mem_used": switch.mem_used, "temp": switch.temp,
                     "up_time": switch.up_time, "info_time": switch.info_time})
    return json.dumps(info, ensure_ascii=False)


# API，返回报警信息
@app.route('/api/warnings')
def api_warnings():
    global building_names
    global building_controller
    info = []
    for building_name in building_names:
        for switch in building_controller[building_name].switches:
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
    global building_names
    global building_controller
    global port_list
    if attr == "ports":
        info = port_list
    else:
        info = []
        for building_name in building_names:
            for switch in building_controller[building_name].switches:
                if attr == "down_time": info.append(switch.down_time)
                if attr == "cpu_load": info.append(switch.cpu_load)
                if attr == "mem_used": info.append(switch.mem_used)
                if attr == "temp": info.append(switch.temp)
    return json.dumps(info, ensure_ascii=False)


# API，返回设备信息
@app.route('/api/devices/<ip>')
def api_devices(ip):
    global building_names
    global building_controller
    info = {}
    for building_name in building_names:
        for switch in building_controller[building_name].switches:
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
    # TODO:接口流量记录、核心接口速度有误的BUG（获取速率太低）。设备详细信息页面改实时监控，因为核心流量太大。
    global building_names
    global building_controller
    # global lock2
    # lock2.acquire()
    conn = sqlite3.connect("data_history.db")
    cursor = conn.cursor()
    tmp_time = time.time()
    try:
        cursor.execute("SELECT * FROM '" + ip + "'")
        values = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
        # lock2.release()
    his_dict = {}
    for a in values:
        his_dict[a[0]] = {'cpu': a[1], 'mem': a[2], 'temp': a[3]}
    print("查询历史数据消耗时间：", time.time() - tmp_time)
    return json.dumps(his_dict, ensure_ascii=False)


# API,返回流量速率历史数据信息
@app.route('/api/flow_history/<port>')
def api_flow_history(port):
    port = port.replace("_", "/")
    # global lock3
    # lock3.acquire()
    conn = sqlite3.connect("flow_history.db")
    cursor = conn.cursor()
    tmp_time = time.time()
    try:
        cursor.execute("SELECT * FROM '" + port + "'")
        values = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
        # lock3.release()
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


# 测试工单提交。TODO：接入新helpdesk
@app.route('/test_ticket')
def test_ticket():
    if 'username' in session:
        send_incident('东二', '172.16.102.1')
        return 0
    else:
        return "未登录！"


if __name__ == '__main__':
    start_switch_monitor()
