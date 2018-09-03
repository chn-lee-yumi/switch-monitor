# encoding: utf-8
import time


def runtime(func):  # 计算函数运行时间
    def wrapper(*args):
        tmp_time = time.time()
        func(*args)
        print("运行时间：", time.time() - tmp_time)

    return wrapper
