# -*- coding = utf-8 -*-
# @Author: yinzs Wang
# @Time: 2021/1/25 21:18
# @File: CustomFunction.py
# @Software: PyCharm

def counter(last=[0]):
    '''
    用于次数统计
    :param last: 起始次数 <class 'list'>
    :return: 使用次数 <class 'int'>
    '''
    next = last[0] + 1
    last[0] = next
    return next
