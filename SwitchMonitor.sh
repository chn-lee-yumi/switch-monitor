#!/bin/bash
sleep 20 # 开机运行脚本时等待网络启动
ntpdate cn.pool.ntp.org
cd /home/monitor/SwitchMonitor
python3 SwitchMonitor.py
