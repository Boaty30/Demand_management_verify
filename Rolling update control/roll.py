from daily_rolling import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

file_path = 'Data\\xr_12_filtered.csv'
data = pd.read_csv(file_path)
data_1130 = pd.read_csv('C:\\Codes\\Projects\\Demand_management_verify\\Rolling update control\\Data\\xr_11_30_filtered.csv')

r = Rolling()
r.SimDays = 5
r.Load = np.hstack([data[f'Day{i}'].values for i in range(1, 6)])
pre_1 = [data_1130['Power'].values]
pre_2 = [data[f'Day{i}'].values for i in range(1, 5)]
r.Pre = np.hstack(pre_1+pre_2)
r.Alpha = 0.3
# r.Pmax = 4000.0 
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
# plt.plot(r.Pre, '--')
plt.plot(r.Pmax_, color='orange')
plt.plot(r.Load, color='green')
plt.plot(r.BatPow, color='blue')
plt.plot(r.Output)
plt.axhline(y=r.MonthMax, color='red', linestyle='--')
plt.legend(['功率阈值','负荷','电池功率','电网侧实际负荷','最大功率'])

plt.subplot(2,1,2)
plt.plot(r.BatSto)
plt.axhline(y=r.BatMinSto, color='red', linestyle='--')
plt.legend(['电池容量','最小容量'])

plt.suptitle('电池容量和功率曲线(2023.12.1-2023.12.31)')
plt.show()