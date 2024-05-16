import daily_pred as dpred

class Rolling:

    def __init__(self):
        self.SimDays = 0.0
        self.Load = []
        self.Pre = []
        self.Alpha = 1.0
        self.Pmax = 0.0

        self.BatMaxPow = 0.0  # Battery Max Power
        self.BatMaxSto = 0.0  # Battery Max Storage
        self.BatCurPow = 0.0  # Battery Current Power
        self.BatCurSto = 0.0

        self.MonthMax = 0.0
        self.BatMinSto = 0.05 * self.BatMaxSto
        self.BatPow = []
        self.BatSto = []
        self.Output = []
        self.Pmax_ = []

    def main(self):
        for i in range(96 * self.SimDays):

            self.Pmax = dpred.calculate_threshold(self.Pre)
            LoadReal = self.Load[i]
            Error = LoadReal - self.Pre[i]
            PMaxNew = (1 + (self.Alpha * Error) / LoadReal) * self.Pmax 

            Threshold = PMaxNew * int(PMaxNew >= self.MonthMax) + self.MonthMax * int(PMaxNew < self.MonthMax)
            Delta = LoadReal - Threshold
            Output = LoadReal - self.battery(Delta)
            self.MonthMax = self.MonthMax * int(Output <= self.MonthMax) + Output * int(Output > self.MonthMax)
            self.Output.append(Output)
            self.Pmax_.append(PMaxNew)

    def battery(self, demand):
        if demand == 0:
            return 0

        S = demand / 0.95 * (demand > 0) + demand * 0.95 * (demand < 0)    # 储能的线性模型 0.95的充/放电效率
        S = (int(demand > 0) + int(demand < 0) * (-1.0)) * (      # 最大功率越限判断
                    (abs(S) <= self.BatMaxPow) * abs(S) + (abs(S) > self.BatMaxPow) * self.BatMaxPow)
        if demand > 0:  # 放电 电池储量越限判断
            if self.BatCurSto <= self.BatMinSto:
                S = 0
            elif self.BatCurSto - S * 0.25 < self.BatMinSto:
                S = (self.BatCurSto - self.BatMinSto) * 4
        if demand < 0:  # 充电 电池储量越限判断
            if self.BatCurSto >= self.BatMaxSto:
                S = 0
            elif self.BatCurSto - S * 0.25 > self.BatMaxSto:
                S = (self.BatCurSto - self.BatMaxSto) * 4
        self.BatCurSto = self.BatCurSto - S * 0.25
        out = S * 0.95 * (S > 0) + S / 0.95 * (S < 0)  # 输出侧
        self.BatPow.append(S)
        self.BatSto.append(self.BatCurSto)
        return out
