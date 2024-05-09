from daily_rolling import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

file_path = 'Data\\xr_12_filtered.csv'
data = pd.read_csv(file_path)

r = Rolling()
r.SimDays = 3
r.Load = np.hstack((data['Day3'].values,data['Day4'].values,data['Day5'].values))
r.Pre = np.hstack((data['Day2'].values,data['Day3'].values,data['Day4'].values))
r.Alpha = 0.2
r.Pmax = 4400.0 
r.BatMaxPow = 900.0
r.BatMaxSto = 1800.0 
r.BatCurSto = 900.0
r.BatMinSto = 0.05 * r.BatMaxSto

r.main()

print('Maximum:',r.MonthMax)
plt.subplot(2,1,1)
plt.plot(r.Pre, '--')
plt.plot(r.Pmax_)
plt.plot(r.Load)
plt.plot(r.BatPow)
plt.plot(r.Output)

plt.subplot(2,1,2)
plt.plot(r.BatSto)
plt.show()

