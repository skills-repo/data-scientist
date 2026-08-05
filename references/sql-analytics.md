# 分析型 SQL

> 分析 SQL 与业务 SQL 是两种手艺。业务 SQL 追求单点低延迟，分析 SQL 追求**在正确口径下
> 扫描尽可能少的数据**。写错了不会报错，只会给出一个看起来合理的错数字。

## 一、写之前先画口径

任何分析 SQL 动笔前，先用一句话写清三件事，写不出来就不要开始：

```
统计【时间范围】内，满足【过滤条件】的【实体粒度】的【指标定义】
例：统计 2026-07 内，非测试账号、已支付订单的，按用户去重的，首单金额中位数
```

**粒度**是最常出错的地方。一句 SQL 里只能有一个明确的输出粒度：
一行代表一个用户？一个订单？一个用户一天？粒度混乱会直接导致重复计数。

## 二、JOIN 会悄悄改变粒度

这是分析 SQL 里最高频的错误来源：

```sql
-- 订单表 1 行，订单明细表 3 行
SELECT o.order_id, o.amount, i.sku
FROM orders o JOIN order_items i ON o.order_id = i.order_id
-- 结果 3 行，amount 被复制了 3 次
-- 此时 SUM(o.amount) = 真实金额 × 3
```

防御手段：

1. **JOIN 前先确认右表在 JOIN 键上是否唯一**。不唯一就先聚合成唯一，再 JOIN：
   ```sql
   LEFT JOIN (
     SELECT order_id, COUNT(*) AS item_cnt, SUM(qty) AS total_qty
     FROM order_items GROUP BY order_id
   ) i ON o.order_id = i.order_id
   ```
2. **JOIN 后立刻核对行数**。JOIN 前后主表行数应当相等（LEFT JOIN 一对一时）。
   多了就是扇出，少了就是 JOIN 键有空值或类型不匹配。
3. **对金额类字段用 `SUM(DISTINCT)` 是错的**——两个真实等额订单会被去掉一个。
   正确做法是修正粒度，而不是打补丁。

**LEFT JOIN 后接 WHERE 右表字段** 会静默退化成 INNER JOIN：

```sql
-- 错：右表无匹配时 b.status 为 NULL，被 WHERE 过滤掉
LEFT JOIN b ON a.id = b.a_id WHERE b.status = 'ok'
-- 对：条件写进 ON
LEFT JOIN b ON a.id = b.a_id AND b.status = 'ok'
```

## 三、窗口函数：分析 SQL 的主力

窗口函数的价值在于**不改变行数的前提下做组内计算**。

```sql
SELECT
  user_id, order_id, created_at, amount,
  ROW_NUMBER()  OVER w                       AS order_seq,     -- 第几单
  LAG(created_at) OVER w                     AS prev_order_at, -- 上一单时间
  SUM(amount)   OVER (PARTITION BY user_id)  AS user_ltv,      -- 用户总额
  amount / SUM(amount) OVER (PARTITION BY user_id) AS amount_share
FROM orders
WINDOW w AS (PARTITION BY user_id ORDER BY created_at)
```

三个必须分清的排名函数：

| 函数 | 并列时 | 用途 |
|------|--------|------|
| `ROW_NUMBER()` | 强制不并列，随机决定顺序 | 去重取一条（**必须给稳定的 ORDER BY**，否则结果不可复现） |
| `RANK()` | 并列同名次，后续跳号（1,1,3） | 竞赛排名 |
| `DENSE_RANK()` | 并列同名次，不跳号（1,1,2） | 分层、分档 |

**滑动窗口的帧定义**是常见坑：默认帧是 `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`，
在有并列值时会把同值行一次性全算进来。要精确控制行数必须显式写 `ROWS`：

```sql
AVG(amount) OVER (ORDER BY dt ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)  -- 7 日移动平均
```

## 四、三个高频分析模式

### 漏斗转化

关键是**同一批用户按步骤顺序推进**，而不是各步骤独立计数（后者会算出下一步比上一步还多）。

```sql
WITH step AS (
  SELECT user_id,
         MIN(CASE WHEN event = 'view'     THEN ts END) AS t_view,
         MIN(CASE WHEN event = 'add_cart' THEN ts END) AS t_cart,
         MIN(CASE WHEN event = 'pay'      THEN ts END) AS t_pay
  FROM events WHERE ts >= '2026-07-01' GROUP BY user_id
)
SELECT
  COUNT(*)                                                        AS s1_view,
  COUNT(CASE WHEN t_cart > t_view THEN 1 END)                     AS s2_cart,
  COUNT(CASE WHEN t_pay  > t_cart THEN 1 END)                     AS s3_pay
FROM step WHERE t_view IS NOT NULL
```

注意 `t_cart > t_view` 的时序约束——不加就会把"先加购后浏览"的乱序数据算进转化。

### 留存（同期群）

```sql
WITH first_day AS (
  SELECT user_id, MIN(DATE(ts)) AS cohort_date FROM events GROUP BY user_id
),
activity AS (
  SELECT DISTINCT e.user_id, f.cohort_date,
         DATE_DIFF(DATE(e.ts), f.cohort_date, DAY) AS day_n
  FROM events e JOIN first_day f USING (user_id)
)
SELECT cohort_date,
       COUNT(DISTINCT CASE WHEN day_n = 0 THEN user_id END) AS d0,
       COUNT(DISTINCT CASE WHEN day_n = 1 THEN user_id END) AS d1,
       COUNT(DISTINCT CASE WHEN day_n = 7 THEN user_id END) AS d7
FROM activity GROUP BY cohort_date ORDER BY cohort_date
```

**同期群表最右下角的数字永远不可信**——最近的 cohort 还没到 7 日观察期，
显示的低留存是数据未成熟，不是真的下降。绘制时应把未成熟单元格留空。

### 同比环比

```sql
SELECT dt, revenue,
       LAG(revenue, 1)  OVER (ORDER BY dt) AS prev_day,
       LAG(revenue, 7)  OVER (ORDER BY dt) AS same_day_last_week,
       revenue / NULLIF(LAG(revenue, 7) OVER (ORDER BY dt), 0) - 1 AS wow
FROM daily_revenue
```

用 `LAG(7)` 而不是 `LAG(1)` 做周环比，可以消除星期几效应。
除法一律套 `NULLIF(x, 0)` 防除零。

## 五、性能：让优化器能用上索引

| 反模式 | 为什么慢 | 改法 |
|--------|---------|------|
| `WHERE DATE(created_at) = '2026-07-01'` | 函数包裹列，索引失效 | `WHERE created_at >= '2026-07-01' AND created_at < '2026-07-02'` |
| `WHERE CAST(user_id AS STRING) = '123'` | 隐式/显式类型转换 | 修正类型，两边类型一致 |
| `WHERE name LIKE '%abc%'` | 前置通配符无法走索引 | 用全文索引或倒排 |
| `SELECT *` | 列存储下扫描全部列，成本翻数倍 | 只选需要的列 |
| `WHERE col NOT IN (子查询)` | 子查询含 NULL 时结果全空，且难优化 | 改 `NOT EXISTS` 或 `LEFT JOIN ... IS NULL` |
| `UNION` | 隐含全局去重排序 | 确定无重复时用 `UNION ALL` |
| `ORDER BY` 无 `LIMIT` | 全量排序 | 探索阶段一律加 LIMIT |
| `COUNT(DISTINCT x)` 大表 | 需要全局去重，内存压力大 | 可接受误差时用 `APPROX_COUNT_DISTINCT` |

**分区裁剪**是列式数仓最大的省钱杠杆：分区键必须出现在 WHERE 里，
且不能被函数包裹。一句忘写分区条件的查询可能比正确写法贵 100 倍。

**看执行计划**：`EXPLAIN`（估算）与 `EXPLAIN ANALYZE`（实际执行）。
重点看三处：
1. 是否有全表扫描（Seq Scan / Full Scan）出现在大表上
2. 估算行数与实际行数是否差一个数量级以上（差太多说明统计信息过期，需要 ANALYZE）
3. JOIN 算法：大表 × 大表用 Hash Join 正常，出现 Nested Loop 通常是灾难

## 六、可读性：CTE 分层，一层一件事

```sql
WITH
-- 1. 限定时间窗与基础过滤（尽早缩小数据量）
base AS (
  SELECT * FROM orders
  WHERE dt BETWEEN '2026-07-01' AND '2026-07-31' AND is_test = FALSE
),
-- 2. 修正粒度
per_user AS (
  SELECT user_id, COUNT(*) AS order_cnt, SUM(amount) AS total_amount
  FROM base GROUP BY user_id
),
-- 3. 计算指标
final AS (
  SELECT
    CASE WHEN order_cnt = 1 THEN '单次' WHEN order_cnt <= 3 THEN '2-3次'
         ELSE '4次以上' END AS segment,
    COUNT(*) AS users, AVG(total_amount) AS avg_amount
  FROM per_user GROUP BY 1
)
SELECT * FROM final ORDER BY users DESC
```

原则：
- **过滤尽早下推**，在第一个 CTE 就把数据量降下来
- **每个 CTE 有注释说明它输出什么粒度**
- 超过 5 层 CTE 就该考虑落成中间表——可读性和调试成本都会失控
- 部分引擎（如老版本 PostgreSQL）CTE 是优化屏障，性能敏感时改子查询或临时表

## 七、交付前的自检清单

- [ ] 输出粒度和预期一致？用 `COUNT(*)` vs `COUNT(DISTINCT 主键)` 验证
- [ ] JOIN 前后主表行数是否变化？变化了能否解释
- [ ] 所有除法都套了 `NULLIF` 防除零？
- [ ] `NULL` 参与的比较和聚合行为确认过？（`NULL != NULL`；`COUNT(col)` 不算 NULL 但 `COUNT(*)` 算）
- [ ] 时间边界是左闭右开？跨月/跨年查询验证过？
- [ ] 时区处理正确？
- [ ] 关键数字能和已知的另一个来源对上（哪怕量级对上）？
- [ ] 跑过 `scripts/sql_lint.py` 静态检查？

> 最后一条最重要：**分析结果一定要和一个独立来源交叉验证**。
> 哪怕只是"总订单数和后台看板对得上"，也比自己算了一遍自己信更可靠。
