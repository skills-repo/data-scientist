---
name: sql-query-writer
description: SQL 查询生成、优化与调试，支持 MySQL/PostgreSQL/SQLite，从自然语言到高性能 SQL
source:
  type: original
  repo: skills-repo/data-scientist
  path: skills/sql-query-writer/SKILL.md
  version: 1.0.0
  updated: 2026-07-26
metadata:
  category: SQL
  platform: 通用
  difficulty: 入门
---

# SQL 查询编写器

> 从自然语言需求生成高性能 SQL 查询：建表、增删改查、JOIN、子查询、窗口函数、索引优化。

## 能力

- **自然语言转 SQL**：描述需求即可生成对应查询
- **多方言支持**：MySQL、PostgreSQL、SQLite 语法适配
- **查询优化**：分析 EXPLAIN 输出，建议索引、重写慢查询
- **Schema 理解**：读取已有表结构，生成符合规范的查询
- **数据迁移**：生成 ALTER TABLE、数据迁移脚本

## 使用方式

```
/sql-query-writer 查出过去 30 天每天的新增用户数
/sql-query-writer 优化这个慢查询: [粘贴 SQL]
/sql-query-writer 设计一个电商订单表结构
```

## 工作流

1. 接收查询需求或现有 SQL
2. 理解上下文（表结构、业务逻辑）
3. 生成 SQL（附注释说明）
4. 预测性能问题并给出优化建议
5. 输出可执行的完整查询

## 适用场景

- 不熟悉 SQL 的开发者需要写数据库查询
- 复杂 JOIN/子查询/窗口函数手写容易出错
- 慢查询需要分析和重写
- 新项目设计数据库表结构

## 限制

- 不连接实际数据库，不执行查询
- 复杂 OLAP/数据仓库场景不在范围内
- 优化建议依赖提供的表结构信息完整性
