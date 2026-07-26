# 数据科学技能库

> AI Agent Skills for Data Science —— 覆盖数据管道、分析工具包、可视化图表、SQL 查询

## 定位

为数据工程师和分析师提供一套可安装的 AI Agent 数据技能，让 Claude Code 成为你的数据搭档。

## 核心理念

> 让数据处理自动化。从提取到分析，从 SQL 到可视化，一个人也能高效产出。

- **流式处理**——数据从来源到洞察的自动化流水线
- **低门槛分析**——不需要数据科学家也能完成探索性分析
- **可视化优先**——好的图表比数字更有说服力

## 技能清单

| 环节 | 技能 | 描述 | 来源 |
|------|------|------|------|
| 📡 数据管道 | `data-pipeline-builder` | 数据管道与 ETL 自动化：提取、转换、加载，调度与错误处理 | [衍生](https://skills.sh/claude-office-skills/skills/data-pipeline) |
| 📊 分析工具 | `data-analysis-toolkit` | 数据分析：电子表格分析、洞察生成、趋势检测、可视化图表 | [衍生](https://skills.sh/claude-office-skills/skills/data-analysis) |
| 📈 可视化 | `data-visualizer` | AntV 图表可视化：20+ 图表类型，柱状图、饼图、雷达图等 | [衍生](https://skills.sh/antvis/chart-visualization-skills/chart-visualization) |
| 🗄️ SQL 查询 | `sql-query-writer` | SQL 查询编写与优化：schema 设计、查询优化、CLI 自动化 | [衍生](https://skills.sh/planetscale/skills/planetscale-pscale-cli-automation) |

## 快速开始

```bash
npx skills add skills-repo/data-scientist@data-pipeline-builder -g -y
npx skills add skills-repo/data-scientist@data-analysis-toolkit -g -y
npx skills add skills-repo/data-scientist@data-visualizer -g -y
npx skills add skills-repo/data-scientist@sql-query-writer -g -y
```

## 推荐工作流

```
数据提取 → 分析探索 → 可视化呈现 → SQL 深度查询
data-     data-      data-        sql-
pipeline  analysis   visualizer   query
builder   toolkit                 writer
```

## 许可

MIT
