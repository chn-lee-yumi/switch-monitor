# encoding: utf-8
import requests
import json
import time

'''
该模块用于发送微信推送
用法：token=refreshtoken()
返回字符串access_token。
用法：sendweixinmsg(msg, agentid, token)
msg为推送内容
agentid为应用id
token为前面得到的access_token
无返回值，结果会输出到屏幕。
'''

corpid = "wx0dfgsdhfsd134c36"
corpsecret = "Lh8fvzSvpfdgskjghfdg783grf3irfg783g7HIlMYhmv2"


def refreshtoken():
    t1 = time.time()
    a = requests.get("https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=" + corpid + "&corpsecret=" + corpsecret).text
    a = json.loads(a)
    t2 = time.time()
    print("连接微信服务器所用的时间：%.3f秒" % (t2 - t1))
    return a['access_token']


def sendweixinmsg(msg, agentid, token):
    t1 = time.time()
    datas = '{"touser": "@all","msgtype": "text","agentid": ' + str(agentid) + ',"text":{"content": "' + msg + '"}}'
    a = requests.post("https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=" + token,
                      data=datas.encode('utf-8'))
    print("**********************")
    print(msg)
    print(a.text)
    t2 = time.time()
    print("发送推送所用的时间：%.3f秒" % (t2 - t1))