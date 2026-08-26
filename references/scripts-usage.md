# 内置脚本运行手册（scripts-usage）

> 根 `SKILL.md` 只列脚本用途，本文件给**完整运行示例、参数与常见坑**，按需加载。
> 所有脚本：纯 Python 标准库、零第三方依赖、不联网、不修改被检查的文件。

## 1. profile_dataset.py — 数据画像

拿到新数据的第一个动作：类型推断、缺失率、基数、分布、异常值、伪装缺失、候选主键。

```bash
# 默认 CSV
python3 scripts/profile_dataset.py data.csv

# TSV（指定分隔符）
python3 scripts/profile_dataset.py data.tsv --sep '\t'

# 输出 JSON 供下游消费
python3 scripts/profile_dataset.py data.csv --json > profile.json
```

**常见坑**：
- 伪装缺失（`"N/A"`、`"unknown"`、`""`、`"null"`）不会被当成缺失，**必须先跑画像看 `missing_tokens` 再决定规则**，否则质量门禁会漏检。
- 高基数文本列（如 UUID）会被判为「候选主键」，需人工确认是否真主键。

## 2. ab_test_calc.py — A/B 实验计算器

子命令：`power` 样本量 / `srm` 分流校验 / `prop` 比率检验 / `mean` 均值检验。

```bash
# 开跑前算样本量（基线 10%，最小可检测效应 1pp）
python3 scripts/ab_test_calc.py power --baseline 0.10 --mde 0.01

# 开跑后先验 SRM（两组分流是否均衡）
python3 scripts/ab_test_calc.py srm --counts 502341 497108

# 比率检验（如转化率）
python3 scripts/ab_test_calc.py prop \
  --a-n 50000 --a-x 1500 --b-n 50000 --b-x 1620

# 均值检验（如时长）
python3 scripts/ab_test_calc.py mean \
  --a-n 4000 --a-mean 82.1 --a-sd 31.5 \
  --b-n 4050 --b-mean 85.3 --b-sd 33.2
```

**常见坑**：
- `power` 的 `--mde` 是**绝对百分点**不是相对比例；想要「相对 +10%」要先换算。
- SRM 即便 p>0.05 也要看分流差异是否业务可解释，别只看显著性。
- 不要用 `mean` 检验当数据明显偏态（时长类）时直接下结论，先确认分布。

## 3. data_quality_check.py — 数据质量断言

JSON 规则驱动，硬断言失败退出码 1（可直接进管道门禁）。

```bash
python3 scripts/data_quality_check.py data.csv \
  --rules assets/data-quality-rules.json
```

**常见坑**：
- 质量门禁**不猜哨兵值**：没在 `missing_tokens` 里声明的 `unknown` 会被当作正常取值参与枚举检查，漏声明 = 漏检。
- 先跑 `profile_dataset.py` 找出伪装缺失值，再把它们写进规则文件的 `missing_tokens`，再接门禁。

## 相关引用与层次边界

> 本文是 `scripts/` 的**使用说明层**；方法背景见对应 reference。

- 数据质量规则与管道门禁 → `references/data-pipeline.md`
- 数据画像脚本背景 → `references/exploratory-analysis.md`
- A/B 检验脚本背景 → `references/experimentation-ab-testing.md` / `references/statistical-inference.md`
- ETL 落地操作 → `skills/data-pipeline-builder/SKILL.md`
