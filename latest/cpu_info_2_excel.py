# encoding: utf-8
from xlsxwriter.workbook import Workbook
from mod_cpu import getcpuinfo
import threading, time, shutil

'''
说明：该脚本用于获取所有接入交换机的 CPU 5分钟平均使用率，4秒可以扫完并导出excel表格。
'''

SWITCHS = 668  # 总的交换机数
thread_finished = 0  # 线程每结束一个，就加一，等于SWITCHS时表示已完成任务
lock = threading.Lock()

switch_numbers = {}
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


def writecpuinfo(ip, c):
    global thread_finished
    cpu = getcpuinfo(ip)
    worksheet.write(c, 0, ip)
    worksheet.write(c, 1, cpu)
    thread_finished = thread_finished + 1  # 线程每结束一个，就加一
    print(threading.current_thread().name, "Finished")


def cpuinfo2excel():
    global worksheet
    filename = 'cpuinfo_' + time.strftime("%Y_%m_%d_%H_%M_%S") + '.xlsx'
    workbook = Workbook(filename)
    worksheet = workbook.add_worksheet()
    column_head = ['IP地址', 'CPU 5分钟使用率']
    y = 0
    for column in column_head:
        worksheet.write(0, y, column)
        y += 1
    y = 1

    a = 101
    b = 1
    c = 1
    while 1:
        ip = "172.16." + str(a) + "." + str(b)
        t = threading.Thread(target=writecpuinfo, args=(ip, c,))
        t.start()
        time.sleep(0.01)
        c = c + 1
        # 设置下一个交换机IP
        b = b + 1
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
    while 1:
        if thread_finished == SWITCHS: break  # 等所有线程结束完
        time.sleep(0.1)
    workbook.close()
    shutil.move(filename, "static/" + filename)
    return filename


if __name__ == '__main__':
    cpuinfo2excel()
