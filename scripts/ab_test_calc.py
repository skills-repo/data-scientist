#!/usr/bin/env python3
"""A/B 实验计算器——样本量、显著性、SRM 一站式。

纯标准库（正态分布用 math.erf 实现）。覆盖实验全生命周期的三个计算节点：
开始前算样本量、进行中查 SRM、结束后做检验。
对齐 references/experimentation-ab-testing.md 与 statistical-inference.md。

用法:
    # 1) 开始前：样本量与检验力
    python3 scripts/ab_test_calc.py power --baseline 0.03 --mde 0.003
    python3 scripts/ab_test_calc.py power --baseline 0.03 --mde-relative 0.10 --daily-traffic 50000

    # 2) 进行中：分流健康度（SRM）
    python3 scripts/ab_test_calc.py srm --control 502341 --treatment 497108

    # 3) 结束后：比例型指标检验
    python3 scripts/ab_test_calc.py prop --control 50000 3000 --treatment 50000 3200

    # 3') 结束后：均值型指标检验（Welch）
    python3 scripts/ab_test_calc.py mean --control 5000 128.4 96.2 --treatment 5000 133.1 99.7
"""
from __future__ import annotations

import argparse
import json
import math
import sys

Z95 = 1.959963984540054
Z80 = 0.8416212335729143


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_ppf(p: float) -> float:
    """标准正态分位数，Acklam 有理逼近，精度约 1e-9。"""
    if not 0 < p < 1:
        raise ValueError("p 必须在 (0,1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
                ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q, r = p - 0.5, (p - 0.5) ** 2
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def chi2_sf_df1(x: float) -> float:
    """卡方分布 df=1 的生存函数：P(X > x) = 2 * (1 - Phi(sqrt(x)))。"""
    if x <= 0:
        return 1.0
    return 2 * (1 - norm_cdf(math.sqrt(x)))


# ─────────────────────────────────────────────── 样本量 / 检验力
def cmd_power(args):
    p1 = args.baseline
    if args.mde is not None:
        delta = args.mde
    elif args.mde_relative is not None:
        delta = p1 * args.mde_relative
    else:
        raise SystemExit("需要 --mde（绝对提升）或 --mde-relative（相对提升）")
    p2 = p1 + delta
    if not 0 < p2 < 1:
        raise SystemExit(f"目标比例超出 (0,1)：{p2}")

    z_a = norm_ppf(1 - args.alpha / 2) if args.two_sided else norm_ppf(1 - args.alpha)
    z_b = norm_ppf(args.power)
    p_bar = (p1 + p2) / 2
    # 标准双比例检验样本量（含合并方差项）
    n = ((z_a * math.sqrt(2 * p_bar * (1 - p_bar)) +
          z_b * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) / (delta ** 2)
    n = math.ceil(n)

    out = {"baseline": p1, "target": p2, "mde_absolute": delta,
           "mde_relative": delta / p1, "alpha": args.alpha, "power": args.power,
           "two_sided": args.two_sided, "n_per_group": n, "n_total": n * 2}
    if args.daily_traffic:
        per_group_daily = args.daily_traffic * args.traffic_share / 2
        out["days_needed"] = math.ceil(n / per_group_daily) if per_group_daily else None
    if args.as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    print(f"""
=================== 样本量估算 ===================
基线转化率      : {p1:.4%}
目标转化率      : {p2:.4%}
最小可检测效应  : {delta:.4%} 绝对 / {delta / p1:+.2%} 相对
显著性水平 α    : {args.alpha}（{'双侧' if args.two_sided else '单侧'}）
检验力 power    : {args.power:.0%}
--------------------------------------------------
每组所需样本    : {n:,}
两组合计        : {n * 2:,}""")
    if args.daily_traffic:
        d = out.get("days_needed")
        print(f"日均可用流量    : {args.daily_traffic:,}（实验占比 {args.traffic_share:.0%}）")
        print(f"预计运行天数    : {d} 天" + ("" if d and d >= 14 else "  ← 建议仍至少跑满 14 天，覆盖完整周期"))
    print(f"""--------------------------------------------------
提示：MDE 减半 → 样本量约变为 4 倍（当前减半需 {math.ceil(n * 4):,}/组）。
      样本量不足时不要开实验：power 太低时"没显著"无法解读。
      降方差手段见 references/experimentation-ab-testing.md 第五节（CUPED / 触发分析）。
""")
    return 0


# ─────────────────────────────────────────────── SRM
def cmd_srm(args):
    obs = [args.control, args.treatment]
    ratio = args.ratio
    total = sum(obs)
    exp = [total * ratio / (1 + ratio), total * 1 / (1 + ratio)]
    chi2 = sum((o - e) ** 2 / e for o, e in zip(obs, exp))
    p = chi2_sf_df1(chi2)
    actual = obs[0] / total
    out = {"control": obs[0], "treatment": obs[1], "expected_ratio": ratio,
           "observed_control_share": actual, "chi2": chi2, "p_value": p,
           "srm_detected": p < 0.001}
    if args.as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1 if out["srm_detected"] else 0

    print(f"""
=================== 分流健康度（SRM）===================
对照组          : {obs[0]:,}
实验组          : {obs[1]:,}
期望比例        : {ratio:.4g} : 1  → 对照组应占 {exp[0] / total:.4%}
实际对照组占比  : {actual:.4%}
卡方统计量      : {chi2:.4f}
p 值            : {p:.6g}
--------------------------------------------------------""")
    if out["srm_detected"]:
        print("""判定            : ⚠ 检测到 SRM，实验结果不可信

处置：整个实验必须作废重来，不能"忽略它继续分析"。
      导致比例失衡的机制几乎一定同时污染了指标。
排查顺序：
  1. 实验组代码 bug 导致部分用户崩溃或未上报（最常见）
  2. 分流哈希不均匀，或用了有偏的 ID（自增 ID 取模）
  3. 两组的曝光/触发时机不同
  4. 机器人流量只命中一侧
  5. 重定向或加载耗时差异导致跳出率不同""")
    else:
        print("判定            : ✓ 未检测到 SRM（p ≥ 0.001），分流比例正常")
    print()
    return 1 if out["srm_detected"] else 0


# ─────────────────────────────────────────────── 比例检验
def cmd_prop(args):
    n1, x1 = int(args.control[0]), int(args.control[1])
    n2, x2 = int(args.treatment[0]), int(args.treatment[1])
    p1, p2 = x1 / n1, x2 / n2
    diff = p2 - p1
    p_pool = (x1 + x2) / (n1 + n2)
    se_pool = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    z = diff / se_pool if se_pool else 0.0
    p_value = 2 * (1 - norm_cdf(abs(z)))
    se_unpool = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    z_a = norm_ppf(1 - args.alpha / 2)
    ci = (diff - z_a * se_unpool, diff + z_a * se_unpool)
    rel = diff / p1 if p1 else float("inf")
    rel_ci = (ci[0] / p1, ci[1] / p1) if p1 else (None, None)

    # 期望频数检查
    warns = []
    for label, n, x in (("对照组", n1, x1), ("实验组", n2, x2)):
        if min(x, n - x) < 5:
            warns.append(f"{label}的成功或失败数 < 5，正态近似不可靠，应改用 Fisher 精确检验")
    if min(n1, n2) < 100:
        warns.append("样本量偏小（<100），结论稳健性有限")

    out = {"control": {"n": n1, "x": x1, "rate": p1},
           "treatment": {"n": n2, "x": x2, "rate": p2},
           "abs_diff": diff, "rel_lift": rel, "z": z, "p_value": p_value,
           "ci_abs": ci, "ci_rel": rel_ci, "alpha": args.alpha,
           "significant": p_value < args.alpha, "warnings": warns}
    if args.as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    print(f"""
=================== 比例检验（双比例 z 检验）===================
              样本量        转化数        转化率
对照组     {n1:>10,}  {x1:>12,}   {p1:>10.4%}
实验组     {n2:>10,}  {x2:>12,}   {p2:>10.4%}
----------------------------------------------------------------
绝对差异        : {diff:+.4%}  （{diff * 100:+.4f} pp）
相对提升        : {rel:+.2%}
{int((1 - args.alpha) * 100)}% 置信区间     : [{ci[0]:+.4%}, {ci[1]:+.4%}] 绝对
                  [{rel_ci[0]:+.2%}, {rel_ci[1]:+.2%}] 相对
z 统计量        : {z:.4f}
p 值            : {p_value:.6g}
----------------------------------------------------------------""")
    if out["significant"]:
        print(f"判定            : 统计显著（p < {args.alpha}）")
    else:
        print(f"判定            : 未达显著（p ≥ {args.alpha}）——这是「证据不足」，不是「证明无差异」")
    width = ci[1] - ci[0]
    print(f"""
如何解读（务必按此顺序）：
  1. 先看置信区间而不是 p 值。当前区间宽度 {width:.4%}
  2. 区间下界 {ci[0]:+.4%} 是否仍高于你的最小可接受效应？是 → 值得上线
  3. 区间横跨 0 且很宽 → 样本量不足，继续收集而不是下结论
  4. 区间很窄且贴近 0 → 有把握认为效应可忽略，这也是有价值的结论
  5. 别忘了检查 SRM 与护栏指标；分人群结论需事前声明否则只能算探索性""")
    for w in warns:
        print(f"  ⚠ {w}")
    print()
    return 0


# ─────────────────────────────────────────────── 均值检验
def cmd_mean(args):
    n1, m1, s1 = float(args.control[0]), float(args.control[1]), float(args.control[2])
    n2, m2, s2 = float(args.treatment[0]), float(args.treatment[1]), float(args.treatment[2])
    diff = m2 - m1
    v1, v2 = s1 ** 2 / n1, s2 ** 2 / n2
    se = math.sqrt(v1 + v2)
    t = diff / se if se else 0.0
    # Welch–Satterthwaite 自由度；大样本下用正态近似 p 值
    df = (v1 + v2) ** 2 / (v1 ** 2 / (n1 - 1) + v2 ** 2 / (n2 - 1)) if n1 > 1 and n2 > 1 else 1
    p_value = 2 * (1 - norm_cdf(abs(t)))
    z_a = norm_ppf(1 - args.alpha / 2)
    ci = (diff - z_a * se, diff + z_a * se)
    pooled_sd = math.sqrt(((n1 - 1) * s1 ** 2 + (n2 - 1) * s2 ** 2) / (n1 + n2 - 2)) \
        if n1 + n2 > 2 else 0.0
    cohen_d = diff / pooled_sd if pooled_sd else 0.0

    out = {"control": {"n": n1, "mean": m1, "sd": s1},
           "treatment": {"n": n2, "mean": m2, "sd": s2},
           "diff": diff, "rel": diff / m1 if m1 else None, "t": t, "df": df,
           "p_value": p_value, "ci": ci, "cohens_d": cohen_d,
           "significant": p_value < args.alpha}
    if args.as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    mag = ("极小" if abs(cohen_d) < 0.1 else "小" if abs(cohen_d) < 0.3
           else "中等" if abs(cohen_d) < 0.5 else "大")
    print(f"""
=================== 均值检验（Welch's t 检验）===================
              样本量          均值        标准差
对照组     {n1:>10,.0f}  {m1:>12.4f}  {s1:>12.4f}
实验组     {n2:>10,.0f}  {m2:>12.4f}  {s2:>12.4f}
----------------------------------------------------------------
均值差异        : {diff:+.4f}   相对 {diff / m1 if m1 else float('nan'):+.2%}
{int((1 - args.alpha) * 100)}% 置信区间     : [{ci[0]:+.4f}, {ci[1]:+.4f}]
t 统计量        : {t:.4f}     自由度(Welch) : {df:.1f}
p 值            : {p_value:.6g}
Cohen's d       : {cohen_d:.4f}（效应量：{mag}）
----------------------------------------------------------------
判定            : {'统计显著' if out['significant'] else '未达显著'}（α = {args.alpha}）

注意事项：
  · 默认使用 Welch 检验，不假设两组方差相等——这应当是默认选择
  · 若指标是长尾分布（金额/时长/次数），均值检验收敛慢，几个极端值就能左右结论。
    建议同时报告中位数差异，或对指标 winsorize 至 P99 后重算
  · p 值大不代表无差异；请以置信区间宽度和业务最小可接受效应共同判断
""")
    return 0


def main():
    ap = argparse.ArgumentParser(description="A/B 实验计算器：样本量 / SRM / 显著性检验")
    ap.add_argument("--json", action="store_true", dest="as_json")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("power", help="样本量与检验力估算")
    p1.add_argument("--baseline", type=float, required=True, help="基线转化率，如 0.03")
    p1.add_argument("--mde", type=float, help="最小可检测效应（绝对），如 0.003")
    p1.add_argument("--mde-relative", type=float, help="最小可检测效应（相对），如 0.10")
    p1.add_argument("--alpha", type=float, default=0.05)
    p1.add_argument("--power", type=float, default=0.8)
    p1.add_argument("--two-sided", action="store_true", default=True)
    p1.add_argument("--daily-traffic", type=int, help="日均可用流量（总量）")
    p1.add_argument("--traffic-share", type=float, default=1.0, help="分给本实验的流量比例")
    p1.set_defaults(func=cmd_power)

    p2 = sub.add_parser("srm", help="样本比例不匹配检查")
    p2.add_argument("--control", type=int, required=True)
    p2.add_argument("--treatment", type=int, required=True)
    p2.add_argument("--ratio", type=float, default=1.0, help="期望的 control:treatment 比例")
    p2.set_defaults(func=cmd_srm)

    p3 = sub.add_parser("prop", help="比例型指标检验")
    p3.add_argument("--control", nargs=2, required=True, metavar=("N", "X"))
    p3.add_argument("--treatment", nargs=2, required=True, metavar=("N", "X"))
    p3.add_argument("--alpha", type=float, default=0.05)
    p3.set_defaults(func=cmd_prop)

    p4 = sub.add_parser("mean", help="均值型指标检验（Welch）")
    p4.add_argument("--control", nargs=3, required=True, metavar=("N", "MEAN", "SD"))
    p4.add_argument("--treatment", nargs=3, required=True, metavar=("N", "MEAN", "SD"))
    p4.add_argument("--alpha", type=float, default=0.05)
    p4.set_defaults(func=cmd_mean)

    args = ap.parse_args()
    try:
        return args.func(args)
    except (ValueError, ZeroDivisionError) as exc:
        print(f"计算失败: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
