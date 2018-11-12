# encoding: utf-8
import json
import time
import requests
from Config import corpid, corpsecret, WEIXIN_ENABLE

'''
该模块用于发送微信推送
用法：token=refreshtoken()
返回字符串access_token。
用法：sendweixinmsg(msg, agentid)
msg为推送内容
agentid为应用id
无返回值，结果会输出到屏幕。
TODO：处理网络异常。
'''

token = [''] * len(corpsecret)


def get_token(agentid):
    if WEIXIN_ENABLE:
        try:
            a = requests.get(
                "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=" + corpid + "&corpsecret=" + corpsecret[
                    agentid]).text
            a = json.loads(a)
            return a['access_token']
        except:
            print("[Error] Get Weixin token error!")
            return 0


def send_weixin_msg(msg, agentid):  # agentid: 2=监控程序调试信息 6=学生宿舍交换机监控
    if WEIXIN_ENABLE:
        global token
        t1 = time.time()
        datas = '{"touser": "@all","msgtype": "text","agentid": ' + str(agentid) + ',"text":{"content": "' + msg + '"}}'
        try:
            a = requests.post("https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=" + token[agentid],
                              data=datas.encode('utf-8'))
            b = json.loads(a.text)  # 检查是否发送成功
            if b['errcode'] != 0:  # 可能是token过期，重新获取token
                refresh_token()
                a = requests.post("https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=" + token[agentid],
                                  data=datas.encode('utf-8'))
        except:
            print("[Error] Send Weixin message error!")
        print("*" * 30)
        print("微信通知：", msg)
        print(a.text)
        t2 = time.time()
        print("发送推送所用的时间：%.3f秒" % (t2 - t1))
        print("*" * 30)


def refresh_token():
    # 注：这里需要根据需要定制，参考Config.py，我使用了编号为2和6的两个应用（查看看微信企业号后台，根据需要自行设置）
    if WEIXIN_ENABLE:
        token[2] = get_token(2)
        token[6] = get_token(6)


if __name__ == '__main__':
    refresh_token()
    send_weixin_msg("测试", 2)
