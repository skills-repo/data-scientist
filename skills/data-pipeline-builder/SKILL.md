---
name: data-pipeline-builder
description: 数据管道与 ETL 自动化：提取、转换、加载，调度与错误处理
source:
  type: derived
  repo: skills-repo/data-scientist
  path: skills/data-pipeline-builder/SKILL.md
  version: 1.0.0
  updated: 2026-07-26
  url: https://skills.sh/claude-office-skills/skills/data-pipeline
metadata:
  category: 数据工程
  platform: 通用
  difficulty: 进阶
---

# 数据管道构建器

> 基于 n8n 的数据管道与 ETL 自动化：从多数据源提取、清洗转换、加载到目标存储。

## 能力

- **数据提取**：API、数据库、文件、Webhook 多源接入
- **数据转换**：清洗、映射、聚合、增强
- **数据加载**：数据库、数据仓库、文件系统、API 输出
- **调度管理**：定时触发、依赖编排、重试机制
- **错误处理**：失败告警、回滚策略、数据质量校验

## 使用方式

```
/data-pipeline-builder 设计一个从 API 到数据库的 ETL 流程
/data-pipeline-builder 帮我调试这个数据管道的转换逻辑
/data-pipeline-builder 为这个数据源配置增量同步策略
```

## 工作流

1. 确认数据源和目标存储
2. 设计提取策略（全量/增量/CDC）
3. 定义转换规则和数据模型
4. 配置调度和错误处理
5. 运行验证和监控

## 适用场景

- 多源数据汇聚和分析
- 数据仓库 ETL/ELT 构建
- 实时数据流处理
- 数据迁移项目

## 限制

- 不涉及流处理框架（Flink/Spark）
- 不涉及数据治理和元数据管理
- 需要理解数据建模基础

## 相关分析参考

> 本子技能属**工具执行层**（ETL 落地、调度、错误处理）；管道工程原则见 reference。

- 分层、幂等、增量、质量断言方法 → [`references/data-pipeline.md`](../../references/data-pipeline.md)
- 清洗/转换规则决策 → [`references/data-cleaning.md`](../../references/data-cleaning.md)
