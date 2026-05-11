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

## 论坛经验 ML 对照

`论坛经验/` 中的材料主要来自 Datawhale 金融风控贷款违约分类赛，不是余额宝申购赎回时间序列赛，因此没有直接替换当前方案。已新增一个独立对照脚本：

```bash
conda run -n funds-ml python src/forum_ml_ensemble.py
```

脚本借鉴论坛资料中的特征工程、LightGBM/XGBoost/Ridge、加权融合和防过拟合验证思路，生成 ML 单模型、ML 加权融合、规则模型与 ML 的保守融合报告：

```text
output/forum_ml_model_report.json
output/forum_ml_summary.json
output/forum_blend_summary.json
output/forum_blend_weight_scan.csv
```

本次对照结论：纯 ML 加权融合 overall proxy 为 4.244502，8 月门禁 FAIL；规则/ML 50/50 融合 overall proxy 为 5.191191，8 月 PASS 但低于当前规则基线；权重扫描中最好的 95% 规则 + 5% ML overall proxy 为 6.037310，也低于当前正式候选 6.075524。因此暂不替换 `output/tc_comp_predict_table.csv`，继续保留第三十五版规则模型作为官网提交文件。
