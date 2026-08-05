#!/usr/bin/env python3
"""数据集画像——CSV/TSV 一键体检。

纯标准库，不需要 pandas。对每一列做类型推断、缺失统计、基数分析、
数值分布、异常值检测、可疑值识别，并给出全局风险提示。
对齐 references/exploratory-analysis.md 的"数据画像"一节。

用法:
    python3 scripts/profile_dataset.py data.csv
    python3 scripts/profile_dataset.py data.tsv --sep '\\t' --max-rows 200000
    python3 scripts/profile_dataset.py data.csv --json > profile.json
    python3 scripts/profile_dataset.py data.csv --column amount
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics as st
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

# 伪装成正常值的缺失
SENTINELS = {"", "na", "n/a", "nan", "null", "none", "nil", "-", "--", "未知", "无", "不详",
             "unknown", "#n/a", "\\n", "9999", "-9999", "-1", "0000-00-00"}
DATE_PATTERNS = [
    (re.compile(r"^\d{4}-\d{2}-\d{2}$"), "date(YYYY-MM-DD)"),
    (re.compile(r"^\d{4}/\d{1,2}/\d{1,2}$"), "date(YYYY/M/D)"),
    (re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$"), "date(ambiguous D/M or M/D)"),
    (re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}"), "datetime"),
    (re.compile(r"^\d{8}$"), "date(YYYYMMDD?)"),
]
NUM_RE = re.compile(r"^-?[\d,]*\.?\d+(?:[eE][-+]?\d+)?$")
BOOL_TOKENS = {"true", "false", "t", "f", "yes", "no", "y", "n", "是", "否", "0", "1"}


def is_missing(v: str) -> bool:
    return v.strip().lower() in SENTINELS


def is_disguised(v: str) -> bool:
    """真空之外的哨兵值——它们被当成缺失，但原文件里是"有值"的，必须回报给用户。"""
    s = v.strip()
    return bool(s) and s.lower() in SENTINELS


DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y", "%Y%m%d",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M")


def valid_date(s: str) -> bool:
    """校验字符串是否为真实存在的日历日期（2026-13-45 这类要判假）。"""
    s = s.strip().rstrip("Z")
    for fmt in DATE_FORMATS:
        try:
            datetime.strptime(s, fmt)
            return True
        except ValueError:
            continue
    return False


def to_num(v: str):
    s = v.strip().replace(",", "")
    if s.startswith("(") and s.endswith(")"):   # 会计负数写法
        s = "-" + s[1:-1]
    s = s.rstrip("%")
    try:
        return float(s)
    except ValueError:
        return None


def quantile(sorted_vals, q):
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = (len(sorted_vals) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return sorted_vals[int(pos)]
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def infer_type(values):
    """values: 非缺失的原始字符串列表"""
    if not values:
        return "empty"
    sample = values[: min(len(values), 5000)]
    n = len(sample)
    nums = sum(1 for v in sample if NUM_RE.match(v.strip().replace(",", "")))
    if nums / n > 0.95:
        ints = sum(1 for v in sample if re.fullmatch(r"-?[\d,]+", v.strip()))
        return "integer" if ints / n > 0.95 else "float"
    for pat, label in DATE_PATTERNS:
        if sum(1 for v in sample if pat.match(v.strip())) / n > 0.9:
            return label
    if len({v.strip().lower() for v in sample}) <= 2 and \
            all(v.strip().lower() in BOOL_TOKENS for v in sample):
        return "boolean"
    return "string"


def profile_column(name, raw_values, total_rows):
    present = [v for v in raw_values if not is_missing(v)]
    missing = total_rows - len(present)
    col = {
        "name": name,
        "missing": missing,
        "missing_rate": missing / total_rows if total_rows else 0.0,
        "present": len(present),
    }
    counter = Counter(v.strip() for v in present)
    col["unique"] = len(counter)
    col["unique_rate"] = len(counter) / len(present) if present else 0.0
    col["top_values"] = counter.most_common(5)
    col["dtype"] = infer_type(present)

    flags = []
    if col["unique"] == 1 and present:
        flags.append("常量列（唯一值仅 1 个，通常无分析价值）")
    if col["unique_rate"] > 0.95 and len(present) > 50:
        flags.append("高基数（近似唯一，多半是 ID/时间戳，不可作为类别特征）")
    if col["missing_rate"] > 0.5:
        flags.append("高缺失（>50%，使用前需确认缺失代表什么）")
    elif col["missing_rate"] > 0.3:
        flags.append("缺失偏高（>30%）")
    if not present:
        flags.append("全空列")

    # 伪装缺失：原文件里"有值"、但被本脚本按哨兵计入缺失的那些值。
    # 必须显式回报，否则用户看到缺失率会对不上原始数据。
    disguised = Counter(v.strip() for v in raw_values if is_disguised(v))
    col["disguised_missing"] = dict(disguised)
    if disguised:
        detail = "、".join(f"{v!r}×{c}" for v, c in disguised.most_common(5))
        flags.append(f"伪装缺失值已计入缺失: {detail}"
                     f"（真空仅 {missing - sum(disguised.values())} 个，落库前需统一成 NULL）")

    # 文本形态问题
    if col["dtype"] == "string" and present:
        ws = sum(1 for v in present if v != v.strip())
        case_dup = len({v.strip().lower() for v in present}) < len({v.strip() for v in present})
        if ws:
            flags.append(f"{ws} 个值含首尾空格（会导致分组统计被拆开）")
        if case_dup:
            flags.append("存在仅大小写不同的重复值（分组前需统一）")
        lens = [len(v) for v in present]
        col["len_min"], col["len_max"] = min(lens), max(lens)

    # 数值统计
    if col["dtype"] in ("integer", "float"):
        nums = [x for x in (to_num(v) for v in present) if x is not None]
        if nums:
            s = sorted(nums)
            q1, q3 = quantile(s, 0.25), quantile(s, 0.75)
            iqr = q3 - q1
            lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outliers = [x for x in s if x < lo or x > hi]
            col["stats"] = {
                "min": s[0], "p01": quantile(s, 0.01), "q1": q1,
                "median": quantile(s, 0.5), "mean": st.fmean(s), "q3": q3,
                "p99": quantile(s, 0.99), "max": s[-1],
                "std": st.pstdev(s) if len(s) > 1 else 0.0,
                "zeros": sum(1 for x in s if x == 0),
                "negatives": sum(1 for x in s if x < 0),
                "outliers_iqr": len(outliers),
                "outlier_rate": len(outliers) / len(s),
            }
            mean, med = col["stats"]["mean"], col["stats"]["median"]
            if med and abs(mean - med) / (abs(med) + 1e-9) > 0.5:
                flags.append("均值显著偏离中位数（长尾分布，用中位数描述，不要用均值）")
            if col["stats"]["std"] == 0:
                flags.append("零方差（所有值相同）")
            if col["stats"]["outlier_rate"] > 0.05:
                flags.append(f"IQR 异常值占比 {col['stats']['outlier_rate']:.1%}"
                             f"（{len(outliers)} 个，分布可能非单峰，先看直方图）")
            # 比例之外单独看极值倍数：小样本里 1 个离群点占比不高，但足以毁掉均值
            if iqr > 0 and s[-1] > hi:
                times = (s[-1] - q3) / iqr
                if times >= 3:
                    flags.append(f"最大值 {s[-1]:.4g} 超出 IQR 上界 {times:.1f} 倍"
                                 f"（中位数仅 {col['stats']['median']:.4g}，先确认是真实业务值还是脏数据）")
            if iqr > 0 and s[0] < lo:
                times = (q1 - s[0]) / iqr
                if times >= 3:
                    flags.append(f"最小值 {s[0]:.4g} 低于 IQR 下界 {times:.1f} 倍（同上需确认）")
            if col["stats"]["zeros"] and col["stats"]["zeros"] / len(s) > 0.2:
                flags.append(f"{col['stats']['zeros']} 个零值（占 {col['stats']['zeros'] / len(s):.1%}），"
                             f"确认 0 是真实取值还是缺失的替身")
            if col["stats"]["negatives"] and re.search(
                    r"(?i)(amount|price|qty|count|num|age|金额|数量|年龄)", name):
                flags.append(f"疑似不应为负的字段出现 {col['stats']['negatives']} 个负值")

    # 日期列：格式对不代表日期真实存在（2026-13-45 能过正则，过不了日历）
    if col["dtype"].startswith(("date", "datetime")) and present:
        bad = [v.strip() for v in present if not valid_date(v)]
        col["invalid_dates"] = len(bad)
        if bad:
            flags.append(f"{len(bad)} 个值格式像日期但不是真实日期，例: {bad[:3]}")
        good = sorted(v.strip() for v in present if valid_date(v))
        if good:
            col["date_min"], col["date_max"] = good[0], good[-1]

    # 敏感字段提示
    if re.search(r"(?i)(phone|mobile|email|id_card|idcard|passport|address|身份证|手机|邮箱|地址)", name):
        flags.append("疑似个人敏感信息列，输出前需脱敏")

    col["flags"] = flags
    return col


def profile(path: Path, sep: str, max_rows: int, encoding: str):
    with path.open("r", encoding=encoding, errors="replace", newline="") as fh:
        reader = csv.reader(fh, delimiter=sep)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError("文件为空")
        header = [h.strip() or f"col_{i}" for i, h in enumerate(header)]
        cols = {h: [] for h in header}
        dup_header = [h for h, c in Counter(header).items() if c > 1]
        rows, ragged, row_hashes = 0, 0, Counter()
        for rec in reader:
            if max_rows and rows >= max_rows:
                break
            if len(rec) != len(header):
                ragged += 1
                rec = (rec + [""] * len(header))[: len(header)]
            for h, v in zip(header, rec):
                cols[h].append(v)
            row_hashes[tuple(rec)] += 1
            rows += 1

    dup_rows = sum(c - 1 for c in row_hashes.values() if c > 1)
    result = {
        "file": str(path),
        "rows_scanned": rows,
        "columns": len(header),
        "ragged_rows": ragged,
        "duplicate_rows": dup_rows,
        "duplicate_header_names": dup_header,
        "column_profiles": [profile_column(h, cols[h], rows) for h in header],
    }

    # 候选主键：唯一且无缺失
    result["primary_key_candidates"] = [
        c["name"] for c in result["column_profiles"]
        if c["missing"] == 0 and c["present"] == rows and c["unique"] == rows and rows > 0]
    return result


def render(r):
    print(f"\n数据集画像: {r['file']}")
    print("=" * 92)
    print(f"扫描行数 {r['rows_scanned']:,}   列数 {r['columns']}   "
          f"完全重复行 {r['duplicate_rows']:,}   列数不齐的行 {r['ragged_rows']:,}")
    if r["duplicate_header_names"]:
        print(f"!! 表头重复: {r['duplicate_header_names']}（下游按名取列会取错）")
    print(f"候选主键: {r['primary_key_candidates'] or '无（没有既唯一又无缺失的列）'}")

    print("\n" + "-" * 92)
    print(f"{'列名':<24}{'类型':<20}{'缺失率':>8}{'唯一值':>10}{'  概要'}")
    print("-" * 92)
    for c in r["column_profiles"]:
        summary = ""
        if "stats" in c:
            s = c["stats"]
            summary = (f"中位 {s['median']:.4g}  均值 {s['mean']:.4g}  "
                       f"[{s['min']:.4g}, {s['max']:.4g}]")
        elif "date_min" in c:
            summary = f"{c['date_min']} → {c['date_max']}"
            if c.get("invalid_dates"):
                summary += f"  (+{c['invalid_dates']} 个非法日期)"
        elif c["top_values"]:
            top = c["top_values"][0]
            summary = f"最常见 {top[0][:18]!r} × {top[1]}"
        name = c["name"][:22]
        pad = 24 - sum(2 if ord(ch) > 127 else 1 for ch in name)
        print(f"{name}{' ' * max(1, pad)}{c['dtype']:<20}"
              f"{c['missing_rate'] * 100:>7.1f}%{c['unique']:>10,}  {summary}")

    flagged = [c for c in r["column_profiles"] if c["flags"]]
    if flagged:
        print("\n" + "-" * 92)
        print("需要关注的列")
        print("-" * 92)
        for c in flagged:
            print(f"\n▸ {c['name']}  ({c['dtype']})")
            for f in c["flags"]:
                print(f"    · {f}")
    print("\n" + "-" * 92)
    print("下一步建议：确认候选主键 → 核对高缺失列的缺失含义 → 对长尾数值列改用中位数/分位数 →"
          "\n            把伪装缺失值统一成真正的缺失 → 再进入分析")
    print()


def main():
    ap = argparse.ArgumentParser(description="CSV/TSV 数据集画像（零依赖）")
    ap.add_argument("file")
    ap.add_argument("--sep", default=",", help="分隔符，默认 ','；TSV 用 '\\t'")
    ap.add_argument("--encoding", default="utf-8-sig")
    ap.add_argument("--max-rows", type=int, default=500000, help="最多扫描行数，0 表示不限")
    ap.add_argument("--column", help="只看某一列的详细信息")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(f"找不到文件: {path}", file=sys.stderr)
        return 2
    sep = "\t" if args.sep in ("\\t", "tab") else args.sep

    try:
        r = profile(path, sep, args.max_rows, args.encoding)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.column:
        col = next((c for c in r["column_profiles"] if c["name"] == args.column), None)
        if not col:
            print(f"列不存在: {args.column}", file=sys.stderr)
            return 2
        print(json.dumps(col, ensure_ascii=False, indent=2, default=float))
        return 0
    if args.as_json:
        print(json.dumps(r, ensure_ascii=False, indent=2, default=float))
        return 0
    render(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
