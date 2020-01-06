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
'''

a = [ []for i in range(2) ]
a[0] = [1,2,3]
del a[0][0]
print(a)

