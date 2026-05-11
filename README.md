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

当前第三十五版连续规则优化基线的本地评价：

```text
Purchase relative error mean: 0.108418
Redeem relative error mean:   0.127333
Weighted relative error mean: 0.118821
Weighted proxy score mean:    6.478250
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

当前第三十五版滚动验证整体 `weighted_proxy_score` 为 6.075524，高于第三十四版 5.948866；8 月候选门禁继续通过。该版本连续保留多条小规则，整体分数首次稳定超过 6，但仍以本地代理评价为准，官网提交前需要注意固定日号规则的过拟合风险。

## 候选搜索

为了减少手工试错，可以先运行只读候选搜索：

```bash
conda run -n funds-ml python src/search_candidates.py --top 20
```

脚本会基于当前滚动验证明细扫描单日、星期、日区间和轻量参数候选，输出：

```text
output/candidate_search_report.csv
output/candidate_search_report.json
```

默认只保存排序前 200 条候选；如需完整结果，可添加 `--save-limit 0`。搜索结果只用于排队，最终仍需把候选实装后重新运行基线、8 月评价和滚动验证三脚本。

## LSTM Challenger

参考 `论坛经验/思路1.md`，仓库中新增了一个独立的 LSTM challenger，用来和当前规则模型做并行对照，而不是直接替换正式候选：

```bash
conda env create -f environment-lstm.yml
conda run -n funds-ml-lstm python src/lstm_challenger.py
```

该脚本采用纯序列多步预测方案：

- 复用现有日级聚合后的 `purchase` / `redeem`
- 对目标做 `log1p` 和 EMA 平滑
- 使用 direct multi-output LSTM 一次预测未来 31 天
- 固定实验队列：`pure_base`、`pure_lb30`、`pure_lb60`、`pure_ema5`
- 自动扫描轻量融合：`rule 95%/90%/85%/80% + LSTM`

主要输出：

```text
output/lstm_validation_2014_05_08.csv
output/lstm_validation_august_2014.csv
output/lstm_experiment_summary.csv
output/lstm_experiment_summary.json
output/lstm_best_experiment.json
output/lstm_best_pure_tc_comp_predict_table.csv
output/lstm_best_blend_tc_comp_predict_table.csv
```

当前实验结论：

```text
Best pure:  pure_base
overall proxy_score: 3.459591
8 月 proxy_score:    3.690146
Decision: FAIL

Best blend: blend_rule95_lstm05
overall proxy_score: 5.973985
8 月 proxy_score:    6.408349
Decision: PASS
```

由于最优融合版本的 rolling overall proxy 仍低于当前规则基线 `6.075524`，且 rolling `bad_day_rate_max` 为 `0.211382`，超过当前基线 `0.203252`，因此本轮 LSTM challenger 不提升为正式提交文件。当前正式候选仍然是规则模型生成的 `output/tc_comp_predict_table.csv`。
