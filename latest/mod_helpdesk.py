# encoding: utf-8
import json

import requests


def send_incident(building_name, switch_ip):
    if building_name == "东一":
        building_location = 1
    elif building_name == "东二":
        building_location = 2
    elif building_name == "东三":
        building_location = 3
    elif building_name == "东四":
        building_location = 4
    elif building_name == "东五":
        building_location = 5
    elif building_name == "东六":
        building_location = 6
    elif building_name == "东七":
        building_location = 7
    elif building_name == "东八":
        building_location = 8
    elif building_name == "东九":
        building_location = 9
    elif building_name == "东十":
        building_location = 10
    elif building_name == "东十二":
        building_location = 12
    elif building_name == "东十三":
        building_location = 13
    elif building_name == "东十四":
        building_location = 14
    elif building_name == "西一":
        building_location = 18
    elif building_name == "西二":
        building_location = 19
    elif building_name == "西三":
        building_location = 20
    elif building_name == "西四":
        building_location = 21
    elif building_name == "西五":
        building_location = 22
    elif building_name == "西六":
        building_location = 23
    elif building_name == "西七":
        building_location = 24
    elif building_name == "西八":
        building_location = 25
    elif building_name == "西九":
        building_location = 26
    elif building_name == "西十":
        building_location = 27
    elif building_name == "西十一":
        building_location = 28
    elif building_name == "西十二":
        building_location = 29
    elif building_name == "西十三":
        building_location = 30
    elif building_name == "西十四":
        building_location = 31
    # …………………………
    else:
        building_location = 2
        # return 1

    '''
    datas={"formId":"1",
    "processId":"fbfbdae025bb44c093ab7ad8d3520830",
    "processInstanceId":"",
    "activityInstanceId":"",
    "activityId":"84d8011ea67d4502b461e8637e02ff25",
    "itemId":"",
    "activityName":"开始",
    "appId":"",
    "attach_code":"92EA6212938992A8C0DBEAF604F21273",
    "status_id":"7",
    "type_id":"1",
    "contacts_id":"",
    "emploeeid":"",
    "contacts_phone":"",
    "contacts_name":"",
    "port_code":"端口编号",
    "internet_account":"",
    "contacts_dept":"",
    "contacts_email":"",
    "source":"4",
    "hostel":"",
    "port":"",
    "ip":"",
    "emailuser":"",
    "category":"28",
    "priority_code":"20",
    "emailpwd":"",
    "area":"58",
    "location_id":"2",
    "location":"",
    "title":"标题",
    "template_id":"",
    "description":"<p>描述</p>",
    "resolution_code":"",
    "logical_id":"",
    "logical_name":"",
    "resolution":"",
    "time":"1"}
    '''

    # 模拟登录。用户名密码是加密过的，在浏览器用F12抓包获得。
    a = requests.get(
        "http://helpdesk1.gdut.edu.cn/portal/edulogin?username=12345%3D%3D&password=12345&safe=1")
    print(a.cookies)
    # print(a.text)

    # http://helpdesk.gdut.edu.cn/portal/itsmLocation/lists.action?parentId=58 访问此链接，可以获取楼栋对应的 location_id

    # 保存工单
    datas = {
        "formId": "1",
        "processId": "ebfbdae025bb44c093ab7ad8d3520830",  # 这个是固定的
        "activityId": "84d8011ea67d4502b461e8637e02ff25",  # 这个是固定的
        "activityName": "开始",
        "status_id": "7",
        "type_id": "1",
        "category": "28",
        "priority_code": "20",
        "area": "58",
        "location_id": 2,  # building_location 楼栋。东一到东十四：1到14  西一到西十四：18-31
        "title": "交换机故障检查 " + switch_ip,
        "description": "交换机IP：" + switch_ip + "\n检查步骤：\n1.交换机是否通电开机了\n2.交换机到汇聚的线有没有问题\n3.汇聚是否通电开机了\n4.汇聚光纤端口的灯有没有亮 ",
        "time": "1"}
    b = requests.post("http://helpdesk1.gdut.edu.cn/portal/wfe/save.action", cookies=a.cookies,
                      data=datas)
    print(b.text)
    # 返回内容{"activityId":"84d8011ea67d4502b461e8637e02ff25","activityInstanceId":"5e48e28b58cd6a4201592c5cdc75245e","activityName":"开始","appId":"INC-10100282","author":"3115006254","authorName":"利昱旻","docStatus":"","formId":"1","itemId":"5e48e28b58cd6a4201592c5cdc75245f","parentProcessInstanceId":"","processId":"ebfbdae025bb44c093ab7ad8d3520830","processInstanceId":"5e48e28b58cd6a4201592c5cdc74245d","processName":"","status":"new","title":"1"}
    c = json.loads(b.text)
    print(c["appId"])  # 工单编号

    # 不需要的步骤，返回一个转一线二线处理的页面
    # http://helpdesk.gdut.edu.cn/portal/wfe/getRuoteList.action?activityId=84d8011ea67d4502b461e8637e02ff25&appId=INC-10100282&formId=1

    # 获取用户列表
    e = requests.post(
        "http://helpdesk1.gdut.edu.cn/portal/wfe/getUsers.action?activityId=d3d147a82cf0458381ca79ff39c8ff08&isBack=N&appId=" +
        c["appId"] + "&hasextenduser=Y&formId=1", cookies=a.cookies)
    print(e.text)
    e2 = json.loads(e.text)
    e_orgid = ""
    e_orgname = ""
    e_orgtype = ""
    for e_everyone in e2:
        e_orgid = e_orgid + e_everyone['orgid'] + ","
        e_orgname = e_orgname + e_everyone['orgname'] + ","
        e_orgtype = e_orgtype + e_everyone['orgtype'] + ","
    print(e_orgid)
    print(e_orgname)
    # http://helpdesk.gdut.edu.cn/portal/wfe/getUsers.action?activityId=d3d147a82cf0458381ca79ff39c8ff08&isBack=N&appId=INC-10100282&hasextenduser=Y&formId=1

    # 工单加绿色点
    f = requests.post("http://helpdesk.gdut.edu.cn/portal/sla/sla_addRecord.action?id=" + c["appId"],
                      cookies=a.cookies)

    # 下面是转一线处理
    datas = {
        "appId": c["appId"],
        "processId": "ebfbdae025bb44c093ab7ad8d3520830",
        # "formId": "1",
        "processInstanceId": c["processInstanceId"],
        "activityInstanceId": c["activityInstanceId"],
        "itemId": c["itemId"],
        "activityId": "84d8011ea67d4502b461e8637e02ff25",
        "orgIds": e_orgid,
        "orgNames": e_orgname,
        "orgTypes": e_orgtype,
        "routeId": "e84fd80751ae4b58837ddb732462cf12",
        # "routeName": "转一线处理",
        "nextActivityId": "d3d147a82cf0458381ca79ff39c8ff08",
        # "memo": "",
        # "isEnd": "N",
        # "title": "测试",
        # "entityExt": "status_id=8",
        # "sendsms": "1"
    }
    g = requests.post("http://helpdesk1.gdut.edu.cn/portal/wfe/submit.action", cookies=a.cookies, data=datas)
    print("工单提交状况：" + g.text)

    return 0


if __name__ == '__main__':
    send_incident("东二", "172.16.102.1")

