import pandas as pd

# 加载CSV文件
df = pd.read_csv('C:\\Codes\\Projects\\Demand_management_verify\\Data\\xr_12_combined.csv', index_col=0)
df.index = pd.to_datetime(df.index)

# 筛选分钟为0, 15, 30, 45的行
filtered_df = df[df.index.minute.isin([0, 15, 30, 45])]

# 输出结果查看
print(filtered_df)

# 如果需要，可以将筛选后的数据保存到新的CSV文件
filtered_df.to_csv('xr_12_filtered.csv')
