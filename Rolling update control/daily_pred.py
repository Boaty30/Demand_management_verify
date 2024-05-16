import daily_opt as dopt
import pandas as pd
import time

start_time = time.time()

p_l = dopt.load_data("C:\\Codes\\Projects\\Demand_management_verify\\Data\\xr_12_filtered.csv")

def calculate_threshold(p_l):
    low = min(p_l)
    high = max(p_l)
    print("Lowest power demand:", low)
    print("Highest power demand:", high)
    tolerance = 0.1  # 阈值调整的精度
    best_threshold = None
    best_cost = float('inf')

    while high - low > tolerance:
        current_threshold = (high + low) / 2
        has_solution, cost, solution = dopt.solve_problem("C:\\Codes\\Projects\\Demand_management_verify\\Data\\xr_12_filtered.csv", 
                                           s_n=1800, alpha=0.85, 
                                           delta_t=0.25, 
                                           output_file="C:\\Codes\\Projects\\Demand_management_verify\\Data\\daily_pred.csv",
                                           p_f_max=current_threshold)

        if has_solution:
            if cost < best_cost:
                best_cost = cost
                best_threshold = current_threshold
                high = current_threshold  # 成本更低，试图通过降低上限来找到更优阈值
            else:
                low = current_threshold  # 当前成本不佳，提高下限
        else:
            # 如果没有解，意味着当前阈值过低或其他原因导致无法满足条件
            # 提高下限试图找到可行解
            low = current_threshold

    return best_threshold if best_threshold is not None else 'No feasible solution found within the given range'

def grid_cost(p_l, is_valley):
    cost = 0
    m_valley = 0.389  # m值在谷时段
    m_non_valley = 0.656  # m值在非谷时段
    for p in p_l:
        if is_valley:
            cost += m_valley * p * 0.25
        else:
            cost += m_non_valley * p * 0.25
    return cost

# 使用历史负载数据调用此函数
num_periods = len(p_l)
threshold = calculate_threshold(p_l)
print("Optimal threshold for the day:", threshold)
has_solution, cost, solution = dopt.solve_problem(file_path="C:\\Codes\\Projects\\Demand_management_verify\\Data\\xr_12_filtered.csv", 
                                    s_n=1800, alpha=0.85, 
                                    delta_t=0.25, 
                                    output_file="C:\\Codes\\Projects\\Demand_management_verify\\Data\\daily_pred.csv",
                                    p_f_max=threshold,
                                    figpath="C:\\Codes\\Projects\\Demand_management_verify\\Data\\daily_pred_curve.png")
print("Cost:", cost)

is_valley = [True if (i>=36 and i<=48) or (i>=68 and i<=76) or (i>=80 and i<=88) else False for i in range(num_periods)]
print("Original cost:", grid_cost(p_l, is_valley))
print("Now cost:", grid_cost(p_l+solution['P_CS'], is_valley))

stop_time = time.time()
print("Time elapsed:", stop_time - start_time)