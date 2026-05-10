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
