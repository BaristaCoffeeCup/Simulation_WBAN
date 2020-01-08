from scipy.stats import binom
from tabulate import tabulate
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import math
import operator

#全局变量类，在该类对象中放置全局变量
class Globalmap(object):

    def _init_(self):
        self._global_dict = {'clocktime':0,'distance':100,'finishBuffer':[]}


    def set_value(self,name,value):
        self._global_dict[name] = value


    def get_value(self,name):
        return self._global_dict[name]
