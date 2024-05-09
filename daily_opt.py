import cplex
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from matplotlib.font_manager import FontProperties

def generate_time_labels(num_periods, interval_minutes=15):
    base_time = datetime(2023, 12, 1)  # 可以是任意日期，只要时间是从0:00开始即可
    time_labels = [base_time + timedelta(minutes=i * interval_minutes) for i in range(num_periods)]
    return time_labels

def load_data(file_path):
    # 从CSV文件加载数据
    data = pd.read_csv(file_path)
    return data['Day5'].values

def create_problem():
    # 初始化一个CPLEX问题实例
    prob = cplex.Cplex()
    prob.objective.set_sense(prob.objective.sense.maximize)
    return prob


def add_variables(prob, num_periods, p_max, s_n):
    # 添加充放电功率变量和电池存储状态变量
    for t in range(num_periods):
        prob.variables.add(names=[f"P_CS_{t}"], lb=[-p_max], ub=[p_max])
    prob.variables.add(names=[f"S_{t}" for t in range(num_periods)],
                    lb=[0.05 * s_n] * num_periods,
                    ub=[s_n] * num_periods)
    # 添加二元控制变量
    prob.variables.add(names=[f"charge_{t}" for t in range(num_periods)], types=["B"]*num_periods)
    prob.variables.add(names=[f"discharge_{t}" for t in range(num_periods)], types=["B"]*num_periods)

def add_constraints(prob, num_periods, p_f_max, p_l, s_n, alpha, delta_t):
    M = 10000  # 大M方法中使用的一个大常数
    for t in range(num_periods):
        # 存储状态动态更新
        if t > 0:
            prob.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=[f"S_{t-1}", f"S_{t}", f"P_CS_{t-1}"],
                                           val=[1, -1, alpha * delta_t])],
                senses=["E"],
                rhs=[0],
                names=[f"storage_update_{t}"]
            )

        # 低于控制线时，禁止放电
        if p_l[t] < p_f_max:
            prob.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=[f"P_CS_{t}"], val=[1.0])],
                senses=["G"],
                rhs=[0],
                names=[f"no_discharge_{t}"]
            )
        
        # 高于控制线时，禁止充电
        if p_l[t] > p_f_max:
            prob.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=[f"P_CS_{t}"], val=[1.0])],
                senses=["L"],
                rhs=[0],
                names=[f"no_charge_{t}"]
            )
    # 添加 S_0 的初始存储状态约束
    prob.linear_constraints.add(
        lin_expr=[cplex.SparsePair(ind=["S_0"], val=[1.0])],
        senses=["E"],
        rhs=[0.5 * s_n],
        names=["initial_storage_condition"]
    )
    # 添加功率约束和存储状态动态更新约束
    for t in range(num_periods):
        if t > 0:
            # 存储状态动态更新
            prob.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=[f"S_{t-1}", f"S_{t}", f"P_CS_{t-1}"],
                                           val=[1.0, -1.0, alpha * delta_t])],
                senses=["E"],
                rhs=[0],
                names=[f"storage_update_{t}"]
            )
        # 功率约束
        prob.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=[f"P_CS_{t}"], val=[1.0])],
            senses=["L"],
            rhs=[p_f_max - p_l[t]],
            names=[f"power_limit_{t}"]
        )


def set_objective(prob, num_periods, h, w, is_valley):
    # 设置目标函数
    objective = []
    m_valley = 0.389  # m值在谷时段
    m_non_valley = 0.656  # m值在非谷时段

    for t in range(num_periods):
        p_cs_name = f"P_CS_{t}"
        s_name = f"S_{t}"
        if is_valley[t]:
            # 谷时段目标函数
            objective.append((p_cs_name, -h * m_valley))
            objective.append((s_name, w))  # w乘以S_t，直接添加到目标函数中
        else:
            # 非谷时段目标函数
            objective.append((p_cs_name, -h * m_non_valley))

    prob.objective.set_linear(objective)



def solve_problem(file_path, s_n, alpha, delta_t, output_file, p_f_max=4750, figpath="C:\\Codes\\Projects\\Demand_management_verify\\Data\\\power_and_storage_profiles.png"):
    try:
        # 载入负荷功率数据并设置问题参数
        p_l = load_data(file_path)
        num_periods = len(p_l)
        print(f"Number of periods = {num_periods}")
        p_max = 900
        h = 0.25
        w = 1
        is_valley = [True if (i>=36 and i<=48) or (i>=68 and i<=76) or (i>=80 and i<=88) else False for i in range(num_periods)]

        # 创建并设置问题
        prob = create_problem()
        add_variables(prob, num_periods, p_max, s_n)
        add_constraints(prob, num_periods, p_f_max, p_l, s_n, alpha, delta_t)
        set_objective(prob, num_periods, h, w, is_valley)

        # 解决问题
        prob.solve()

        # # 输出结果
        # print("Solution status = ", prob.solution.get_status(), ":", prob.solution.status[prob.solution.get_status()])
        # print("Solution value  = ", prob.solution.get_objective_value())
        # for t in range(num_periods):
        #     print(f"P_CS_{t} = {prob.solution.get_values(f'P_CS_{t}'): .2f}")
        #     print(f"S_{t} = {prob.solution.get_values(f'S_{t}'): .2f}")

        # 创建一个空的 DataFrame 来存储结果
        solution_df = pd.DataFrame(columns=['P_CS', 'S'])
        for t in range(num_periods):
            p_cs = prob.solution.get_values(f'P_CS_{t}')
            s = prob.solution.get_values(f'S_{t}')
            solution_df.loc[t] = [p_cs, s]

        # 将结果保存到 CSV 文件中
        solution_df.to_csv(output_file, index=False)

        # time_labels = generate_time_labels(num_periods)
        # # 指定字体路径
        # font_path = 'C:/Windows/Fonts/msyh.ttc'  # 微软雅黑字体路径，根据实际情况修改
        # plt.rcParams['font.family'] = ['sans-serif']
        # plt.rcParams['font.sans-serif'] = [FontProperties(fname=font_path).get_name()]
        # plt.rcParams['axes.unicode_minus'] = False  # 解决负号'-'显示为方块的问题

        # fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 6))

        # # 第一个子图：功率曲线
        # ax1.plot(time_labels, p_l, label='电网侧优化前功率')
        # ax1.plot(time_labels, solution_df['P_CS'], label='储能运行功率')
        # ax1.plot(time_labels, solution_df['P_CS'] + p_l, label='电网侧实际功率')
        # ax1.axhline(y=p_f_max, color='r', linestyle='--', label=f'需量控制阈值={p_f_max:.2f} kW', lw=0.7, alpha=0.7)
        # ax1.fill_between(time_labels, p_l, solution_df['P_CS'] + p_l, where=(p_l >= solution_df['P_CS'] + p_l), facecolor='red', alpha=0.3, label='削峰')
        # ax1.fill_between(time_labels, p_l, solution_df['P_CS'] + p_l, where=(p_l <= solution_df['P_CS'] + p_l), facecolor='green', alpha=0.3, label='填谷')
        # ax1.xaxis.set_major_locator(mdates.HourLocator(interval=1))  # 每1小时标记一次
        # ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))  # 格式化时间标签为小时:分钟
        # ax1.set_xlabel('时刻')
        # ax1.set_ylabel('功率 (kW)')
        # ax1.set_title('功率曲线')
        # ax1.legend()
        # ax1.grid(True)
        # ax1.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        # ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        # ax1.tick_params(axis='x', rotation=45)  # 设置横坐标标签旋转45度

        # # 第二个子图：储能电量曲线
        # ax2.plot(time_labels, solution_df['S'], label='储能电量')
        # ax2.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        # ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        # ax2.set_xlabel('时刻')
        # ax2.set_ylabel('储能电量 (kWh)')
        # ax2.set_title('储能电量曲线')
        # ax2.legend()
        # ax2.grid(True)
        # ax2.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        # ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        # ax2.tick_params(axis='x', rotation=45)  # 设置横坐标标签旋转45度

        # # 调整子图间距和显示格式
        # plt.tight_layout()
        # plt.xticks(rotation=45)  # 如果时间标签重叠，可以旋转标签
        # # plt.show()
        # plt.savefig(figpath)

        return prob.solution.get_status(),prob.solution.get_objective_value(), solution_df
    except cplex.exceptions.CplexError as exc:
        print(exc)
        return None, None, None

if __name__ == "__main__":
    status, cost, solution = solve_problem("C:\\Codes\\Projects\\Demand_management_verify\\Data\\xr_12_filtered.csv", s_n=1800, alpha=0.85, delta_t=0.25, output_file="C:\\Codes\\Projects\\Demand_management_verify\\Data\\daily_opt.csv")
    print("Cost:", cost)
    print("Status:", status)