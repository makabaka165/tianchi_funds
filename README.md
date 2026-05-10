# Tianchi Funds Baseline

余额宝申购赎回预测的第一版可复现实验流程。

## 环境

推荐使用 Miniforge/conda：

```bash
conda env create -f environment.yml
conda activate funds-ml
```

如果已经创建过环境，可以直接激活：

```bash
conda activate funds-ml
```

## 数据

原始数据放在本地目录：

```text
Purchase Redemption Data/
```

该目录包含比赛原始 CSV，体积较大，已在 `.gitignore` 中忽略。

## 第一版基线

运行：

```bash
python src/baseline_weekday_mean.py
```

如果当前终端没有激活 conda，也可以直接运行：

```bash
conda run -n funds-ml python src/baseline_weekday_mean.py
```

脚本会：

- 分块读取 `user_balance_table.csv`
- 聚合每日申购、赎回及辅助统计
- 用 2014 年 8 月作为验证集
- 用历史同星期均值作为第一版基线
- 预测 2014 年 9 月 30 天结果
- 输出提交文件到 `output/tc_comp_predict_table.csv`

## 当前方法

第一版基线使用按星期分组的历史均值，并结合最近 14 天、30 天均值做兜底。它的目的不是追求最优分数，而是先把数据读取、验证、预测、提交格式跑通。

## 本地评价

运行：

```bash
conda run -n funds-ml python src/evaluate.py
```

评价脚本会检查 `output/tc_comp_predict_table.csv` 的提交格式，并使用 2014 年 8 月验证集计算近似官方指标。输出报告保存到：

```text
output/evaluation_report.json
```

当前门限定义在 `src/evaluate.py` 的 `GateThresholds` 中。只有通过门限的版本才建议作为官网提交候选。

当前第二版校准基线的本地评价：

```text
Purchase relative error mean: 0.135789
Redeem relative error mean:   0.159858
Weighted relative error mean: 0.149027
Decision: PASS
```

## 滚动验证

为了避免只适配 2014 年 8 月，可以运行 2014 年 5-8 月滚动验证：

```bash
conda run -n funds-ml python src/rolling_validate.py
```

输出：

```text
output/rolling_validation_2014_05_08.csv
output/rolling_validation_summary.json
```

当前滚动验证显示第二版在 8 月通过候选门限，但 6 月赎回误差偏高，说明还需要继续提升跨月稳定性。
