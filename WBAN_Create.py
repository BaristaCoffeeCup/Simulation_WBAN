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

    def __init__(self, number, priority, energy, taskList, waitBuffer, transmitBuffer, executionBuffer,finishBuffer, tranState,exeState):
        #WBAN的编号
        self.number = number
        # WBAN的优先级
        self.priority = priority
        # WBAN剩余能量
        self.energy = energy
        # WBAN的任务列表，不是真实存在的缓冲区
        self.taskList = taskList
        #WBAN的任务池，默认空间为无穷大，分为两个部分，本地执行或者卸载执行
        self.waitBuffer = [ []for i in range(2) ]
        # WBAN的传输任务等待区
        self.transmitBuffer = transmitBuffer
        # WBAN的执行任务缓冲区
        self.executionBuffer = executionBuffer
        #WBAN的完成任务缓冲区，记录在本地执行完的任务
        self.finishBuffer = finishBuffer
        #WBAN是否可以发送下一个任务
        self.tranState = True
        #WBAN是否可以执行下一个任务
        self.exeState = False

    ##################################################################################################################

    def set_Priority_WBAN(self, priority):
        self.priority = priority

    def set_Energy_WBAN(self, energy):
        self.energy = energy

    ##################################################################################################################

    #计算当前执行缓冲区或发送缓冲区中的数据量，缓冲区最大数据量为1MB，如果剩余空间不足则需要在任务池中等待，假设任务池是无穷大的
    #任务生成后按照优先级高低和是否卸载放入本地执行任务池或者发送任务池中
    def return_executionBuffer(self):
        maxSize = pow(2, 20)
        temp = 0
        for i in range(len(self.executionBuffer)):
            temp += self.executionBuffer[i].dataSize

        if maxSize - temp >= 1000:
            return 1
        elif maxSize - temp < 1000:
            return -1

    def return_transmitBuffer(self):
        maxSize = pow(2, 20)
        temp = 0
        for i in range(len(self.transmitBuffer)):
            temp += self.transmitBuffer[i].dataSize

        if maxSize - temp >= 1000:
            return 1
        elif maxSize - temp < 1000:
            return -1

   
    ##################################################################################################################
     
    # 对应WBAN的八个优先级的节点生成任务
    def add_Task_List(self, numOfPacket,Globalmap):
        #获取当前系统时钟
        time = Globalmap.get_value('clocktime')
        print('当前时间为：'+str(time))
        # 八个优先级任务的数据量
        sizeOfTask = [300, 500, 800, 900, 900, 800, 500, 300]  # 5000bit
        # 在某一时刻，不同优先级任务按照不同概率生成
        probability = [0.8, 0.8, 0.8, 0.3, 0.4, 0.4*self.priority, 0.2*self.priority, 0.1*self.priority]

        for i in range(0, 8):
            # 判断当前任务是否生成，按照一定的概率随机生成
            p = np.array([probability[i], 1-probability[i]])
            index = np.random.choice([1, 0], p=p.ravel())
            if index == 1:
                value = pow(self.priority, 2) * pow(i+1, 2) * math.log2(1+sizeOfTask[i])
                task = Task(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
                task.set_dataSize_Task(sizeOfTask[i]*numOfPacket)       #任务的数据量
                task.set_priority_Task(i)                               #任务的优先级，如果卸载处理，其优先级对于任务优先级*WBAN优先级
                task.set_value_Task(value)                              #任务的价值
                task.set_timeslice_Task(time)                           #任务产生时的时间片
                task.set_numWBAN_Task(self.number)                      #任务所隶属的WBAN的编号
                #task.set_timeInto_Task = time                           #任务进入任务池的时间
                self.taskList.append(task)
            

    ##################################################################################################################
    
    # 遍历当前生成的业务列表，根据每个任务是否卸载将其放入对应的列表，等待排序，需要判断这两个缓冲区剩余空间的大小
    def buffer_Allocation(self,Globalmap):
        
        #获取当前系统时钟
        time = Globalmap().get_value('clocktime')

        #现将当前生成的任务列表中的任务按照任务优先级从高到低进行排序
        self.taskList = sorted(self.taskList,key = operator.attrgetter('priority'))
        self.taskList = self.taskList.reverse()
        for i in range(len(self.taskList)):
            self.taskList[i].timeInto = time                #设定任务进入任务池的时间
            #进入任务池中的本地执行缓冲池
            if self.taskList[i].ifOffload == 0:
                self.waitBuffer[0].append(self.taskList[i])
            #进入任务池中的卸载处理缓冲池
            elif self.taskList[i].ifOffload == 1:
                self.waitBuffer[1].append(self.taskList[i])


        #从两个任务池的第一个任务开始处理，根据其卸载决策进行缓冲区分组
        #本地执行任务池，串行模式将本地执行任务送入本地执行缓冲区
        while(1):
            #获取本地执行缓冲区的状况，等于1则可以继续放入任务，等于-1则不能放入任务
            check_1 = self.return_executionBuffer()

            if check_1 == -1:
                break
            elif check_1 == 1:
                self.waitBuffer[0][0].timeWait += time - self.waitBuffer[0][0].timeInto     #在任务池中的等待时间
                self.waitBuffer[0][0].timeInto = time                                       #进入执行缓冲区的时间
                self.executionBuffer.append(self.waitBuffer[0][0])
                del self.waitBuffer[0][0]

        #卸载执行任务池，串行模式将本地执行任务送入发送缓冲区
        while(1):
            #获取卸载发送缓冲区的状况，等于1则可以继续放入任务，等于-1则不能放入任务
            check_2 = self.return_transmitBuffer()

            if check_2 == -1:
                break
            elif check_2 == 1:
                self.waitBuffer[1][0].timeWait += time - self.waitBuffer[1][0].timeInto     #在任务池中的等待时间
                self.waitBuffer[1][0].timeInto = time                                       #进入发送缓冲区的时间
                self.executionBuffer.append(self.waitBuffer[1][0])
                del self.waitBuffer[1][0]



    ##################################################################################################################
    
    #本地执行函数，用于处理本地执行缓冲区的任务  每个时间片执行一次 处理执行缓冲区第一个任务
    def task_execution(self,Globalmap):
        #获取当前系统时钟
        time = Globalmap().get_value('clocktime')

        #判断当前CPU是否空闲，检查exeState变量
        if self.exeState == False:
            #检查当前执行缓冲区的第一个任务是否执行完
            if (time - self.executionBuffer[0].timeInto) < self.executionBuffer[0].timeLocal:
                #当前CPU中的任务还没有执行完
                print('WBAN'+str(self.number)+'正在执行任务')
                return 0                            
            elif (time - self.executionBuffer[0].timeInto) == self.executionBuffer[0].timeLocal:
                #当前CPU中的任务执行完毕，将该任务从执行缓冲区中取出，放入完成缓冲区，设置CPU空闲
                self.exeState = True
                self.finishBuffer.append(self.executionBuffer[0])
                del self.executionBuffer[0]
                return 0
        elif self.exeState == True:
            #当前CPU是空闲的，可以执行任务
            self.executionBuffer[0].timeWait += time - self.executionBuffer[0].timeInto         #该任务在执行缓冲区中等待的时间
            self.executionBuffer[0].timeInto = time                                             #开始执行该任务的起始时间
            self.executionBuffer[0].set_Local_Task()                                            #计算该任务的本地执行时延和本地执行能耗
            self.exeState = False

            return 0


    ##################################################################################################################


    #WBAN发送缓冲区的管理，判断当前信道是否可用，发送出的任务放入MEC的等待缓冲区，每个时间片执行一次 处理发送缓冲区第一个业务
    def task_transmit(self,Globalmap,distance):

        #获取当前系统时钟和距离
        time = Globalmap().get_value('clocktime')
        distance = Globalmap().get_value('distance')

        #检查当前信道是否空闲，检查tranState变量
        if self.tranState == False:
            #检查发送缓冲区第一个业务是否已经发送完
            if (time - self.transmitBuffer[0].timeInto) < self.transmitBuffer[0].timeTransmit:
                #当前CPU中的任务还没有发送完
                print('WBAN'+str(self.number)+'正在发送任务')
                return 0 
            elif (time - self.transmitBuffer[0].timeInto) == self.transmitBuffer[0].timeTransmit:
                #当前信道里的任务已经发送完了，将该任务从发送缓冲区中取出，并用return返回该任务，并存入MEC服务器的等待缓冲区
                self.tranState = True
                temp = self.transmitBuffer[0]
                del self.transmitBuffer[0]
                return temp
        elif self.tranState == True:
            #可以发送下一个业务
            self.transmitBuffer[0].timeWait += time - self.transmitBuffer[0].timeInto
            self.transmitBuffer[0].timeInto = time      #开始发送该任务的起始时间
            self.transmitBuffer[0].set_Transmit_Task(distance)      #计算传输时延和传输能耗
            self.tranState = False
            return 0


    ##################################################################################################################
     
    # 打印当前WBAN所有任务的属性值
    def print_TaskList(self):

        KEYS = ['数据量', '优先级', '价值', '本地频率', '本地时延', '本地能耗','云频率', '云时延', '云能耗', '带宽', 
                '发送时延', '发送能耗', '决策','报酬','网号','排队时延']
        VALUE = []
        for i in range(len(self.taskList)):
            value = self.taskList[i].__dict__.values()
            value = list(value)
            for i in range(0, 3):
                value.pop(16)
            value = [float(x) for x in value]
            VALUE.append(value)
        print()
        print("WBAN " + str(self.priority) + " 任务细节如下：")
        print(tabulate(VALUE, headers=KEYS, tablefmt='rst', disable_numparse=True))
        print()
        print()

    ##################################################################################################################
    
    #输出当前在发送缓冲区内的任务细节
    def printTransmitBuffer(self):

        KEYS = ['数据量', '优先级', '价值', '本地频率', '本地时延', '本地能耗','云频率', '云时延', '云能耗', '带宽', 
                '发送时延', '发送能耗', '决策','报酬','网号','排队时延']
        VALUE = []
        for i in range(len(self.transmitBuffer)):
            value = self.transmitBuffer[i].__dict__.values()
            value = list(value)
            for i in range(0, 3):
                value.pop(16)
            value = [float(x) for x in value]
            VALUE.append(value)
        print()
        print("WBAN " + str(self.priority) + " 发送缓冲区细节如下：")
        print(tabulate(VALUE, headers=KEYS, tablefmt='rst', disable_numparse=True))
        print()
        print()

    ##################################################################################################################
    
    #输出当前在执行缓冲区内的任务细节
    def printExecutionBuffer(self):

        KEYS = ['数据量', '优先级', '价值', '本地频率', '本地时延', '本地能耗','云频率', '云时延', '云能耗', '带宽', 
                '发送时延', '发送能耗', '决策','报酬','网号','排队时延']
        VALUE = []
        for i in range(len(self.executionBuffer)):
            value = self.executionBuffer[i].__dict__.values()
            value = list(value)
            for i in range(0, 3):
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
WBAN_A = WBAN(1,1, 1000, [], [], [], [], [], True,False)
WBAN_A.add_Task_List(1,gl)
WBAN_A.print_TaskList()
'''