from scipy.stats import binom
from tabulate import tabulate
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import math
import operator


import task_Create
from task_Create import Task
from config import Globalmap


class WBAN(object):

    def __init__(self, number, priority, energy):
        # WBAN的编号
        self.number = number
        # WBAN的优先级
        self.priority = priority
        # WBAN剩余能量
        self.energy = energy
        # WBAN的任务列表，不是真实存在的缓冲区
        self.taskList = []
        # WBAN的传输任务等待区
        self.transmitBuffer = []
        # WBAN的执行任务缓冲区
        self.executionBuffer = []
        # WBAN是否可以发送下一个任务
        self.tranState = True
        # WBAN是否可以执行下一个任务
        self.exeState = True

    ##################################################################################################################

    def set_Priority_WBAN(self, priority):
        self.priority = priority

    def set_Energy_WBAN(self, energy):
        self.energy = energy

    ##################################################################################################################

    # 计算当前执行缓冲区或发送缓冲区中的数据量，缓冲区最大数据量为1GB，如果剩余空间不足则需要在任务池中等待，假设任务池是无穷大的
    # 任务生成后按照优先级高低和是否卸载放入本地执行任务池或者发送任务池中
    def return_executionBuffer(self):
        maxSize = pow(2, 30)
        temp = 0
        for i in range(1, len(self.executionBuffer)):
            temp += self.executionBuffer[i].dataSize

        if maxSize - temp >= 1000:
            return 1
        elif maxSize - temp < 1000:
            return -1

    def return_transmitBuffer(self):
        maxSize = pow(2, 30)
        temp = 0
        for i in range(1, len(self.transmitBuffer)):
            temp += self.transmitBuffer[i].dataSize

        if maxSize - temp >= 1000:
            return 1
        elif maxSize - temp < 1000:
            return -1

    ##################################################################################################################

    # 对应WBAN的八个优先级的节点生成任务
    def add_Task_List(self, numOfPacket, Globalmap):
        # 获取当前系统时钟
        time = Globalmap.get_value('clocktime')
        print('当前时间为：'+str(time))
        # 八个优先级任务的数据量
        sizeOfTask = [300, 500, 800, 900, 900, 800, 500, 300]  # 5000bit
        # 在某一时刻，不同优先级任务按照不同概率生成
        probability = [0.8, 0.8, 0.8, 0.3, 0.4, 0.4 *
                       self.priority, 0.2*self.priority, 0.1*self.priority]

        for i in range(0, 8):
            # 判断当前任务是否生成，按照一定的概率随机生成
            p = np.array([probability[i], 1-probability[i]])
            index = np.random.choice([1, 0], p=p.ravel())
            if index == 1:
                value = pow(self.priority, 2) * pow(i+1, 2) * \
                    math.log2(1+sizeOfTask[i])
                value = format(value, '.10f')
                task = Task(0, 0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
                task.set_dataSize_Task(sizeOfTask[i]*numOfPacket)  # 任务的数据量
                task.set_priority_Task(i)  # 任务的优先级，如果卸载处理，其优先级对于任务优先级*WBAN优先级
                task.set_value_Task(value)  # 任务的价值
                task.set_timeslice_Task(time)  # 任务产生时的时间片
                task.set_numWBAN_Task(self.number)  # 任务所隶属的WBAN的编号

                self.taskList.append(task)

    ##################################################################################################################

    # 遍历当前生成的业务列表，根据每个任务是否卸载将其放入对应的列表，等待排序，需要判断这两个缓冲区剩余空间的大小
    def buffer_Allocation(self, Globalmap):

        # 获取当前系统时钟和失效列表
        time = Globalmap().get_value('clocktime')
        unavailableBuffer = Globalmap().get_value('unavailableBuffer')

        # 现将当前生成的任务列表中的任务按照任务优先级从高到低进行排序
        self.taskList = sorted(self.taskList, key=operator.attrgetter('priority'))
        self.taskList = self.taskList.reverse()

        # 获取本地执行缓冲区和发送缓冲区的状况，等于1则可以继续放入任务，等于-1则不能放入任务
        check_1 = self.return_executionBuffer()
        check_2 = self.return_transmitBuffer()

        for i in range(len(self.taskList)):

            # 若当前本地执行Buffer有空闲空间，则将该任务放入本地执行Buffer
            if self.taskList[i].ifOffload == 0:
                # 如果该缓冲区有足够的空间,则放入该任务
                if check_1 == 1:
                    self.executionBuffer.append(self.taskList[i])
                    self.taskList[i].timeInto = time  # 任务进入本地执行Buffer的时间点
                # 如果该缓冲区没有足够的空间，则将该任务放入失效列表
                elif check_1 == -1:
                    self.taskList[i].available = False
                    unavailableBuffer.append(self.taskList[i])

            # 若当前发送Buffer有空闲空间，则将该任务送入发送Buffer
            elif self.taskList[i].ifOffload == 1:
                # 如果该缓冲区有足够的空间,则放入该任务
                if check_1 == 1:
                    self.transmitBuffer.append(self.taskList[i])
                    self.taskList[i].timeInto = time  # 任务进入发送Buffer的时间点
                # 如果该缓冲区没有足够的空间，则将该任务放入失效列表
                elif check_1 == -1:
                    self.taskList[i].available = False
                    unavailableBuffer.append(self.taskList[i])

        # 重新赋值失效列表
        Globalmap().set_value('unavailableBuffer', unavailableBuffer)
        # 清空任务列表
        self.taskList = []

    ##################################################################################################################

    # 检查将要执行或者发送的一个任务在送入CPU/信道时是否会超时
    def checkTaskAvailable(self, Globalmap, Task):

        # 获取当前系统时钟和失效列表
        time = Globalmap().get_value('clocktime')
        unavailableBuffer = Globalmap().get_value('unavailableBuffer')

        # 设置每个优先级的额定处理时延
        maxDelay = [40000, 35000, 30000, 25000, 20000, 15000, 10000, 5000]
        index = Task.priority

        # 如果该任务在本地执行
        if Task.ifOffload == 0:
            # 计算该任务已有的等待时延+在该缓冲区中的时延+执行时延
            temp = time - Task.timeInto + Task.timeWait + Task.timeLocal
            if temp >= maxDelay[index]:
                return -1
            elif temp < maxDelay[index]:
                return 1

        #如果该任务卸载执行
        elif Task.ifOffload == 1:
            # 计算该任务已有的等待时延+在该缓冲区中的时延+发送时延
            temp = time - Task.timeInto + Task.timeWait + Task.timeTransmit
            if temp >= maxDelay[index]:
                return -1
            elif temp < maxDelay[index]:
                return 1



    # 检查WBAN的两个缓冲区中是否有超时的任务，如果有就丢弃
    def checkBufferAvailable(self, Globalmap):
        # 获取当前系统时钟和失效列表
        time = Globalmap().get_value('clocktime')
        unavailableBuffer = Globalmap().get_value('unavailableBuffer')

        # 设置每个优先级的额定处理时延，单位是微秒
        maxDelay = [40000, 35000, 30000, 25000, 20000, 15000, 10000, 5000]

        #分别判断两个缓冲区中的任务是否过去，如果过期就直接删除
        for i in range(1,range(len(self.executionBuffer))):
            temp = time - self.executionBuffer[i].timeInto
            index = self.executionBuffer[i].priority
            if temp < maxDelay[index]:
                continue
            elif temp >= maxDelay[index]:
                unavailableBuffer.append(self.executionBuffer[i])
                # 重新赋值失效列表
                Globalmap().set_value('unavailableBuffer', unavailableBuffer)
                self.executionBuffer.remove(self.executionBuffer[i])

        for i in range(1,range(len(self.transmitBuffer))):
            temp = time - self.transmitBuffer[i].timeInto
            index = self.transmitBuffer[i].priority
            if temp < maxDelay[index]:
                continue
            elif temp >= maxDelay[index]:
                unavailableBuffer.append(self.transmitBuffer[i])
                # 重新赋值失效列表
                Globalmap().set_value('unavailableBuffer', unavailableBuffer)
                self.transmitBuffer.remove(self.transmitBuffer[i])


    ##################################################################################################################

    # 本地执行函数，用于处理本地执行缓冲区的任务  每个时间片执行一次 处理执行缓冲区第一个任务

    def task_execution(self, Globalmap):
        # 获取当前系统时钟
        time = Globalmap().get_value('clocktime')
        finishBuffer = Globalmap().get_value('finishBuffer')
        unavailableBuffer = Globalmap().get_value('unavailableBuffer')

        # 判断当前CPU是否空闲，检查exeState变量
        if self.exeState == False:
            # 检查当前执行缓冲区的第一个任务是否执行完
            if (time - self.executionBuffer[0].timeInto) < self.executionBuffer[0].timeLocal:
                # 当前CPU中的任务还没有执行完
                print('WBAN'+str(self.number)+'正在执行任务')
                return 0
            elif (time - self.executionBuffer[0].timeInto) == self.executionBuffer[0].timeLocal:
                # 当前CPU中的任务执行完毕，将该任务从执行缓冲区中取出，放入完成缓冲区，设置CPU空闲
                self.exeState = True
                finishBuffer.append(self.executionBuffer[0])
                Globalmap.set_value('finishBuffer', finishBuffer)
                del self.executionBuffer[0]
                #self.task_execution(Globalmap)


        if self.exeState == True:

            #首先判断执行缓冲区第一个任务在执行过程中会不会超时
            check = self.checkTaskAvailable(self.executionBuffer[0])

            #如果当前这个任务在执行时会超时，则删除这个任务，执行下一个任务
            if check == -1:
                self.exeState = True
                #将不满足执行统条件的任务送入失效列表
                unavailableBuffer.append(self.executionBuffer[0])
                Globalmap.set_value('unavailableBuffer', unavailableBuffer)
                del self.executionBuffer[0]
                self.task_execution(Globalmap)
            #如果不会超时
            elif check == 1:
                self.executionBuffer[0].timeWait += time - self.executionBuffer[0].timeInto  # 该任务在执行缓冲区中等待的时间
                self.executionBuffer[0].timeInto = time   # 开始执行该任务的起始时间
                self.executionBuffer[0].set_Local_Task()  # 计算该任务的本地执行时延和本地执行能耗
                self.exeState = False                     #设置CPU被占用
                #计算WBAN剩余的能量
                energy = self.energy - self.executionBuffer[0].energyLocal
                self.set_Energy_WBAN(energy)

                return 0
            

    ##################################################################################################################

    # WBAN发送缓冲区的管理，判断当前信道是否可用，发送出的任务放入MEC的等待缓冲区，每个时间片执行一次 处理发送缓冲区第一个业务
    def task_transmit(self, Globalmap):

        # 获取当前系统时钟和距离,以及递归时需要用的临时变量
        time = Globalmap().get_value('clocktime')
        distance = Globalmap().get_value('distance')
        unavailableBuffer = Globalmap().get_value('unavailableBuffer')
        temp = Globalmap().get_value('temp')

        # 检查当前信道是否空闲，检查tranState变量
        if self.tranState == False:
            # 检查发送缓冲区第一个业务是否已经发送完
            if (time - self.transmitBuffer[0].timeInto) < self.transmitBuffer[0].timeTransmit:
                # 当前的任务还没有发送完
                print('WBAN'+str(self.number)+'正在发送任务')
                return 0
            elif (time - self.transmitBuffer[0].timeInto) == self.transmitBuffer[0].timeTransmit:
                # 当前信道里的任务已经发送完了，将该任务从发送缓冲区中取出，并用return返回该任务，并存入MEC服务器的等待缓冲区
                self.tranState = True
                temp = self.transmitBuffer[0]
                Globalmap().set_value('temp',temp)
                del self.transmitBuffer[0]
                #self.task_transmit(Globalmap)


        if self.tranState == True:

            #首先判断发送缓冲区第一个任务在执行过程中会不会超时
            check = self.checkTaskAvailable(self.transmitBuffer[0])

            #如果当前这个任务在发送时会超时，则删除这个任务，执行下一个任务
            if check == -1:
                self.exeState = True
                #将不满足发送统条件的任务送入失效列表
                unavailableBuffer.append(self.transmitBuffer[0])
                Globalmap.set_value('unavailableBuffer', unavailableBuffer)
                del self.transmitBuffer[0]
                self.task_transmit(Globalmap)   #递归
            #如果不会超时
            elif check == 1:
                self.transmitBuffer[0].timeWait += time - self.executionBuffer[0].timeInto  # 该任务在发送缓冲区中等待的时间
                self.transmitBuffer[0].timeInto = time   # 开始发送该任务的起始时间
                self.transmitBuffer[0].set_Transmit_Task(distance)  # 计算该任务的本地执行时延和本地执行能耗
                self.tranState = False                     #设置CPU被占用
                #计算WBAN剩余的能量
                energy = self.energy - self.transmitBuffer[0].energyLocal
                self.set_Energy_WBAN(energy)

                return temp
        

    ##################################################################################################################

    # 打印当前WBAN所有任务的属性值
    def print_TaskList(self):

        KEYS = ['数据量', '优先级', '价值', '本地频率', '本地时延', '本地能耗', '云频率', '云时延',
                '云能耗', '带宽', '发送时延', '发送能耗', '决策', '报酬', '网号', '排队时延', '时间片', '有效']
        VALUE = []
        for i in range(len(self.taskList)):
            value = self.taskList[i].__dict__.values()
            value = list(value)
            for i in range(0, 2):
                value.pop(16)
            value = [float(x) for x in value]
            VALUE.append(value)
        print()
        print("WBAN " + str(self.priority) + " 任务细节如下：")
        print(tabulate(VALUE, headers=KEYS, tablefmt='rst', disable_numparse=True))
        print()
        print()

    ##################################################################################################################

    # 输出当前在发送缓冲区内的任务细节
    def printTransmitBuffer(self):

        KEYS = ['数据量', '优先级', '价值', '本地频率', '本地时延', '本地能耗', '云频率', '云时延',
                '云能耗', '带宽', '发送时延', '发送能耗', '决策', '报酬', '网号', '排队时延', '时间片', '有效']
        VALUE = []
        for i in range(len(self.transmitBuffer)):
            value = self.transmitBuffer[i].__dict__.values()
            value = list(value)
            for i in range(0, 2):
                value.pop(16)
            value = [float(x) for x in value]
            VALUE.append(value)
        print()
        print("WBAN " + str(self.priority) + " 发送缓冲区细节如下：")
        print(tabulate(VALUE, headers=KEYS, tablefmt='rst', disable_numparse=True))
        print()
        print()

    ##################################################################################################################

    # 输出当前在执行缓冲区内的任务细节
    def printExecutionBuffer(self):

        KEYS = ['数据量', '优先级', '价值', '本地频率', '本地时延', '本地能耗', '云频率', '云时延',
                '云能耗', '带宽', '发送时延', '发送能耗', '决策', '报酬', '网号', '排队时延', '时间片', '有效']
        VALUE = []
        for i in range(len(self.executionBuffer)):
            value = self.executionBuffer[i].__dict__.values()
            value = list(value)
            for i in range(0, 2):
                value.pop(16)
            value = [float(x) for x in value]
            VALUE.append(value)
        print()
        print("WBAN " + str(self.priority) + " 执行缓冲区细节如下：")
        print(tabulate(VALUE, headers=KEYS, tablefmt='rst', disable_numparse=True))
        print()
        print()

    ##################################################################################################################

'''
gl = Globalmap()
gl._init_()
WBAN_A = WBAN(1, 1, 1000)
WBAN_A.add_Task_List(1, gl)
WBAN_A.print_TaskList()
'''