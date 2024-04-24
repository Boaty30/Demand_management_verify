import cplex
from cplex.exceptions import CplexError

def create_problem():
    # 创建一个新的线性问题
    prob = cplex.Cplex()
    # 设置问题为最大化
    prob.objective.set_sense(prob.objective.sense.maximize)
    return prob

def add_variables(prob, num_periods, num_chargers, p_max, s_n):
    # 添加决策变量P_{CS,i,t}
    for t in range(num_periods):
        for i in range(num_chargers):
            var_name = f"P_CS_{i}_{t}"
            prob.variables.add(names=[var_name], lb=[-p_max], ub=[p_max])

    # 添加电池状态变量S_{i,t}
    for t in range(num_periods):
        for i in range(num_chargers):
            var_name = f"S_{i}_{t}"
            prob.variables.add(names=[var_name], lb=[0.05 * s_n], ub=[s_n])

def add_constraints(prob, num_periods, num_chargers, p_max):
    # 添加功率约束
    for t in range(num_periods):
        constraint = []
        for i in range(num_chargers):
            constraint.append((f"P_CS_{i}_{t}", 1.0))
        prob.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=[var[0] for var in constraint], val=[var[1] for var in constraint])],
            senses=["L"],
            rhs=[p_max],
            names=[f"power_limit_{t}"]
        )

def set_objective(prob, num_periods, num_chargers, h, w, is_valley):
    # 设置目标函数
    objective = []
    for t in range(num_periods):
        for i in range(num_chargers):
            if is_valley[t]:
                # 谷时段目标函数部分
                objective.append((f"P_CS_{i}_{t}", -h))
                objective.append((f"S_{i}_{t}", w))
            else:
                # 非谷时段目标函数部分
                objective.append((f"P_CS_{i}_{t}", -h))
    prob.objective.set_linear(objective)

def solve_problem():
    num_periods = 24  # 假设有24个时段
    num_chargers = 5  # 假设有5个充电器
    p_max = 100  # 最大功率
    s_n = 200  # 存储容量
    h = 1  # 功率单位时间成本
    w = 1.5  # 谷时段奖励系数
    is_valley = [True if i < 12 else False for i in range(num_periods)]  # 假设前12个时段为谷时段

    prob = create_problem()
    add_variables(prob, num_periods, num_chargers, p_max, s_n)
    add_constraints(prob, num_periods, num_chargers, p_max)
    set_objective(prob, num_periods, num_chargers, h, w, is_valley)
    prob.solve()

    # 输出结果
    print("Solution status = ", prob.solution.get_status(), ":", prob.solution.status[prob.solution.get_status()])
    print("Solution value  = ", prob.solution.get_objective_value())
    for v in prob.variables.get_names():
        print(v, prob.solution.get_values(v))

if __name__ == "__main__":
    solve_problem()
