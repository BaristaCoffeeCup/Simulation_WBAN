from scipy.stats import binom
from tabulate import tabulate
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import math

from WBAN_Create import WBAN
from task_Create import Task
from MECserver_create import MEC
from config import Globalmap

#本函数给出一系列进行卸载决策和资源分配计算的算法函数

#对于当前时间点生成的一批任务，假设已经确认了卸载决策和资源分配，计算处理这批任务的系统收益
def profitOfSystem(WBANList,MEC,Globalmap):

    #算法运行的系统时钟与实际运行的时钟是不一样的，在算法中改变了真实的时钟，在算法运行结束后需要回复时钟
    timeReal = Globalmap().get_value('clocktime')
    Globalmap().set_value('timeReal',timeReal)
    #获取当前时刻完成列表和失效列表的长度
    #无论当前这批任务能否完成，某时刻两个列表的长度-原本长度 = 生成的任务数，则表示任务处理完成
    finishBuffer = Globalmap().get_value('finishBuffer')
    len_finish = len(finishBuffer)
    unavailableBuffer = Globalmap().get_value('unavailableBuffer')
    len_unavailable = len(unavailableBuffer)

    #获取当前所有WBAN生成的任务
    numOfTask = 0
    for i in range(len(WBANList)):
        numOfTask += len(WBANList[i].taskList)

    #在调用本函数时，WBAN已经生成了业务，即taskList中已经出现的任务
    while(1):
        #需要处理传入该函数中的所有WBAN
        for i in range(len(WBANList)):
            #将taskList中的任务分配到本地执行缓冲区中或者发送缓冲区中
            WBAN.buffer_Allocation(Globalmap)
            #WBAN本地执行任务
            WBAN.task_execution(Globalmap)
            #WBAN发送任务
            WBAN.task_transmit(Globalmap)
        
        #MEC服务器接收从所有WBAN中传来的任务
        MEC.receive_Task(WBANList,Globalmap)
        #MEC服务器对接收到的任务进行分配
        MEC.buffer_Allocation(Globalmap)
        #MEC服务器处理缓冲队列中的任务
        MEC.MEC_TaskExecution(Globalmap)

        buffer_1 = Globalmap().get_value('finishBuffer')
        buffer_2 = Globalmap().get_value('unavailableBuffer')
        if (len(buffer_1)+len(buffer_2)) - (len_finish+len_unavailable) == numOfTask:
            Globalmap().set_value('clocktime',timeReal)
            break
        else:
            time = Globalmap().get_value('clocktime')
            time += 1
            Globalmap().set_value('clocktime',time)

    Profit_WBAN = [ 0 for i in range(len(WBANList)) ]
    Profit_MEC = 0

    #当前这批业务处理完之后，计算每个WBAN的收益和服务器的收益
    for i in range(len(finishBuffer)):
        for j in range(len(WBANList)):
            #计算时延因子和能耗因子
            alpha = WBANList[j].energy / (1000 - WBANList[j])   #时延因子
            Beta = 1- alpha                                     #能耗因子
            #如果完成列表中遍历的任务属于某个WBAN且所属时间片等于算法运行时的时间
            if finishBuffer[i].timeslice == timeReal and finishBuffer[i].numOfWBAN == WBANList[j].number:
                #如果该任务是在本地执行的
                if finishBUffer[i].ifOffload == 0:
                    Profit_WBAN[j] += finishBuffer[i].value - alpha*finishBuffer[i].timeLocal - Beta*finishBuffer[i].energyLocal
                #如果该任务卸载执行
                elif finishBuffer[i].ifOffload == 1:
                    Profit_WBAN[j] += finishBuffer[i].value - alpha*finishBuffer[i].timeTransmit - Beta*finishBuffer[i].energyTransmit - finishBuffer[i].payForMEC
                    Profit_MEC += finishBuffer[i].payForMEC - alpha*finishBuffer[i].timeMEC - Beta*finishBuffer[i].energyMEC

    #计算用户收益的平均值
    for i in range(len(Profit_WBAN)):
        temp += Profit_WBAN[i]
    temp = temp/len(Profit_WBAN)

    #函数返回用户平均收益和服务器收益
    return [temp,Profit_MEC]


    
    





