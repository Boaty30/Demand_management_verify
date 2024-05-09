from daily_rolling import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

file_path = 'Data\\xr_12_filtered.csv'
data = pd.read_csv(file_path)

r = Rolling()
r.SimDays = 30
r.Load = np.hstack([data[f'Day{i}'].values for i in range(2, 32)])
r.Pre = np.hstack([data[f'Day{i}'].values for i in range(1, 31)])
r.Alpha = 0.1
r.Pmax = 4400.0 
r.BatMaxPow = 900.0
r.BatMaxSto = 1800.0 
r.BatCurSto = 900.0
r.BatMinSto = 0.05 * r.BatMaxSto

r.main()

print('Maximum:',r.MonthMax)

font_path = 'C:/Windows/Fonts/msyh.ttc'  # 微软雅黑字体路径，根据实际情况修改
plt.rcParams['font.family'] = ['sans-serif']
plt.rcParams['font.sans-serif'] = [FontProperties(fname=font_path).get_name()]
plt.rcParams['axes.unicode_minus'] = False  # 解决负号'-'显示为方块的问题

plt.subplot(2,1,1)
plt.plot(r.Pre, '--')
plt.plot(r.Pmax_)
plt.plot(r.Load)
plt.plot(r.BatPow)
plt.plot(r.Output)
plt.legend(['预测值（基于前一天）','动态阈值','负荷','电池功率','电网侧实际负荷'])

plt.subplot(2,1,2)
plt.plot(r.BatSto)
plt.legend(['电池容量'])

plt.suptitle('电池容量和功率曲线(2023.12.2-2023.12.31)')
plt.show()