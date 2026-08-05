---
name: data-scientist
description: >-
  数据科学与分析全链路技能库：从探索性分析、数据清洗、SQL 取数、指标体系设计，到统计推断、
  A/B 实验设计与结果解读、数据可视化、ETL 数据管道搭建与数据质量门禁。内置零依赖脚本可直接
  对 CSV 做数据画像、跑 A/B 实验统计检验、执行数据质量断言。适用于业务分析、实验评估、
  指标口径治理、数据管道上线等场景，并覆盖辛普森悖论、幸存者偏差、峰值窥探、p 值误读等
  典型分析陷阱的识别与规避。
  触发词："数据分析、探索性分析、EDA、数据清洗、数据画像、SQL 分析、取数、留存、漏斗、
  指标体系、指标口径、北极星指标、统计推断、假设检验、p 值、置信区间、样本量、AB 测试、
  A/B 实验、实验设计、SRM、CUPED、数据可视化、图表选型、ETL、数据管道、数据质量、
  data-analysis-toolkit、data-pipeline-builder、data-visualizer、sql-query-writer"。
agent_created: true
metadata:
  version: 2.0.0
  category: 数据科学与分析
  difficulty: 专家
  architecture: superpower
---

# Data Scientist

> 把 AI 助手变成一名**能独立扛下"从原始数据到可执行结论"整条链路**的数据科学搭档：
> 既能写出粒度正确、口径清晰的 SQL，也能在结论发布前拦下辛普森悖论和幸存者偏差；
> 既能设计一个不会被峰值窥探污染的 A/B 实验，也能把清洗规则固化成阻断脏数据的管道门禁。

本技能采用 **superpower 架构**：`SKILL.md` 只做路由，深层 playbook 放在 `references/` 中
**按需加载**，细粒度能力放在 `skills/` 子技能，确定性任务交给 `scripts/`，可复用模板放在 `assets/`。

## 何时使用

在以下任一情况触发本技能：

- 拿到一份陌生数据，需要摸清质量、粒度与分布，判断它能不能支撑要回答的问题
- 需要写分析型 SQL：留存、漏斗、同环比、分组 Top N，且必须保证 JOIN 粒度与口径正确
- 要设计或评估一个 A/B 实验：算样本量、查 SRM、做显著性检验、解读置信区间
- 业务方问"这个数为什么涨/跌"，需要做异动归因而不是给一句"受多种因素影响"
- 需要建立或治理指标体系：定义口径、拆解北极星、处理"会上出现两个 DAU"的问题
- 要做数据可视化，且这张图会被拿去做决策，不能有误导性编码
- 搭建 ETL 管道，需要保证幂等、处理迟到数据、设置数据质量门禁
- **需要在结论发布前做一次陷阱自查**——这是本技能最该被调用的时刻

## 能力索引（超级技能路由）

本技能采用渐进式加载（progressive disclosure）。`SKILL.md` 仅作路由，**按需**读取下列
`references/` 中的完整 playbook，避免一次性占满上下文。

| 任务 | 读取 / 调用 | 关键词（grep 线索） |
|------|------------|---------------------|
| 拿到陌生数据先做什么、如何避免分析陷阱 | `references/exploratory-analysis.md` | EDA, 数据画像, 辛普森悖论, 幸存者偏差, 时间泄漏, 分母陷阱 |
| 缺失值/重复/异常值/一致性的处理决策 | `references/data-cleaning.md` | 清洗, 缺失值, 去重, 异常值, 伪装缺失, 清洗日志 |
| 分析型 SQL 的粒度、窗口函数与性能 | `references/sql-analytics.md` | SQL, JOIN 粒度, 窗口函数, 留存, 漏斗, 分区裁剪, 执行计划 |
| p 值/置信区间/检验选择/多重比较 | `references/statistical-inference.md` | 假设检验, p 值, 置信区间, 效应量, 样本量, 检验力, 多重比较 |
| A/B 实验的设计、执行与结果解读 | `references/experimentation-ab-testing.md` | AB 测试, 实验设计, 随机化单元, SRM, 峰值窥探, CUPED, MDE |
| 图表选型、误导识别、仪表盘设计 | `references/data-visualization.md` | 可视化, 图表选型, 双 Y 轴, 色盲友好, chartjunk, 仪表盘 |
| ETL/ELT 分层、幂等、迟到数据、回填 | `references/data-pipeline.md` | ETL, 数据管道, 幂等, 增量, 回填, schema 演进, 数据质量 |
| 指标定义、分层拆解、口径治理、异动归因 | `references/metrics-design.md` | 指标体系, 北极星, 口径, 比率陷阱, 指标腐化, 异动归因 |
| 电子表格分析、洞察生成、趋势检测与统计报告（细粒度调用） | `skills/data-analysis-toolkit/SKILL.md` | 电子表格, Excel, 洞察, 趋势检测, 统计报告 |
| ETL 任务落地：提取转换加载、调度与错误处理（细粒度调用） | `skills/data-pipeline-builder/SKILL.md` | ETL, 提取, 转换, 加载, 调度, 错误处理 |
| AntV 图表生成，20+ 图表类型（细粒度调用） | `skills/data-visualizer/SKILL.md` | AntV, 折线图, 柱状图, 饼图, 散点图, 图表生成 |
| SQL 编写优化、schema 设计、PlanetScale CLI（细粒度调用） | `skills/sql-query-writer/SKILL.md` | SQL 优化, schema 设计, PlanetScale, pscale |

> **路由规则**：
> 1. 任务是**判断"该怎么分析、结论能不能信"** → 读 `references/`。
> 2. 任务是**执行一个确定性动作**（画像、算样本量、跑质量检查）→ 直接用 `scripts/`，别手写代码。
> 3. 任务是**产出一份文档/规则文件** → 从 `assets/` 取模板改，别从空白开始。
> 4. 任务是**具体工具操作**（生成 AntV 图表、跑 pscale 命令）→ 调 `skills/` 子技能。

## 内置脚本（确定性、可重复执行）

放在 `scripts/`，**纯 Python 标准库、零第三方依赖、不联网、不修改被检查的文件**。
优先用脚本处理重复/确定性任务，而非每次重写代码：

| 脚本 | 用途 | 典型场景 |
|------|------|----------|
| `scripts/profile_dataset.py` | CSV/TSV 数据画像：类型推断、缺失率、基数、分布、异常值、伪装缺失、候选主键 | 拿到新数据的第一个动作 |
| `scripts/ab_test_calc.py` | A/B 实验计算器：`power` 样本量 / `srm` 分流校验 / `prop` 比率检验 / `mean` 均值检验 | 实验设计与结果判定 |
| `scripts/data_quality_check.py` | JSON 规则驱动的数据质量断言，硬断言失败退出码 1 | 管道门禁、清洗验收 |

运行示例：

```bash
# 1) 拿到数据先看画像——伪装缺失、极值、重复行会在这里暴露
python3 scripts/profile_dataset.py data.csv
python3 scripts/profile_dataset.py data.tsv --sep '\t' --json > profile.json

# 2) 实验开跑前算样本量；开跑后先验 SRM，再做显著性检验
python3 scripts/ab_test_calc.py power --baseline 0.10 --mde 0.01
python3 scripts/ab_test_calc.py srm  --counts 502341 497108
python3 scripts/ab_test_calc.py prop --a-n 50000 --a-x 1500 --b-n 50000 --b-x 1620
python3 scripts/ab_test_calc.py mean --a-n 4000 --a-mean 82.1 --a-sd 31.5 \
                                     --b-n 4050 --b-mean 85.3 --b-sd 33.2

# 3) 把清洗规则固化成门禁，接进管道（退出码 1 即阻断下游）
python3 scripts/data_quality_check.py data.csv --rules assets/data-quality-rules.json
```

> 先跑 `profile_dataset.py` 找出伪装缺失值，再把它们写进规则文件的 `missing_tokens`——
> 质量门禁**不猜哨兵值**，没声明的 `unknown` 会被当作正常取值参与枚举检查。

## 模板资源

`assets/` 提供可直接套用的模板，改占位符即可交付：

| 模板 | 用途 | 对应 reference |
|------|------|----------------|
| `assets/data-quality-rules.json` | 数据质量规则模板（硬断言/软约束、哨兵值声明） | data-cleaning / data-pipeline |
| `assets/eda-report-template.md` | 探索性分析报告模板，含 8 项陷阱自查 | exploratory-analysis |
| `assets/experiment-design-doc.md` | 实验设计文档（预注册），含结果判定矩阵 | experimentation / statistical-inference |
| `assets/metrics-dictionary.md` | 指标字典模板，含口径版本管理与陷阱速查 | metrics-design |
| `assets/sql-analysis-patterns.sql` | 分析型 SQL 模式库：粒度校验、漏斗、留存、同环比、辛普森自检 | sql-analytics |
| `assets/chart-review-checklist.md` | 图表交付前审查清单，含五种常见误导 | data-visualization |
| `assets/pipeline-runbook.md` | 数据管道 Runbook：幂等、回填、故障处理、上线检查 | data-pipeline |

## 核心原则（始终遵循）

1. **先问粒度，再写代码**。说不清"一行代表什么"就动手，后面所有数字都是错的。
   JOIN 前必须验证右表在 JOIN KEY 上唯一。
2. **结论必须带边界**。写清成立前提、不能外推到哪里、哪些是相关而非因果。
   把不确定的结论包装成确定，比给不出结论危害更大。
3. **渐进式加载**：先读路由表与对应 `references/`，再动手；不凭记忆猜命令与 API。
4. **能被脚本验证的，不靠人眼**。数据画像、样本量、质量断言都有脚本，
   跑一遍的成本远低于结论错了之后的返工。
5. **报效应量与置信区间，不只报 p 值**。"不显著"是证据不足，不是证明无差异；
   显著也不等于业务上值得做。
6. **判定标准写在看到数据之前**。实验的停止规则、指标口径、质量阈值都要预先锁死，
   事后调整判定标准等于自欺。
7. **明确边界**：本技能负责给出分析结论、量化不确定性、指出风险，
   **不替用户拍板业务决策**；涉及个人敏感数据时先脱敏再分析。

## 与其他技能协作

- 需要把分析结论做成演示材料 → 调用 `skills-repo/presentation-master`
- 需要建模、特征工程与模型上线 → 调用 `skills-repo/machine-learning-engineer`
- 需要数据库 schema 设计与调优 → 调用 `skills-repo/database-engineer`
- 需要把管道部署进 CI/CD 与可观测体系 → 调用 `skills-repo/devops-engineer`
- 需要把分析结论写成正式报告文档 → 调用 `skills-repo/docs-writer`
