from scipy.stats import binom
from tabulate import tabulate
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import math
import operator

import task_Create
from task_Create import Task
from WBAN_Create import WBAN
from config import Globalmap


class MEC(object):

    # 设置单个MEC服务器共具备四个工作缓冲区
    def __init__(self):
        self.sizeOfBuffer = [pow(2, 20), pow(2, 20), pow(2, 20), pow(2, 20)]                # 服务器共有四个CPU执行缓冲区，每一个总大小为1MB
        self.executionBuffer = [[]for i in range(4)]                                        # 每个WBAN共四个CPU，各有一个执行缓冲区
        self.waitBuffer = []                                                                # 等待分配缓冲区，该缓冲区的容量默认为无限大
        self.exeBufferState = [True, True, True, True]                                      # 当前四个CPU是否可以执行CPU缓冲区中的下一个任务
        self.virtualBuffer = []                                                             # 虚拟缓冲区，由于
        

    ##################################################################################################################

    def waitbuffer_addTask(self, Task):
        # 每次向等待分配缓冲区放入一个任务，都需要将缓冲区队列进行一次排序,排队缓冲区内按优先级从高到低排列
        self.waitBuffer.append(Task)
        self.waitBuffer = sorted(self.waitBuffer, key=operator.attrgetter('priority'))
        self.waitBuffer = self.waitBuffer.reverse()

    ##################################################################################################################

    # 将WBAN发送到MEC服务器中的任务放入到waitBuffer中，每个时间片执行一次
    def receive_Task(self, WBAN, Globalmap):

        # 获取当前系统时钟和距离
        time = Globalmap().get_value('clocktime')
        distance = Globalmap().get_value('distance')

        # 获取当前WBAN是否完成一个任务的发送
        check = WBAN.task_transmit(Globalmap, distance)

        # 如果没有发送成功，即task_transmit函数的返回值是0
        if check == 0:
            return 0
        # 如果有一个任务发送成功，即task_transmit函数的返回值是一个Task类对象
        elif check != 0:
            check.timeWait += time - check.timeInto                     # 任务在信道中的等待时间
            check.timeInto = time                                       # 设定该任务进入等待分配缓冲区的时间
            self.waitbuffer_addTask(check)                              # 将该任务放入waitbuffer中，等待分配

    ##################################################################################################################

    # 将排队缓冲区的任务分配到各个CPU缓冲区中
    def buffer_Allocation(self, Globalmap):

        # 获取当前系统时钟
        time = Globalmap().get_value('clocktime')

        for i in range(len(self.waitBuffer)):
            free = self.sizeOfBuffer
            if max(free) >= self.waitBuffer[i]:

                # 给当前任务赋值进入缓冲区的时间
                self.waiterbuffer[i].timeInto = time

                # 如果四个缓冲区中最大的空闲空间大于当前任务的数据量，则把这个任务放入该缓冲区中
                index = free.index(max(free))
                self.executionBuffer[index].append(self.waitBuffer[i])
                self.sizeOfBuffer[index] -= self.waitBuffer[i].dataSize

                # 从等待缓冲区中删除该任务
                self.waitBuffer.pop(self.waitBuffer[i])

                return 1  # 返回值为1，表示的当前缓冲区有空，可以接收任务

            elif max(free) <= self.waitBuffer[i]:
                # 如果当前四个缓冲区都没有合适的空闲区，就等待下一个时间片，返回-1表示当前服务器中无法接受任务
                return -1

    ##################################################################################################################

