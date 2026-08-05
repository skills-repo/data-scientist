# AGENTS.md — 数据科学家技能库

> 本仓库为 **skills-repo/data-scientist**，采用 **superpower 架构**。
> 本文件是 Agent 的入口说明，人类读者请看 [README.md](README.md)。

## 加载顺序（务必遵守）

1. **先读 `SKILL.md`** —— 它是路由表，不是内容。根据任务在表中定位该读哪个文件。
2. **按需读 `references/<topic>.md`** —— 只读当前任务相关的那一两篇，不要全量加载。
   每篇约 8K，全部读完会挤占上下文，把真正的数据挤出去。
3. **能用 `scripts/` 就不要手写代码** —— 见下方"脚本优先"。
4. **产出文档前先看 `assets/`** —— 有模板就别从空白开始写。
5. **具体工具操作调 `skills/` 子技能** —— 如生成 AntV 图表、执行 pscale 命令。

## 脚本优先（重要）

以下任务**必须**调用脚本，不要即兴写 pandas 代码：

| 任务 | 命令 |
|------|------|
| 摸清一份 CSV 的质量与结构 | `python3 scripts/profile_dataset.py <file>` |
| 算实验样本量 | `python3 scripts/ab_test_calc.py power --baseline <p> --mde <d>` |
| 校验实验分流是否正常 | `python3 scripts/ab_test_calc.py srm --counts <n_a> <n_b>` |
| 比率型指标显著性检验 | `python3 scripts/ab_test_calc.py prop --a-n .. --a-x .. --b-n .. --b-x ..` |
| 均值型指标显著性检验 | `python3 scripts/ab_test_calc.py mean --a-n .. --a-mean .. --a-sd .. --b-n .. --b-mean .. --b-sd ..` |
| 执行数据质量断言 | `python3 scripts/data_quality_check.py <file> --rules <rules.json>` |

脚本特性：**纯标准库、不联网、不修改被检查的文件**，支持 `--json` 输出便于串联。
`data_quality_check.py` 硬断言失败时退出码为 1，可直接接进管道阻断下游。

两个脚本的配合次序很重要：先跑 `profile_dataset.py` 找出伪装缺失值（`unknown`/`N/A`/`-1`），
再把它们写进规则文件的 `missing_tokens`。质量门禁**不猜哨兵值**——没声明的 `unknown`
会被当作正常取值参与枚举检查，从而漏报。

## 行为准则

- **先问粒度**：任何取数任务，先说清"一行代表什么"。JOIN 前必须验证右表在 JOIN KEY 上唯一，
  否则金额类指标会被静默放大。
- **口径先行**：涉及指标时先确认分子、分母、时间窗、时区、排除项。
  口径没对齐就出数，等于制造下一场会议上的争吵。
- **不替用户拍板**：给出结论、量化不确定性、指出风险，业务决策交回用户。
- **结论带边界**：明确写出成立前提、不可外推的范围、哪些是相关而非因果。
- **拒绝伪确定性**：确信度低就写低。把不确定包装成确定，比给不出结论危害更大。
- **统计结论的表述规范**：必须同时给出效应量、置信区间、p 值。
  "不显著"要表述为「证据不足」而非「证明无差异」。
- **敏感数据**：识别到手机号、身份证、邮箱、地址等字段时，先脱敏再分析，输出中不得原样回显。
- **实验纪律**：判定标准必须在看到数据之前锁死。用户中途问"现在显著了吗"，
  要说明峰值窥探会把假阳性率从 5% 推到 20%+，并引导其等到预定终点。

## 陷阱自查（出结论前必过）

发布任何分析结论前，逐条检查 `references/exploratory-analysis.md` 第 8 节的清单：
辛普森悖论、幸存者偏差、时间泄漏、分母陷阱、选择偏差、回归到均值、多重比较、时间窗口。

**这是本技能被调用时最有价值的动作**，不要因为"用户只是想快速看个数"而跳过。

## 子技能

| 技能 | 用途 |
|------|------|
| `data-analysis-toolkit` | 电子表格分析、洞察生成、趋势检测、统计报告 |
| `data-pipeline-builder` | ETL 落地：提取、转换、加载、调度与错误处理 |
| `data-visualizer` | AntV 图表生成，20+ 图表类型 |
| `sql-query-writer` | SQL 编写优化、schema 设计、PlanetScale CLI 自动化 |

## 定位与边界

- 聚焦"从数据到洞察"的完整链路，覆盖分析、实验、指标、管道四条主线
- 不替代专业 BI 工具或大数据平台，也不做模型训练与上线（那属于 `machine-learning-engineer`）
- 需要跨域协作时：演示材料 → `presentation-master`；建模 → `machine-learning-engineer`；
  数据库调优 → `database-engineer`；管道部署 → `devops-engineer`
