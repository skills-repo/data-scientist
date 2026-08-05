-- =====================================================================
-- 分析型 SQL 模式库
-- 配套 references/sql-analytics.md
--
-- 说明：以 ANSI SQL / 主流数仓（Hive、Spark、Presto、BigQuery、ClickHouse）
-- 通用写法为主。方言差异在注释中标出。
-- 用法：复制对应模式，替换 {{占位符}}，先在小分区上验证再跑全量。
-- =====================================================================


-- ---------------------------------------------------------------------
-- 0. 每次写分析 SQL 前的三个必答问题
-- ---------------------------------------------------------------------
-- a) 这张表的粒度是什么？一行代表什么？（订单？订单行？用户日？）
-- b) JOIN 之后粒度会不会变？会不会把主表行数放大？
-- c) 时间字段是事件时间还是写入时间？分区字段是哪个？
--
-- 不回答完这三个问题就开始写 SQL，等于在猜。


-- ---------------------------------------------------------------------
-- 1. JOIN 前先验粒度 —— 防止一对多把指标翻倍
-- ---------------------------------------------------------------------
-- 症状：JOIN 完之后 GMV 突然涨了 3 倍。原因几乎总是右表不唯一。
-- 铁律：JOIN 之前先确认右表在 JOIN KEY 上唯一。

SELECT
    COUNT(*)                        AS total_rows,
    COUNT(DISTINCT {{join_key}})    AS distinct_keys,
    COUNT(*) - COUNT(DISTINCT {{join_key}}) AS dup_rows   -- 必须为 0
FROM {{right_table}}
WHERE dt = '{{dt}}';

-- 若不唯一，先聚合到目标粒度再 JOIN，不要直接 JOIN 后 DISTINCT
-- （DISTINCT 只是把错误藏起来，金额类指标照样错）。
WITH right_agg AS (
    SELECT
        {{join_key}},
        SUM({{amount}}) AS amount,      -- 明确聚合方式，而不是随便取一行
        MAX({{updated_at}}) AS updated_at
    FROM {{right_table}}
    WHERE dt = '{{dt}}'
    GROUP BY {{join_key}}
)
SELECT l.*, r.amount
FROM {{left_table}} l
LEFT JOIN right_agg r ON l.{{join_key}} = r.{{join_key}}
WHERE l.dt = '{{dt}}';


-- ---------------------------------------------------------------------
-- 2. 去重取最新一条 —— 拉链表/状态表的标准写法
-- ---------------------------------------------------------------------
-- 不要用 GROUP BY + MAX(其他列)：那会把不同行的字段拼成一条不存在的记录。
WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY {{entity_id}}
            ORDER BY {{updated_at}} DESC, {{tie_breaker}} DESC   -- 必须有 tie-breaker，否则结果不稳定
        ) AS rn
    FROM {{table}}
    WHERE dt = '{{dt}}'
)
SELECT * FROM ranked WHERE rn = 1;


-- ---------------------------------------------------------------------
-- 3. 漏斗分析 —— 带顺序约束与时间窗
-- ---------------------------------------------------------------------
-- 常见错误：把"做过 A"和"做过 B"直接相除，忽略了 B 必须发生在 A 之后。
WITH steps AS (
    SELECT
        user_id,
        MIN(CASE WHEN event = '{{step1}}' THEN event_time END) AS t1,
        MIN(CASE WHEN event = '{{step2}}' THEN event_time END) AS t2,
        MIN(CASE WHEN event = '{{step3}}' THEN event_time END) AS t3
    FROM {{event_table}}
    WHERE dt BETWEEN '{{start}}' AND '{{end}}'
    GROUP BY user_id
)
SELECT
    COUNT(*)                                                        AS s1_users,
    COUNT(CASE WHEN t2 > t1 AND t2 <= t1 + INTERVAL '{{7}}' DAY THEN 1 END) AS s2_users,
    COUNT(CASE WHEN t3 > t2 AND t3 <= t1 + INTERVAL '{{7}}' DAY THEN 1 END) AS s3_users,
    -- 分子分母同时输出，永远不要只给比率
    ROUND(COUNT(CASE WHEN t2 > t1 THEN 1 END) * 1.0 / NULLIF(COUNT(*), 0), 4) AS cvr_1_2
FROM steps
WHERE t1 IS NOT NULL;


-- ---------------------------------------------------------------------
-- 4. 留存分析 —— 按注册日分群
-- ---------------------------------------------------------------------
WITH cohort AS (
    SELECT user_id, MIN(DATE(register_time)) AS cohort_date
    FROM {{user_table}}
    GROUP BY user_id
),
activity AS (
    SELECT DISTINCT user_id, DATE(event_time) AS active_date
    FROM {{event_table}}
    WHERE dt BETWEEN '{{start}}' AND '{{end}}'
)
SELECT
    c.cohort_date,
    DATE_DIFF(a.active_date, c.cohort_date) AS day_n,   -- Hive: DATEDIFF(a.active_date, c.cohort_date)
    COUNT(DISTINCT c.user_id)               AS retained_users,
    -- 分母固定为该 cohort 的总人数，否则留存率会随分母变化而失真
    COUNT(DISTINCT c.user_id) * 1.0
        / NULLIF(MAX(COUNT(DISTINCT c.user_id)) OVER (PARTITION BY c.cohort_date), 0) AS retention_rate
FROM cohort c
LEFT JOIN activity a ON c.user_id = a.user_id AND a.active_date >= c.cohort_date
WHERE c.cohort_date BETWEEN '{{start}}' AND '{{end}}'
GROUP BY c.cohort_date, day_n;

-- 注意：观察窗不足的 cohort 不能与老 cohort 并列比较。
-- 昨天注册的用户不可能有 7 日留存——把它画进折线图就是在制造下跌假象。


-- ---------------------------------------------------------------------
-- 5. 同比 / 环比 / 移动平均
-- ---------------------------------------------------------------------
SELECT
    dt,
    {{metric}},
    LAG({{metric}}, 1)  OVER (ORDER BY dt) AS prev_day,
    LAG({{metric}}, 7)  OVER (ORDER BY dt) AS same_day_last_week,  -- 消除周内周期
    ROUND(({{metric}} - LAG({{metric}}, 7) OVER (ORDER BY dt)) * 1.0
          / NULLIF(LAG({{metric}}, 7) OVER (ORDER BY dt), 0), 4)   AS wow,
    AVG({{metric}}) OVER (ORDER BY dt ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma7
FROM {{daily_table}}
WHERE dt BETWEEN '{{start}}' AND '{{end}}'
ORDER BY dt;

-- 日环比几乎总是噪声（周内周期主导）。默认用周同比或 7 日移动平均。


-- ---------------------------------------------------------------------
-- 6. 分组内 Top N
-- ---------------------------------------------------------------------
WITH ranked AS (
    SELECT
        {{group_col}},
        {{item_col}},
        SUM({{metric}}) AS total,
        ROW_NUMBER() OVER (PARTITION BY {{group_col}} ORDER BY SUM({{metric}}) DESC) AS rk
    FROM {{table}}
    WHERE dt = '{{dt}}'
    GROUP BY {{group_col}}, {{item_col}}
)
SELECT * FROM ranked WHERE rk <= {{10}};


-- ---------------------------------------------------------------------
-- 7. 分位数（比均值更能描述长尾）
-- ---------------------------------------------------------------------
SELECT
    {{group_col}},
    COUNT(*)                                                        AS n,
    APPROX_PERCENTILE({{metric}}, 0.5)                              AS p50,
    APPROX_PERCENTILE({{metric}}, 0.9)                              AS p90,
    APPROX_PERCENTILE({{metric}}, 0.99)                             AS p99,
    AVG({{metric}})                                                 AS mean
FROM {{table}}
WHERE dt = '{{dt}}'
GROUP BY {{group_col}};
-- 方言：Hive/Spark 用 percentile_approx；Presto 用 approx_percentile；
--       PostgreSQL 用 percentile_cont(0.5) WITHIN GROUP (ORDER BY x)。
-- 若 mean 远大于 p50，报告里就不该出现 mean。


-- ---------------------------------------------------------------------
-- 8. 辛普森悖论自检 —— 整体结论与分组结论是否一致
-- ---------------------------------------------------------------------
-- 整体
SELECT
    {{group_flag}},
    SUM({{numerator}}) * 1.0 / NULLIF(SUM({{denominator}}), 0) AS overall_rate
FROM {{table}} WHERE dt = '{{dt}}' GROUP BY {{group_flag}};

-- 按混杂变量分层后再看一次。若方向反转，说明存在混杂，整体结论不可用。
SELECT
    {{confounder}},
    {{group_flag}},
    SUM({{denominator}})                                       AS n,
    SUM({{numerator}}) * 1.0 / NULLIF(SUM({{denominator}}), 0)  AS rate
FROM {{table}} WHERE dt = '{{dt}}'
GROUP BY {{confounder}}, {{group_flag}}
ORDER BY {{confounder}}, {{group_flag}};


-- ---------------------------------------------------------------------
-- 9. 性能：分区裁剪与谓词下推
-- ---------------------------------------------------------------------
-- 反例：对分区字段做函数运算 → 分区裁剪失效，全表扫描
--   WHERE DATE(dt) = '2026-01-01'
--   WHERE SUBSTR(dt, 1, 7) = '2026-01'
-- 正例：分区字段裸用
--   WHERE dt = '2026-01-01'
--   WHERE dt BETWEEN '2026-01-01' AND '2026-01-31'
--
-- 其他要点：
--   · 先过滤再 JOIN，不要 JOIN 完再 WHERE
--   · SELECT 明确列名，列存格式下 SELECT * 会拖垮 IO
--   · 大表 JOIN 小表时确认走了 broadcast/map join
--   · 数据倾斜（某个 key 占比过高）：先看 key 分布，再决定加盐还是单独处理
--
-- 上线前必做：EXPLAIN 看执行计划，确认分区裁剪生效、JOIN 策略符合预期。


-- ---------------------------------------------------------------------
-- 10. 交付前自检清单
-- ---------------------------------------------------------------------
-- [ ] 粒度：每个 CTE 的输出粒度我都能说清楚
-- [ ] JOIN：每个 JOIN 的右表在 KEY 上唯一，已验证
-- [ ] NULL：所有除法都套了 NULLIF，避免除零
-- [ ] NULL：LEFT JOIN 后的 NULL 是"无匹配"还是"值为空"，已区分
-- [ ] 时间：分区字段裸用，时区已确认，边界是闭区间还是开区间已明确
-- [ ] 口径：测试账号、内部流量、退款订单的排除规则与指标字典一致
-- [ ] 比率：分子分母都输出了，没有只给一个百分比
-- [ ] 验证：小分区跑通 + 与已有报表交叉核对过至少一个数
