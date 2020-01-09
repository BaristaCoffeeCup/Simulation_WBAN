from scipy.stats import binom
from tabulate import tabulate
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import math

# 设置属性防止中文乱码
mpl.rcParams['font.sans-serif'] = [u'SimHei']
mpl.rcParams['axes.unicode_minus'] = False
tabulate.PRESERVE_WHITESPACE = True

from config import Globalmap

'''x1 = np.random.poisson(lam=200,size=1)

for i in range(len(x1)):
    x = x1[i]


print("x的值为：")
print(x)
'''


class Task(object):
    # 任务类，用于生成WBAN在某一时隙开始时产生的八个任务
    def __init__(self, dataSize, priority, value, frequencyLocal, timeLocal, energyLocal, frequencyMEC, timeMEC, energyMEC,
                 bandwidth,timeTransmit, energyTransmit, ifOffload, payForMEC, numOfWBAN, timeWait, timeInto, timeOut, timeslice):

        self.dataSize = dataSize                                       # 任务的数据量
        self.priority = priority                                       # 任务的优先级
        self.value = value                                             # 任务的价值

        self.frequencyLocal = frequencyLocal                           # 算法分配给该任务的本地CPU计算频率
        self.timeLocal = timeLocal                                     # 该任务在本地执行所需要的时间
        self.energyLocal = energyLocal                                 # 该任务在本地执行所需要的能耗

        self.frequencyMEC = frequencyMEC                               # 算法分配给该任务的服务器CPU计算频率
        self.timeMEC = timeMEC                                         # 该任务在服务器执行所需要的时间
        self.energyMEC = energyMEC                                     # 该任务在服务器执行所需要的能耗

        self.bandwidth = bandwidth                                     #算法分配给该任务的信道带宽
        self.timeTransmit = timeTransmit                               # 该任务由WBAN中心节点发送至服务器需要的时间
        self.energyTransmit = energyTransmit                           # 该任务由WBAN中心节点发送至服务器需要的能耗

        self.ifOffload = ifOffload                                     # 该任务是卸载处理还是在本地处理，0：本地处理   1：卸载处理
        self.payForMEC = payForMEC                                     # 该任务若卸载处理，需要向边缘服务器所支付的报酬
        self.numOfWBAN = numOfWBAN                                     # 任务隶属的WBAN号

        self.timeWait = timeWait                                       # 任务在执行缓冲区/发送缓冲区/信道中的等待时间
        self.timeInto = timeInto                                       # 任务进入缓冲区的时钟时间
        self.timeOut = timeOut                                         # 任务出缓冲区的时间

        self.timeslice = timeslice                                     # 任务隶属的时间批次

        self.available = True                                          #该任务是否在额定时延内执行完成 

    ##################################################################################################################
    
    # 设置任务的时间批次
    def set_timeslice_Task(self, timeslice):
        self.timeslice = timeslice

    # 设置任务的数据量
    def set_dataSize_Task(self, dataSize):
        self.dataSize = dataSize

    # 设置任务的优先级
    def set_priority_Task(self, priority):
        self.priority = priority

    # 设置任务的价值
    def set_value_Task(self, value):
        self.value = value

    # 设置任务的本地频率 本地处理的能耗和时延
    def set_Local_Task(self):
        frequencyLocal = self.frequencyLocal
        # 本地处理时间 = 数据量（bit）* 5900 (处理1bit数据所需要的CPU周期) / 本地COPU分配频率
        self.timeLocal = self.dataSize * 5900 / frequencyLocal
        # 本地处理能耗 = 10^-24 * 本地COPU分配频率^2
        self.energyLocal = pow(10, -24) * pow(frequencyLocal, 2)

    # 设置任务的服务器频率 卸载处理的能耗和时延
    def set_MEC_Task(self):
        frequencyMEC = self.frequencyMEC
        self.timeMEC = self.dataSize * 5900 / frequencyMEC
        self.energyMEC = pow(10, -24) * pow(frequencyMEC, 2)

    # 设置任务发射的时间和能耗
    def set_Transmit_Task(self,distance):
        bandwidth = self.bandwidth
        #计算信道
        noisePower = 10^(-13)       #噪声功率
        transmitPower = 0.6         #发送功率
        channelCap = bandwidth * math.log2(1+(transmitPower * distance^(-4)) / (noisePower))    #信道带宽
        self.timeTransmit = self.dataSize / channelCap  
        self.energyTransmit = timeTransmit * 0.6  # 默认WBAN中心节点的发射功率为0.6W

    # 设置任务时卸载处理还是本地处理
    def set_ifOffload_Task(self, ifOffload):
        self.ifOffload = ifOffload

    # 设置任务在执行缓冲区/发送缓冲区中的等待时间
    def set_timeWait_Task(self, timeWait):
        self.timeWait = timeWait

    # 设置任务进入缓冲区的时间
    def set_timeInto_Task(self, timeInto):
        self.timeInto = timeInto

    # 设置任务离开缓冲区的时间
    def set_timeOut_Task(self, timeOut):
        self.timeOut = timeOut

    #设置任务属于的WBAN的编号
    def set_numWBAN_Task(self,numOfWBAN):
        self.numOfWBAN = numOfWBAN

    #判断当前任务有没有过期
    def check_available_Task(self):
        
        #设置每个优先级的额定处理时延
        maxDelay = [40000,35000,30000,25000,20000,15000,10000,5000]
        #根据当前任务的优先级判断任务是否失效
        index = self.priority
        if self.timeWait < maxDelay[index]:
            self.available = False
            return False
        elif self.timeWait >= maxDelay[index]:
            return True


        


'''
#测试代码
task = Task(0,0,0,0,0,0,0,0,0,0,0,0)
Dict = task.__dict__
KEY = list(Dict.keys())
VALUE = list(Dict.values())
VALUE = [float(x) for x in VALUE]
showdata = []
showdata.append(VALUE)
print(KEY)
print(VALUE)
print(tabulate(showdata,headers=KEY,tablefmt='pipe',disable_numparse=True))
'''
