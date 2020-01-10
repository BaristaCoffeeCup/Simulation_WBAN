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

        # 每个WBAN共四个CPU，各有一个执行缓冲区
        self.executionBuffer = [[]for i in range(4)]
        # 等待分配缓冲区，该缓冲区实际并不存在
        self.waitBuffer = []
        # 当前四个CPU是否可以执行CPU缓冲区中的下一个任务
        self.exeBufferState = [True, True, True, True]
        # 当前四个CPU中的执行缓冲区中的数据量
        self.sizeOfBuffer = [0, 0, 0, 0]

    ##################################################################################################################

    def waitbuffer_addTask(self, Task):
        # 每次向等待分配缓冲区放入一个任务，都需要将缓冲区队列进行一次排序,排队缓冲区内按优先级从高到低排列
        self.waitBuffer.append(Task)
        self.waitBuffer = sorted(self.waitBuffer, key=operator.attrgetter('priority'))
        self.waitBuffer = self.waitBuffer.reverse()

    ##################################################################################################################

    # 将WBAN发送到MEC服务器中的任务放入到waitBuffer中，每个时间片执行一次
    # 该函数的参数WBANList是指将系统中多个WBAN放入到一个列表中
    def receive_Task(self, WBANList, Globalmap):

        # 获取当前系统时钟和距离
        time = Globalmap().get_value('clocktime')
        distance = Globalmap().get_value('distance')

        # 对当前系统里的所有用户进行一个判断，判断是否有WBAN发送完任务
        for i in range(len(WBANList)):
            # 获取当前WBAN是否完成一个任务的发送
            check = WBAN[i].task_transmit(Globalmap)
            # 如果没有发送成功，task_transmit函数的返回值是0,则继续处理下一个任务
            if check == 0:
                continue
            # 如果有一个任务发送成功，即task_transmit函数的返回值是一个Task类对象
            elif check != 0:
                # 将该任务放入虚拟缓冲区中
                self.waitbuffer_addTask(check)

    ##################################################################################################################

    # 将排队缓冲区的任务分配到各个CPU缓冲区中
    def buffer_Allocation(self, Globalmap):

        # 获取当前系统时钟
        time = Globalmap().get_value('clocktime')

        for i in range(len(self.waitBuffer)):
            choice = min(self.sizeOfBuffer)

            # 给当前任务赋值进入缓冲区的时间
            self.waiterbuffer[i].timeInto = time

            # 选择当前数据量最小的缓冲区，将当前任务放入该缓冲区
            index = self.waitBuffer.index(choice)
            self.executionBuffer[index].append(self.waitBuffer[i])
            self.sizeOfBuffer[index] += self.waitBuffer[i].dataSize

    # 当虚拟缓冲区中的任务都分配到CPU缓冲区中，将虚拟缓冲区清空
    self.waitBuffer = []

    ##################################################################################################################

    # 卸载任务处理函数，计算卸载任务的处理时延和处理能耗
    def MEC_TaskExecution(self, Globalmap):
        # 获取当前系统时钟
        time = Globalmap().get_value('clocktime')
        finishBuffer = Globalmap().get_value('finishBuffer')
        unavailableBuffer = Globalmap().get_value('unavailableBuffer')

        # 首先循环判断当前四个CPU是否空闲
        for i in range(len(self.executionBuffer)):
            # 判断每一个CPU是否被占用
            if self.exeBufferState[i] == False:
                # 如果该任务还没有执行完
                if (time - self.executionBuffer[i][0].timeInto) < self.executionBuffer[i][0].timeMEC:
                    self.exeBufferState[i] == False
                    continue
                # 如果该任务执行完了
                elif (time - self.executionBuffer[i][0].timeInto) == self.executionBuffer[i][0].timeMEC:
                    self.exeBufferState[i] == True
                    finishBuffer.append(self.executionBuffer[i][0])
                    Globalmap.set_value('finishBuffer',finishBuffer)
                    del self.executionBuffer[i][0]

        #将处理完成的任务取出后，再处理缓冲区中的下一个任务
        for i in range(len(self.executionBuffer)):
            
            #判断当前将要执行的任务在执行时是否会超时
            check = WBAN.checkTaskAvailable(self.executionBuffer[i][0])

            if check == -1:
                self.exeBufferState[i] == True
                #将不满足执行统条件的任务送入失效列表
                unavailableBuffer.append(self.executionBuffer[i][0])
                Globalmap.set_value('unavailableBuffer', unavailableBuffer)
                del self.executionBuffer[i][0]
                self.MEC_TaskExecution(Globalmap)

            elif check == 1:
                self.waitBuffer[i][0].timeWait += time - self.waitBuffer[i][0].timeInto     #任务在执行缓冲区中等待的时间
                self.waitBuffer[i][0].set_MEC_Task()                                        #计算该任务的卸载执行时延和能耗
                self.waitBuffer[i][0].timeInto = time                                       #该任务调度进入CPU的时间
                self.exeBufferState[i] == False

    ##################################################################################################################
