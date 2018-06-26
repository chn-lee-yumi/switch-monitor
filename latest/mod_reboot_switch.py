# encoding: utf-8
import telnetlib
import time
import traceback
import mod_snmp


'''
该模块用于重启交换机
用法：reboot_switches(ips)
ips为需重启交换机IP的list，如["172.16.101.1","172.16.101.2"]
无返回值。
'''

switch_password = "123456"  # 密码


def reboot_switch_telnet(ip):
    try:
        # 连接Telnet服务器
        print('Connecting', ip, '...')
        tn = telnetlib.Telnet(ip, port=23, timeout=2)
        # tn.set_debuglevel(2)
        a = time.time()
        # 输入登录密码
        print('Connected. Logining...')
        tn.read_until('assword:'.encode('gbk'), 5)
        tn.write(switch_password.encode('gbk') + b'\n')
        # 登录完毕后执行命令
        tn.read_until('>'.encode('gbk'), 5)
        print('Login succeed! Rebooting...')
        tn.write("reboot\n".encode('gbk'))
        a = tn.read_until("[Y/N]".encode('gbk'), 60)
        print(a)
        tn.write("y\n".encode('gbk'))
        print('Send "y"')
        if a.decode('GBK').find('This command will reboot the device') != -1:
            a=tn.read_until("):".encode('gbk'), 60)
            print(a)
            if a.decode==':y':
                tn.close()
                print('reboot succeed!')
                return
            tn.write("\n".encode('gbk'))
            print('Send "\\n"')
            print(tn.read_until("[Y/N]".encode('gbk'), 60))
            tn.write("y\n".encode('gbk'))
            print('Send "y"')
            print(tn.read_until("[Y/N]".encode('gbk'), 60))
            tn.write("y\n".encode('gbk'))
            print('Send "y"')
        # 执行完毕后关闭连接
        tn.close()
        print('reboot succeed!')
    except:
        a = traceback.format_exc()
        print(a[a.find('Error:') + 7:])

def reboot_switch_snmp(ip):
    a=mod_snmp.SnmpSet(ip,'S2700',"reboot")# E152B不支持SNMP重启（我没找到MIB节点）
    # print("重启交换机",ip,a)
    return 0

def reboot_switches(ips):
    for ip in ips:
        reboot_switch_snmp(ip)
        #reboot_switch_telnet(ip)


'''
<D2_4F_H2_E152B_1>reboot
 Start to check configuration with next startup configuration file, please wait.........DONE!
 This command will reboot the device. Current configuration will be lost, save current configuration? [Y/N]:y
Please input the file name(*.cfg)[flash:/config.cfg]
(To leave the existing filename unchanged, press the enter key):
flash:/config.cfg exists, overwrite? [Y/N]:y
 Validating file. Please wait....
 The current configuration is saved to the active main board successfully.
 Configuration is saved to device successfully.
 This command will reboot the device. Continue? [Y/N]:y

<X1_4F_H3_S3050_4>reboot
 This will reboot Switch. Continue? [Y/N] y
 '''
