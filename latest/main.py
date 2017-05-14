# encoding: utf-8
from mod_ping import *
from mod_weixin import *
from mod_cpu import *
from mod_reboot_switch import *
import time
import threading

'''
TODO: 使用SNMP获取内存、温度、风扇信息。交换机数据保存到文件，重启监控后能读取上次的数据。从文件读取交换机IP。
已知BUG：None.

代码分五大部分：交换机在线状态部分、交换机CPU使用率部分、发送统计信息部分、网页部分、主线程

交换机在线状态部分：使用mod_ping、mod_weixin
def checkswitch(ip):  # 检测交换机在线情况的函数，返回True或False
def offline(ip, a):  # 如果交换机不在线，程序怎么处理
def online(ip, building):  # 如果交换机在线，程序怎么处理
def scanbuilding(building):  # 每个楼栋一条线程，逐台交换机扫描，判断状态之后交由online和offline两个过程处理。
                             # 该过程还负责判断和处理三层交换机是否有问题。

交换机CPU使用率部分:使用mod_cpu（mod_cpu使用了mod_snmp）、mod_weixin
def scancpu():  # 单独的一条线程，逐台交换机扫描CPU使用率，并进行分析和处理

发送统计信息部分：使用mod_weixin
def delaystat():  # 延迟发送统计信息的过程。当同时炸掉几台交换机时，只需要发送一次最新的统计信息。
                  # 为了减少信息发送量，特意设置。delay_stat是一个全局变量。
def statistics():  # 统计交换机异常状态并发送微信推送。

网页部分:使用mod_weixin、mod_reboot_switch
def startweb():  # 单独的一条线程，相当于http服务器
@app.route('/')  # 主页，若未登录则跳转到登陆页面
                 # 调用了statistics4web() cpustat() cpu_statistic() onlinestat() online_statistic()
@app.route('/login', methods=['GET', 'POST'])  # 登录页面
@app.route('/logout')  # 退出登录，然后跳转到登陆页面
@app.route('/cpuinfo')  # 生成CPU使用率的excel表格并移动到static文件夹并跳转到表格的下载地址
@app.route('/stat', methods=['POST', 'GET'])  # 马上发送统计信息到微信，若未登录则跳转到登陆页面
@app.route('/rebootswitches', methods=['POST', 'GET'])  # 马上扔出一个线程去逐台重启不稳定的和过载的交换机
def statistics4web():  # 统计交换机异常状态并返回HTML格式的字符串
def cpustat():  # 将CPU使用率分成几个区间，以便在网页上用图表显示
def cpu_statistic():  # 统计交换机CPU使用率状态并返回HTML格式的字符串
def onlinestat():  # 将交换机掉线次数分成几个区间，以便在网页上用图表显示
def online_statistic():  # 统计交换机在线状态并返回HTML格式的字符串

主线程:
首先发送监控在线的信息
然后给所有任务分配线程
最后进入循环：
每小时刷新微信token和发送一次在线信息，特定时间自动发送统计信息，特点时间自动重启不稳定和过载的交换机

'''

# =============监控参数=============
DEAFULT_delay0 = 20  # 扫描间隔，秒，默认20
DEAFULT_CPU_INTERVAL = 5  # CPU扫描间隔，分钟，默认5
SWITCH_DOWN_ALERT_TIMES = 6  # 接入交换机连续多少轮扫描都offline才报警，默认6
THREE_TIER_SWITCH_DOWN_ALERT_TIMES = 3  # 汇聚交换机连续多少轮扫描都offline才报警，默认3
SWITCH_OVERLOAD_ALERT_TIMES = 3  # 接入交换机连续多少轮扫描都overload才报警，默认3
SWITCH_UP_AND_DOWN_ALERT_TIMES = 5  # 接入交换机连续挂了又复活多少次才报警，默认5
DELAY_STAT_TIME = 30  # 延迟发统计信息的时间，秒，默认30
# =============网页参数=============
web_username = 'user'  # 网页登录的用户名
web_password = '12345'  # 网页登录的密码
web_port = 3866  # http端口

# 变量定义
switch_numbers = {}  # 各楼栋接入交换机数目
three_tier_switch_down_cycles = {}  # 汇聚交换机down的扫描次数
three_tier_switch_down_time = {}  # 汇聚交换机down的时间
switch_down_cycles = {}  # 接入交换机down的扫描次数
switch_down_time = {}  # 接入交换机down的时间
switch_up_and_down_times = {}  # 接入交换机挂了又复活的次数，次数过多认为不稳定
switch_overload_times = {}  # 接入交换机overload的次数
switch_cpu_load_5min = {}  # 接入交换机CPU五分钟平均负载

# 初始化
switch_numbers[101] = 17
switch_numbers[102] = 17
switch_numbers[103] = 10
switch_numbers[104] = 18
switch_numbers[105] = 18
switch_numbers[106] = 19
switch_numbers[107] = 19
switch_numbers[108] = 19
switch_numbers[109] = 7
switch_numbers[110] = 21
switch_numbers[111] = 7
switch_numbers[112] = 16
switch_numbers[113] = 36
switch_numbers[114] = 36
switch_numbers[115] = 35
switch_numbers[121] = 19
switch_numbers[122] = 23
switch_numbers[123] = 30
switch_numbers[124] = 35
switch_numbers[125] = 31
switch_numbers[126] = 30
switch_numbers[127] = 28
switch_numbers[128] = 29
switch_numbers[129] = 28
switch_numbers[130] = 26
switch_numbers[131] = 23
switch_numbers[132] = 23
switch_numbers[133] = 28
switch_numbers[134] = 24
for a in list(range(101, 116)) + list(range(121, 135)):
    three_tier_switch_down_cycles[a] = 0
    three_tier_switch_down_time[a] = 0
    for b in range(1, switch_numbers[a] + 1):
        ip = "172.16." + str(a) + "." + str(b)
        switch_down_cycles[ip] = 0
        switch_down_time[ip] = 0
        switch_overload_times[ip] = 0
        switch_cpu_load_5min[ip] = "0%"
        switch_up_and_down_times[ip] = 0


def next_ip(ip):
    a = int(ip.split(".")[2])
    b = int(ip.split(".")[3]) + 1
    if b > switch_numbers[a]:  # 扫完本栋就下一栋
        a = a + 1
        b = 1
        if a == 116: a = 121
        if a == 135: return ""
    if a == 113 and b == 24: b = 25  # 这几台不存在
    if a == 105 and b == 6: b = 7
    if a == 109 and b == 1: b = 2
    if a == 106 and b == 15: b = 16  # 这几台坏了很久
    if a == 105 and b == 2: b = 3
    if a == 115 and b == 7: b = 8
    if a == 125 and b == 15: b = 16
    if a == 131 and b == 8: b = 9
    if a == 133 and b == 1: b = 2
    if a == 109 and b == 6: b = 7
    return "172.16." + str(a) + "." + str(b)


# =====================交换机在线状态部分=====================
# =====================交换机在线状态部分=====================
# =====================交换机在线状态部分=====================


def checkswitch(ip):  # 检测交换机在线情况的函数
    if tcpingip(ip): return True
    return tcpingip(ip)


def offline(ip, a):  # 交换机offline的处理方法
    global delay_stat
    if switch_down_cycles[ip] == SWITCH_DOWN_ALERT_TIMES:
        sendweixinmsg("Time: " + time.strftime("%X") + "\n交换机炸了:\n" + ip, 3, token)  # 发送DOWN信息
        delay_stat = True
    if switch_down_cycles[ip] == 1: switch_down_time[ip] = time.time()
    if switch_down_cycles[ip] == SWITCH_DOWN_ALERT_TIMES * 10:
        sendweixinmsg(
            "Time: " + time.strftime("%X") + "\n交换机" + ip + "\n已经炸了" + str(
                int((time.time() - switch_down_time[ip])) // 60) + "分钟！发生了什么？", 3,
            token)
        delay_stat = True


def online(ip, building):  # 交换机online的处理方法
    global delay_stat
    if switch_down_cycles[ip] >= SWITCH_DOWN_ALERT_TIMES:
        sendweixinmsg("Time: " + time.strftime("%X") + "\n交换机UP:\n" + ip + "\n刚挂了" + str(int(
            (time.time() - switch_down_time[ip])) // 60) + "分钟。", 3, token)  # 发送UP信息
        delay_stat = True
        switch_up_and_down_times[ip] = switch_up_and_down_times[ip] + 1  # 不稳定次数+1
    switch_down_cycles[ip] = 0
    if three_tier_switch_down_cycles[building] >= THREE_TIER_SWITCH_DOWN_ALERT_TIMES:
        sendweixinmsg("Time: " + time.strftime("%X") + "\n汇聚UP:\n172.16." + str(building) + ".254\n刚挂了" + str(
            int((time.time() - three_tier_switch_down_time[building])) // 60) + "分钟。", 4, token)  # 发送UP信息
        delay_stat = True
    three_tier_switch_down_cycles[building] = 0


def scanbuilding(building):
    global delay_stat
    global switch_down_cycles
    global three_tier_switch_down_cycles
    global three_tier_switch_down_time
    ip = "172.16." + str(building) + ".0"
    while 1:
        ip = next_ip(ip)
        if checkswitch(ip) == False:  # 重点：交换机下线的处理环节！！！！！！！！！！！！！！
            switch_down_cycles[ip] = switch_down_cycles[ip] + 1
            # 判断是否汇聚交换机问题
            if checkswitch("172.16." + str(building) + "." + str(254)) == False:
                if switch_down_cycles[ip] == 1: switch_down_cycles[
                    ip] = 0  # 可能有交换机是一直DOWN的，这个可以避免汇聚挂了复活之后给原来就DOWN的交换机重新报一次警
                three_tier_switch_down_cycles[building] = three_tier_switch_down_cycles[building] + 1
                if three_tier_switch_down_cycles[building] == 1: three_tier_switch_down_time[building] = time.time()
                if three_tier_switch_down_cycles[building] == THREE_TIER_SWITCH_DOWN_ALERT_TIMES:  # 汇聚交换机刚DOWN了
                    sendweixinmsg("Time: " + time.strftime("%X") + "\n汇聚炸了！！！\n172.16." + str(building) + ".254", 4,
                                  token)  # 发送DOWN信息
                    delay_stat = True
                if three_tier_switch_down_cycles[building] == THREE_TIER_SWITCH_DOWN_ALERT_TIMES * 10:  # 汇聚交换机DOWN很久了
                    sendweixinmsg("Time: " + time.strftime("%X") + "\n汇聚炸好久了！！！\n已经炸了" + str(
                        int((time.time() - three_tier_switch_down_time[building])) // 60) + "分钟！！\n172.16." + str(
                        building) + ".254\n请前往检查。", 4, token)  # 发送DOWN信息
                    delay_stat = True
                time.sleep(DEAFULT_delay0)  # 等下一轮
                b = 0  # 下面会加1
            else:
                offline(ip, building)  # 如果不是汇聚问题，判断这台交换机offline
        else:
            online(ip, building)  # 交换机是online的
        if int(ip.split(".")[3]) == switch_numbers[building]:  # 扫完本栋就等下一轮
            time.sleep(DEAFULT_delay0)
            ip = "172.16." + str(building) + ".0"


# =====================交换机CPU使用率部分=====================
# =====================交换机CPU使用率部分=====================
# =====================交换机CPU使用率部分=====================


def scancpu():  # 扫描CPU
    global delay_stat
    global switch_cpu_load_5min
    ip = "172.16.101.1"
    while 1:
        cpu = getcpuinfo(ip)
        switch_cpu_load_5min[ip] = cpu
        try:
            if int(cpu[:-1]) > 80:  # 大于80%就算过载
                switch_overload_times[ip] = switch_overload_times[ip] + 1
                if switch_overload_times[ip] == SWITCH_OVERLOAD_ALERT_TIMES:
                    sendweixinmsg("Time:\n" + time.strftime(
                        "%X") + "\n交换机过载:\n" + ip + "\nCPU load in last 5 minutes is " + cpu + "\n持续了" + str(
                        DEAFULT_CPU_INTERVAL * SWITCH_OVERLOAD_ALERT_TIMES) + "分钟，请检查一下。", 3, token)
                    delay_stat = True
                elif switch_overload_times[ip] == 20 * SWITCH_OVERLOAD_ALERT_TIMES:
                    sendweixinmsg("Time:\n" + time.strftime(
                        "%X") + "\n这台交换机过载很长时间了！\nIP: " + ip + "\nCPU load in last 5 minutes is " + cpu + "\n持续了" + str(
                        DEAFULT_CPU_INTERVAL * SWITCH_OVERLOAD_ALERT_TIMES * 20) + "分钟，请检查一下！！！", 3, token)
                    delay_stat = True
            else:
                if switch_overload_times[ip] >= SWITCH_OVERLOAD_ALERT_TIMES and cpu != "0%":
                    sendweixinmsg("Time:\n" + time.strftime("%X") + "\n交换机CPU使用率变回正常\n刚过载了" + str(
                        SWITCH_OVERLOAD_ALERT_TIMES * switch_overload_times[
                            ip]) + "分钟。\nIP: 172.16." + ip + "\nCPU load in last 5 minutes is " + cpu + ".", 3, token)
                    delay_stat = True
                switch_overload_times[ip] = 0
        except:
            switch_cpu_load_5min[ip] = "0%"
        ip = next_ip(ip)
        if ip == "": ip = "172.16.101.1"


# =====================发送统计信息部分=====================
# =====================发送统计信息部分=====================
# =====================发送统计信息部分=====================


def delaystat():
    global delay_stat
    c = -1
    while 1:
        if delay_stat == True:
            delay_stat = False
            c = DELAY_STAT_TIME
        if c == 0: statistics()
        if c >= 0: c = c - 1
        time.sleep(1)


def statistics():
    msg = "===交换机状态异常统计==="
    for a in list(range(101, 116)) + list(range(121, 135)):
        if three_tier_switch_down_cycles[a] >= THREE_TIER_SWITCH_DOWN_ALERT_TIMES: msg = msg + "\n汇聚172.16." + str(
            a) + ".254炸了" + str(int((time.time() - three_tier_switch_down_time[a])) // 60) + "分钟"
    for a in list(range(101, 116)) + list(range(121, 135)):
        for b in range(1, switch_numbers[a] + 1):
            if switch_down_cycles["172.16." + str(a) + "." + str(
                    b)] >= SWITCH_DOWN_ALERT_TIMES: msg = msg + "\n接入172.16." + str(a) + "." + str(b) + "炸了" + str(
                int((time.time() - switch_down_time["172.16." + str(a) + "." + str(b)])) // 60) + "分钟"
    for a in list(range(101, 116)) + list(range(121, 135)):
        for b in range(1, switch_numbers[a] + 1):
            if switch_overload_times["172.16." + str(a) + "." + str(
                    b)] >= SWITCH_OVERLOAD_ALERT_TIMES: msg = msg + "\n接入172.16." + str(
                a) + "." + str(b) + "过载了" + str(
                SWITCH_OVERLOAD_ALERT_TIMES * switch_overload_times["172.16." + str(a) + "." + str(b)]) + "分钟"
    for a in list(range(101, 116)) + list(range(121, 135)):
        for b in range(1, switch_numbers[a] + 1):
            if switch_up_and_down_times["172.16." + str(a) + "." + str(
                    b)] >= SWITCH_UP_AND_DOWN_ALERT_TIMES: msg = msg + "\n接入交换机172.16." + str(
                a) + "." + str(b) + "频繁掉线，今天已经掉线了" + str(
                switch_up_and_down_times["172.16." + str(a) + "." + str(b)]) + "次"
    if msg == "===交换机状态异常统计===": msg = msg + "\n所有交换机正常！"
    sendweixinmsg(msg, 6, token)


# ====================网页部分=====================
# ====================网页部分=====================
# ====================网页部分=====================

from flask import *

app = Flask(__name__)
app.secret_key = 'niasbA0Zr98j/3yX R~XHH!jmN]LWX/,?RT(*&^%$sdfghWERTY'


def startweb():
    app.run(host='0.0.0.0', port=web_port)


@app.route('/')
def index():
    global cpu_state
    global switch_down_stat
    if 'username' in session:
        cpustat()  # 统计CPU使用率数据
        onlinestat()  # 统计二层交换机实时down的次数
        return render_template('dashboard.html', username=escape(session['username']),
                               current_statistic=statistics4web(), cpu_state_all=cpu_state,
                               switch_down_stat_all=switch_down_stat, cpu_statistic=cpu_statistic(),
                               online_statistic=online_statistic())
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form_username = request.form['username']
        form_password = request.form['password']
        # 调戏不知道用户名的人（仅供娱乐）
        if form_username == 'admin': return "系统还未初始化，请使用超级用户登录。用户名：root，初始密码：1am213."
        if form_username == 'root' and form_password != '1am213' and form_password != '1am213.': return "超级用户密码错误！初始密码：1am213."
        if form_username == 'root' and form_password == '1am213': return "超级用户密码错误！初始密码：1am213. 请注意3后面有一个小数点！"
        if form_username == 'root' and form_password == '1am213.': return "<h1>傻逼你居然信了哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈</h1>"
        # 调戏完毕
        if form_username == web_username and form_password == web_password:
            session['username'] = request.form['username']
            return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/cpuinfo')
def cpuinfo():
    from xlsxwriter.workbook import Workbook
    import shutil
    global flag_cpuinfo_botton
    if 'username' in session:
        cpuinfo_filename = 'cpuinfo_' + time.strftime("%Y_%m_%d_%H_%M_%S") + '.xlsx'
        workbook = Workbook(cpuinfo_filename)
        worksheet = workbook.add_worksheet()
        column_head = ['IP地址', 'CPU 5分钟使用率']
        y = 0
        for column in column_head:
            worksheet.write(0, y, column)
            y += 1
        y = 1
        c = 1
        ip = "172.16.101.1"
        while ip != "":
            cpu = switch_cpu_load_5min[ip]
            worksheet.write(c, 0, ip)
            worksheet.write(c, 1, cpu)
            c = c + 1
            # 设置下一个交换机IP
            ip = next_ip(ip)
        workbook.close()
        shutil.move(cpuinfo_filename, "static/" + cpuinfo_filename)
        return redirect(url_for('static', filename=cpuinfo_filename))
    return redirect(url_for('login'))


@app.route('/stat', methods=['POST', 'GET'])
def sendstat2weixin():
    if 'username' in session:
        statistics()
        return '微信推送已发送。'
    return redirect(url_for('login'))


@app.route('/rebootswitches', methods=['POST', 'GET'])
def rebootswitches():
    if 'username' in session:
        ips = []
        for a in list(range(101, 116)) + list(range(121, 135)):
            for b in range(1, switch_numbers[a] + 1):
                ip = "172.16." + str(a) + "." + str(b)
                if switch_overload_times[ip] >= SWITCH_OVERLOAD_ALERT_TIMES or switch_up_and_down_times[
                    ip] >= SWITCH_UP_AND_DOWN_ALERT_TIMES:
                    ips.append(ip)
                    switch_up_and_down_times[ip] = 0
        threading.Thread(target=reboot_switches, args=(ips,)).start()  # 这里得改！！！！！！！线程池，worker！！！
        return '重启命令已发送，请5分钟后再看统计数据。'
    return redirect(url_for('login'))


def statistics4web():
    s_msg = '<div class="alert alert-danger" role="alert">发现交换机异常：'
    msg = s_msg
    for a in list(range(101, 116)) + list(range(121, 135)):
        if three_tier_switch_down_cycles[
            a] >= THREE_TIER_SWITCH_DOWN_ALERT_TIMES: msg = msg + "</br>汇聚交换机172.16." + str(
            a) + ".254 炸了" + str(int((time.time() - three_tier_switch_down_time[a])) // 60) + "分钟"
    for a in list(range(101, 116)) + list(range(121, 135)):
        for b in range(1, switch_numbers[a] + 1):
            if switch_down_cycles["172.16." + str(a) + "." + str(
                    b)] >= SWITCH_DOWN_ALERT_TIMES: msg = msg + "</br>接入交换机172.16." + str(a) + "." + str(
                b) + "炸了" + str(
                int((time.time() - switch_down_time["172.16." + str(a) + "." + str(b)])) // 60) + "分钟"
    for a in list(range(101, 116)) + list(range(121, 135)):
        for b in range(1, switch_numbers[a] + 1):
            if switch_overload_times["172.16." + str(a) + "." + str(
                    b)] >= SWITCH_OVERLOAD_ALERT_TIMES: msg = msg + "</br>接入交换机172.16." + str(
                a) + "." + str(b) + "过载了" + str(
                SWITCH_OVERLOAD_ALERT_TIMES * switch_overload_times["172.16." + str(a) + "." + str(b)]) + "分钟"
    for a in list(range(101, 116)) + list(range(121, 135)):
        for b in range(1, switch_numbers[a] + 1):
            if switch_up_and_down_times["172.16." + str(a) + "." + str(
                    b)] >= SWITCH_UP_AND_DOWN_ALERT_TIMES: msg = msg + "</br>接入交换机172.16." + str(
                a) + "." + str(b) + "频繁掉线，今天已经掉线了" + str(
                switch_up_and_down_times["172.16." + str(a) + "." + str(b)]) + "次"
    if msg == s_msg:
        msg = '<div class="alert alert-success" role="alert">没有交换机异常</div>'
    else:
        msg = msg + '</div>'
    return msg


def cpustat():
    global cpu_state
    cpu_state = [0, 0, 0, 0, 0, 0]
    ip = "172.16.101.1"
    while ip != "":
        try:
            if int(switch_cpu_load_5min[ip][:-1]) == 0: cpu_state[5] = cpu_state[5] + 1
            if int(switch_cpu_load_5min[ip][:-1]) > 0 and int(switch_cpu_load_5min[ip][:-1]) <= 20: cpu_state[0] = \
                cpu_state[0] + 1
            if int(switch_cpu_load_5min[ip][:-1]) > 20 and int(switch_cpu_load_5min[ip][:-1]) <= 40: cpu_state[1] = \
                cpu_state[1] + 1
            if int(switch_cpu_load_5min[ip][:-1]) > 40 and int(switch_cpu_load_5min[ip][:-1]) <= 60: cpu_state[2] = \
                cpu_state[2] + 1
            if int(switch_cpu_load_5min[ip][:-1]) > 60 and int(switch_cpu_load_5min[ip][:-1]) <= 80: cpu_state[3] = \
                cpu_state[3] + 1
            if int(switch_cpu_load_5min[ip][:-1]) > 80: cpu_state[4] = cpu_state[4] + 1
        except:
            cpu_state[5] = cpu_state[5] + 1
        ip = next_ip(ip)


def cpu_statistic():
    s_msg = '<div class="alert alert-info" role="alert">交换机过载/获取错误情况实时统计：'
    msg = s_msg
    for a in list(range(101, 116)) + list(range(121, 135)):
        for b in range(1, switch_numbers[a] + 1):
            ip = "172.16." + str(a) + "." + str(b)
            if switch_overload_times[ip] > 0: msg = msg + "</br>接入交换机" + ip + "连续" + str(
                switch_overload_times[ip]) + "轮扫描过载"
    ip = "172.16.101.1"
    while ip != "":
        try:
            if int(switch_cpu_load_5min[ip][:-1]) == 0: msg = msg + "</br>接入交换机" + ip + "获取错误"
        except:
            msg = msg + "</br>接入交换机" + ip + "获取错误"
        finally:
            ip = next_ip(ip)
    if msg == s_msg:
        msg = s_msg + '</br>所有接入交换机CPU负载正常</div>'
    else:
        msg = msg + '</div>'
    return msg


def onlinestat():  # 交换机在线情况统计（DOWN掉的次数）
    global switch_down_cycles
    global switch_down_stat
    switch_down_stat = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 1,2,3,4,5,6-10,11-20,21-60,61-100,>100
    ip = "172.16.101.1"
    while ip != "":
        if switch_down_cycles[ip] == 1: switch_down_stat[0] = switch_down_stat[0] + 1
        if switch_down_cycles[ip] == 2: switch_down_stat[1] = switch_down_stat[1] + 1
        if switch_down_cycles[ip] == 3: switch_down_stat[2] = switch_down_stat[2] + 1
        if switch_down_cycles[ip] == 4: switch_down_stat[3] = switch_down_stat[3] + 1
        if switch_down_cycles[ip] == 5: switch_down_stat[4] = switch_down_stat[4] + 1
        if switch_down_cycles[ip] >= 6 and switch_down_cycles[ip] <= 10: switch_down_stat[5] = switch_down_stat[5] + 1
        if switch_down_cycles[ip] >= 11 and switch_down_cycles[ip] <= 20: switch_down_stat[6] = switch_down_stat[6] + 1
        if switch_down_cycles[ip] >= 21 and switch_down_cycles[ip] <= 60: switch_down_stat[7] = switch_down_stat[7] + 1
        if switch_down_cycles[ip] >= 61 and switch_down_cycles[ip] <= 100: switch_down_stat[8] = switch_down_stat[8] + 1
        if switch_down_cycles[ip] >= 101: switch_down_stat[9] = switch_down_stat[9] + 1
        ip = next_ip(ip)


def online_statistic():
    s_msg = '<div class="alert alert-info" role="alert">交换机在线情况实时统计：'
    msg = s_msg
    for a in list(range(101, 116)) + list(range(121, 135)):
        for b in range(1, switch_numbers[a] + 1):
            ip = "172.16." + str(a) + "." + str(b)
            if switch_down_cycles[ip] > 0: msg = msg + "</br>接入交换机" + ip + "连续" + str(switch_down_cycles[ip]) + "轮扫描不在线"
    for a in list(range(101, 116)) + list(range(121, 135)):
        for b in range(1, switch_numbers[a] + 1):
            ip = "172.16." + str(a) + "." + str(b)
            if switch_up_and_down_times[ip] > 0: msg = msg + "</br>接入交换机" + ip + "今天累计掉线" + str(
                switch_up_and_down_times[ip]) + "次"
    if msg == s_msg:
        msg = s_msg + '</br>所有接入交换机正常</div>'
    else:
        msg = msg + '</div>'
    return msg


# =====================主线程=====================
# =====================主线程=====================
# =====================主线程=====================

token = refreshtoken()
sendweixinmsg("Time: " + time.strftime("%X") + "\n监控在线", 2, token)  # 发送微信推送，监控在线
threading.Thread(target=scancpu).start()  # 给一条线程慢慢扫CPU
delay_stat = False
threading.Thread(target=delaystat).start()  # 给一条线程负责延迟发统计信息
threading.Thread(target=startweb).start()  # 给一条线程负责web服务
# 下面给每栋分配一条线程
for a in list(range(101, 116)) + list(range(121, 135)):
    threading.Thread(target=scanbuilding, args=(a,), name=a).start()

while 1:
    if time.strftime("%M") == "00": break  # 让后面能够在整点发送统计信息
    time.sleep(60)

while 1:
    token = refreshtoken()
    sendweixinmsg("Time: " + time.strftime("%X") + "\n监控在线", 2, token)  # 发送微信推送，监控在线
    if int(time.strftime("%H")) == 0:
        delay_stat = True  # 发送统计信息
    if int(time.strftime("%H")) == 4:  # 凌晨四点自动重启过载和不稳定的交换机
        ips = []
        for a in list(range(101, 116)) + list(range(121, 135)):
            for b in range(1, switch_numbers[a] + 1):
                ip = "172.16." + str(a) + "." + str(b)
                if switch_overload_times[ip] >= SWITCH_OVERLOAD_ALERT_TIMES or switch_up_and_down_times[
                    ip] >= SWITCH_UP_AND_DOWN_ALERT_TIMES:
                    ips.append(ip)
                switch_up_and_down_times[ip] = 0
        threading.Thread(target=reboot_switches, args=(ips,)).start()  # 这里得改！！！！！！！线程池，worker！！！
    if int(time.strftime("%H")) == 8:
        delay_stat = True  # 发送统计信息
    time.sleep(3598)  # 等待1小时
