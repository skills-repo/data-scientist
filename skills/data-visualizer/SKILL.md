---
name: data-visualizer
description: 数据可视化：AntV 图表生成，支持折线图、柱状图、饼图、散点图等 20+ 类型
source:
  type: derived
  repo: skills-repo/data-scientist
  path: skills/data-visualizer/SKILL.md
  version: 1.0.0
  updated: 2026-07-26
  url: https://skills.sh/antvis/chart-visualization-skills/chart-visualization
metadata:
  category: 数据可视化
  platform: Web
  difficulty: 入门
---

# 数据可视化工具

> AntV 驱动的图表可视化：支持 20+ 图表类型，将数据转化为信息图表。

## 能力

- **比较类图表**：条形图、柱状图、瀑布图、双轴图
- **趋势类图表**：面积图、折线图、散点图
- **分布类图表**：箱线图、直方图、小提琴图、漏斗图
- **占比类图表**：饼图、水波图、词云、矩形树图
- **关系与流程**：桑基图、网络关系图、韦恩图、流程图、鱼骨图
- **多维图表**：雷达图、组织结构图、思维导图

## 使用方式

```
/data-visualizer 把这份销售数据生成季度对比柱状图
/data-visualizer 用饼图展示用户来源分布
/data-visualizer 为这个流程画一个流程图
```

## 工作流

1. 分析数据特征和可视化需求
2. 选择最合适的图表类型
3. 构造符合规范的 JSON 请求体
4. 调用 AntV API 生成图表图片
5. 以 Markdown 图片格式输出

## 适用场景

- 数据报告图表生成
- 商业演示数据可视化
- 流程架构图绘制
- 文本词频分析

## 限制

- 依赖 AntV API 服务
- 不涉及自定义交互式图表
- 图表数据量受 API 限制

## 相关分析参考

> 本子技能属**工具执行层**（AntV 图表生成）；图表选型与误导识别见 reference。

- 图表选型、误导编码识别、仪表盘设计 → [`references/data-visualization.md`](../../references/data-visualization.md)
- 指标口径与呈现边界 → [`references/metrics-design.md`](../../references/metrics-design.md)
