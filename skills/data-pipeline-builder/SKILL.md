---
name: data-pipeline-builder
description: 数据处理流水线构建：ETL 流程、数据清洗、格式转换、批处理调度，面向个人和小项目
source:
  type: original
  repo: skills-repo/data-scientist
  path: skills/data-pipeline-builder/SKILL.md
  version: 1.0.0
  updated: 2026-07-26
metadata:
  category: 数据工程
  platform: 通用
  difficulty: 进阶
---

# 数据流水线构建器

> 为个人数据项目构建轻量级数据处理流水线：ETL、清洗、转换、调度。不是 Airflow 级的企业方案，是你能在 30 分钟内跑起来的数据管道。

## 能力

- **ETL 流程设计**：Extract（CSV/API/DB）→ Transform（清洗/聚合）→ Load（输出到文件/DB）
- **数据清洗**：缺失值处理、异常值检测、类型转换、去重、标准化
- **格式转换**：CSV ↔ JSON ↔ Parquet ↔ SQL，编码检测与修复
- **批处理脚本**：Python/Node.js 数据批处理脚本生成
- **错误处理**：数据验证、重试逻辑、断点续传

## 使用方式

```
/data-pipeline 设计一个从 API 拉取数据 → 清洗 → 存入 SQLite 的流水线
/data-pipeline 这个 CSV 有脏数据，帮我写清洗脚本
/data-pipeline 把 JSON 日志批量转成 Parquet
```

## 工作流

1. 描述数据源和目标
2. AI 分析数据格式和质量问题
3. 生成 ETL 流水线脚本（含错误处理和日志）
4. 输出本地可运行代码

## 技术栈选型

| 场景 | 推荐工具 |
|------|---------|
| CSV/JSON 清洗 | Python + pandas |
| API 数据拉取 | Python + requests + tenacity |
| SQL 导入导出 | Python + SQLAlchemy |
| 定时调度 | crontab / systemd timer |
| 格式转换 | Python + pyarrow |

## 适用场景

- 个人数据项目的数据处理流程
- 公开数据集清洗和导入
- 多个数据源的定期同步
- 日志分析和归档

## 限制

- 不涉及 Kafka/Spark/Flink 等流处理框架
- 不适合 TB 级数据（那是大数据工程范围）
- 生成的流水线需要本地环境安装依赖
