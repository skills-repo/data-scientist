---
name: data-visualizer
description: 数据可视化图表生成：折线图、柱状图、热力图、散点图、饼图，支持 matplotlib/echarts/plotly
source:
  type: original
  repo: skills-repo/data-scientist
  path: skills/data-visualizer/SKILL.md
  version: 1.0.0
  updated: 2026-07-26
metadata:
  category: 可视化
  platform: 通用
  difficulty: 入门
---

# 数据可视化器

> 将数据变成直观的图表：选择正确的图表类型、生成美观的代码、标注关键洞察。支持 Python/R/JavaScript 可视化库。

## 能力

- **图表类型推荐**：根据数据类型（时间序列/分类/分布/关系）推荐最佳图表
- **多库支持**：matplotlib、seaborn、plotly、echarts、D3.js
- **美观默认**：配色方案、字体大小、标注位置的最佳实践
- **交互式图表**：plotly/echarts 交互式图表生成
- **Dashboard 布局**：多图表组合排版建议

## 使用方式

```
/data-visualizer 画过去 30 天的用户增长趋势图
/data-visualizer 用热力图展示各品类销售额的月份分布
/data-visualizer 这个数据适合用什么图表展示？
```

## 图表选择指南

| 数据类型 | 推荐图表 | 示例场景 |
|---------|---------|---------|
| 时间序列 | 折线图 | 日活用户趋势 |
| 类别比较 | 柱状图 | 各产品线收入对比 |
| 占比分布 | 饼图/环形图 | 用户来源渠道占比 |
| 分布形态 | 直方图/箱线图 | 用户年龄分布 |
| 变量关系 | 散点图 | 广告花费 vs 销售额 |
| 矩阵数据 | 热力图 | 相关矩阵 |
| 层次结构 | 树图/旭日图 | 品类→子品类→SKU |

## 工作流

1. 描述数据结构和展示目标
2. AI 推荐图表类型和配色
3. 生成可视化代码
4. 调整标注和注释
5. 输出可运行代码或图表示例

## 适用场景

- 数据分析报告的图表生成
- 产品指标 Dashboard
- 向非技术人员展示数据洞察
- 论文/演示文稿数据配图

## 限制

- 不处理超大数据的实时渲染（那是前端性能问题）
- 高度定制的图表可能需要手动调整细节
- 生成的图表代码需要在本地运行
