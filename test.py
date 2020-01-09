from scipy.stats import binom
from tabulate import tabulate
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import math

from config import Globalmap
from task_Create import Task
from WBAN_Create import WBAN

'''
p = np.array([0.6,0.4])
index = np.random.choice([1,0],p=p.ravel())
print(index)

a = [1,2,3]
b = [4,5,6]
a.extend(b)
print(a)



gl = Globalmap()
gl._init_()
print(gl.get_value('clocktime'))
gl.set_value('clocktime',1)
print(gl.get_value('clocktime'))
gl2 = Globalmap()
print(gl2.get_value('clocktime'))


gl = Globalmap()
gl._init_()

WBAN_A = WBAN(1, 1000, [], [], [], [],True,False)
WBAN_A.add_Task_List(1,gl)


a = [ []for i in range(2) ]
a[0] = [1,2,3]
del a[0][0]
print(a)


task1 = Task(0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2)
task2 = Task(0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2)
task3 = Task(0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)

task = []
task.append(task1)
task.append(task2)
task.append(task3)
task.sort(key = lambda x: (x.timeslice, x.priority))

KEYS = ['数据量', '优先级', '价值', '本地频率', '本地时延', '本地能耗', '云频率', '云时延',
    '云能耗', '带宽', '发送时延', '发送能耗', '决策', '报酬', '网号', '排队时延', '时间片','有效']
VALUE = []
for i in range(len(task)):
    value = task[i].__dict__.values()
    value = list(value)
    for i in range(0, 2):
        value.pop(16)
    value = [float(x) for x in value]
    VALUE.append(value)
print()
print(tabulate(VALUE, headers=KEYS, tablefmt='rst', disable_numparse=True))
print()


def c(l):
    for i in range(len(l)):
        print(l[i])

a = [1,2,3,4,5,6,7,8,9]
c(a)
'''

a = [1,2,3,4,5,6,7]
a.remove(2)
print( a)
