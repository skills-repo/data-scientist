# 数据科学技能库

> AI Agent Skills for Data Science —— 从原始数据到可执行结论的完整链路

[![architecture](https://img.shields.io/badge/architecture-superpower-blue)](#架构)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 定位

把 AI 助手变成一名**能独立扛下整条分析链路**的数据科学搭档：既能写出粒度正确、口径清晰的
SQL，也能在结论发布前拦下辛普森悖论和幸存者偏差；既能设计一个不会被峰值窥探污染的 A/B 实验，
也能把清洗规则固化成阻断脏数据的管道门禁。

**这个库真正的价值不在"教你怎么算"，而在"拦住你算错"。**
大部分分析事故不是算法不够高级，而是粒度搞错了、分母变了、样本是幸存者、
或者中途看了几眼数据就提前下了结论。

## 架构

本仓库采用 **superpower 架构**——`SKILL.md` 只做路由，深层内容按需加载，避免一次性占满上下文。

```
data-scientist/
├── SKILL.md                    # L1 路由层：能力索引 + grep 关键词
├── references/                 # L2 深层 playbook（按需加载）
│   ├── exploratory-analysis.md         # EDA 与分析陷阱
│   ├── data-cleaning.md                # 清洗决策与清洗日志
│   ├── sql-analytics.md                # 分析型 SQL：粒度、窗口、性能
│   ├── statistical-inference.md        # 假设检验、置信区间、多重比较
│   ├── experimentation-ab-testing.md   # A/B 实验设计与解读
│   ├── data-visualization.md           # 图表选型与误导识别
│   ├── data-pipeline.md                # ETL 分层、幂等、回填
│   └── metrics-design.md               # 指标体系与口径治理
├── skills/                     # L3 细粒度子技能（可单独安装）
│   ├── data-analysis-toolkit/
│   ├── data-pipeline-builder/
│   ├── data-visualizer/
│   └── sql-query-writer/
├── scripts/                    # L4 确定性脚本（零依赖）
│   ├── profile_dataset.py              # 数据画像
│   ├── ab_test_calc.py                 # 实验计算器
│   └── data_quality_check.py           # 质量断言门禁
└── assets/                     # L5 可复用模板
    ├── data-quality-rules.json
    ├── eda-report-template.md
    ├── experiment-design-doc.md
    ├── metrics-dictionary.md
    ├── sql-analysis-patterns.sql
    ├── chart-review-checklist.md
    └── pipeline-runbook.md
```

## 内置脚本

**纯 Python 标准库，零第三方依赖，不联网，不修改被检查的文件。** 直接可用，无需安装。

```bash
# 数据画像——拿到新数据的第一个动作
python3 scripts/profile_dataset.py data.csv

# A/B 实验计算器
python3 scripts/ab_test_calc.py power --baseline 0.10 --mde 0.01   # 样本量
python3 scripts/ab_test_calc.py srm   --counts 502341 497108        # 分流校验
python3 scripts/ab_test_calc.py prop  --a-n 50000 --a-x 1500 --b-n 50000 --b-x 1620

# 数据质量门禁（退出码 1 即阻断下游）
python3 scripts/data_quality_check.py data.csv --rules assets/data-quality-rules.json
```

`profile_dataset.py` 会揪出这些容易被忽略的问题：

- 伪装成正常值的缺失（`unknown` / `N/A` / `-1` / `9999`）——它们不会触发任何非空约束
- 格式像日期但不是真实日期的值（`2026-13-45` 能过正则，过不了日历）
- 仅大小写不同的重复类别（`app` 与 `APP` 会被分组统计拆成两行）
- 超出 IQR 上界数十倍的极值——小样本里占比不高，但足以毁掉均值
- 完全重复行与失效的候选主键

## 技能清单

| 环节 | 技能 | 描述 | 来源 |
|------|------|------|------|
| 📡 数据管道 | `data-pipeline-builder` | 数据管道与 ETL 自动化：提取、转换、加载，调度与错误处理 | [衍生](https://skills.sh/claude-office-skills/skills/data-pipeline) |
| 📊 分析工具 | `data-analysis-toolkit` | 数据分析：电子表格分析、洞察生成、趋势检测、可视化图表 | [衍生](https://skills.sh/claude-office-skills/skills/data-analysis) |
| 📈 可视化 | `data-visualizer` | AntV 图表可视化：20+ 图表类型，柱状图、饼图、雷达图等 | [衍生](https://skills.sh/antvis/chart-visualization-skills/chart-visualization) |
| 🗄️ SQL 查询 | `sql-query-writer` | SQL 查询编写与优化：schema 设计、查询优化、CLI 自动化 | [衍生](https://skills.sh/planetscale/skills/planetscale-pscale-cli-automation) |

## 快速开始

安装整个技能库（推荐，可用到 references / scripts / assets 全部内容）：

```bash
npx skills add skills-repo/data-scientist -g -y
```

或只安装单个子技能：

```bash
npx skills add skills-repo/data-scientist@data-pipeline-builder -g -y
npx skills add skills-repo/data-scientist@data-analysis-toolkit -g -y
npx skills add skills-repo/data-scientist@data-visualizer -g -y
npx skills add skills-repo/data-scientist@sql-query-writer -g -y
```

## 推荐工作流

```
                ┌─────────────────────────────────────────────┐
                │  拿到数据                                    │
                └───────────────┬─────────────────────────────┘
                                ▼
        profile_dataset.py  ──▶ 数据画像：粒度？缺失？极值？主键？
                                │
                                ▼
        references/data-cleaning.md ──▶ 清洗决策，规则写进 rules.json
                                │
                                ▼
        assets/sql-analysis-patterns.sql ──▶ 取数（先验 JOIN 粒度）
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
        分析路径                          实验路径
        exploratory-analysis.md          experiment-design-doc.md
        metrics-design.md                ab_test_calc.py power/srm
                │                               │
                ▼                               ▼
        eda-report-template.md           statistical-inference.md
        （含 8 项陷阱自查）                （效应量 + CI，不只报 p 值）
                │                               │
                └───────────────┬───────────────┘
                                ▼
        chart-review-checklist.md ──▶ 出图前审查，排除五种误导
                                │
                                ▼
        pipeline-runbook.md ──▶ 沉淀为管道 + 质量门禁，让结论可复现
```

## 设计原则

1. **先问粒度，再写代码**——说不清"一行代表什么"就动手，后面所有数字都是错的
2. **结论必须带边界**——写清成立前提、不能外推到哪里、哪些只是相关而非因果
3. **能被脚本验证的，不靠人眼**——跑一遍的成本远低于结论错了之后的返工
4. **报效应量与置信区间，不只报 p 值**——"不显著"是证据不足，不是证明无差异
5. **判定标准写在看到数据之前**——事后调整判定标准等于自欺

## 许可

MIT
