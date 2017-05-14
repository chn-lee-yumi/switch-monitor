from mod_reboot_switch import reboot_switch
import time
import threading

'''
说明：该脚本用于批量重启交换机
'''

def reboot_switches(ips):
    for ip in ips:
        threading.Thread(target=reboot_switch,args=(ip,)).start()
    time.sleep(300) # 等待线程执行完毕