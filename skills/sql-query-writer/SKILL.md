---
name: sql-query-writer
description: SQL 查询编写与优化：数据库 schema 设计、查询优化、PlanetScale CLI 自动化
source:
  type: derived
  repo: skills-repo/data-scientist
  path: skills/sql-query-writer/SKILL.md
  version: 1.0.0
  updated: 2026-07-26
  url: https://skills.sh/planetscale/skills/planetscale-pscale-cli-automation
metadata:
  category: 数据查询
  platform: 通用
  difficulty: 进阶
---

# SQL 查询编写器

> 数据库查询编写、优化与 Schema 设计：覆盖 MySQL/PostgreSQL，支持 CLI 自动化。

## 能力

- **查询编写**：SELECT/INSERT/UPDATE/DELETE 语句构造，子查询、JOIN、聚合
- **Schema 设计**：表结构设计、索引策略、外键约束、范式化
- **查询优化**：EXPLAIN 分析、索引建议、慢查询定位
- **CLI 自动化**：pscale 命令行工具的非交互式调用、JSON 格式输出
- **分支工作流**：数据库分支管理、Schema 变更审查、安全部署

## 使用方式

```
/sql-query-writer 为这个需求编写 SQL 查询
/sql-query-writer 审查这个数据库 schema 的设计
/sql-query-writer 优化这个慢查询的性能
```

## 工作流

1. 理解查询需求和数据关系
2. 编写 SQL 语句（SELECT/INSERT/UPDATE/DELETE）
3. 验证查询正确性（语法、逻辑、边界）
4. EXPLAIN 分析性能瓶颈
5. 提供优化建议和索引方案

## 适用场景

- 数据库查询编写和调试
- Schema 设计与审查
- 查询性能优化
- 数据库 CLI 操作自动化

## 限制

- 主要覆盖 MySQL/PostgreSQL 语法
- 不涉及 NoSQL 数据库
- 不涉及数据迁移和 ETL 流程

## 相关分析参考

> 本子技能属**工具执行层**（SQL 编写、优化、schema、CLI）；分析口径与判断标准见 reference。

- 分析型 SQL 的粒度、窗口函数、性能原则 → `references/sql-analytics.md`
- 指标口径与异动归因 → `references/metrics-design.md`
