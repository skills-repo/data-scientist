#!/usr/bin/env python3
"""数据质量断言检查——把清洗规则固化成可重复执行的门禁。

纯标准库。规则用 JSON 描述（见 assets/data-quality-rules.json），
硬断言失败退出码为 1，可直接接进数据管道阻断下游。
对齐 references/data-cleaning.md 与 data-pipeline.md。

用法:
    python3 scripts/data_quality_check.py data.csv --rules rules.json
    python3 scripts/data_quality_check.py data.csv            # 无规则时只跑通用检查
    python3 scripts/data_quality_check.py data.csv --rules rules.json --json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

DEFAULT_MISSING = {"", "na", "n/a", "nan", "null", "none", "nil"}
SEV_ORDER = {"fail": 0, "warn": 1, "pass": 2}

# 门禁不猜哨兵值：默认只认真正的空/null 字面量。
# 本表若把 "unknown"/"未知"/-1 当缺失用，在规则里显式写 missing_tokens 声明，
# 否则它们会被当作正常取值参与枚举、缺失率、非空等所有检查。
MISSING = set(DEFAULT_MISSING)


def set_missing_tokens(tokens):
    """用规则里的 missing_tokens 覆盖默认哨兵集合（追加，不替换默认值）。"""
    global MISSING
    MISSING = set(DEFAULT_MISSING) | {str(t).strip().lower() for t in (tokens or [])}


def is_missing(v: str) -> bool:
    return v.strip().lower() in MISSING


def real_cols(mapping):
    """遍历规则字典时跳过 _ 开头的注释键（模板里的 _comment 不是列名）。"""
    return [(k, v) for k, v in (mapping or {}).items() if not str(k).startswith("_")]


def real_items(seq):
    """遍历规则列表时跳过 _ 开头的注释项。"""
    return [x for x in (seq or []) if not (isinstance(x, str) and x.startswith("_"))]


def to_num(v: str):
    try:
        return float(v.strip().replace(",", ""))
    except (ValueError, AttributeError):
        return None


class Report:
    def __init__(self):
        self.items = []

    def add(self, severity, check, detail, sample=None):
        self.items.append({"severity": severity, "check": check,
                           "detail": detail, "sample": sample or []})

    def ok(self, check, detail):
        self.add("pass", check, detail)

    @property
    def failed(self):
        return sum(1 for i in self.items if i["severity"] == "fail")

    @property
    def warned(self):
        return sum(1 for i in self.items if i["severity"] == "warn")


def load_table(path: Path, sep: str, encoding: str):
    with path.open("r", encoding=encoding, errors="replace", newline="") as fh:
        reader = csv.reader(fh, delimiter=sep)
        header = next(reader)
        header = [h.strip() for h in header]
        rows = [r for r in reader]
    return header, rows


def col_values(header, rows, name):
    if name not in header:
        return None
    i = header.index(name)
    return [(r[i] if i < len(r) else "") for r in rows]


def run_checks(header, rows, rules, rep: Report):
    n = len(rows)
    set_missing_tokens((rules or {}).get("missing_tokens"))
    extra = sorted(MISSING - DEFAULT_MISSING)
    if extra:
        rep.ok("哨兵值声明", f"除空值外，另将 {extra} 视为缺失")

    # ── 通用检查（无需规则）────────────────────────────────────────
    dup_cols = [h for h, c in Counter(header).items() if c > 1]
    if dup_cols:
        rep.add("fail", "表头唯一性", f"存在重复列名 {dup_cols}，按列名取数会取错")
    else:
        rep.ok("表头唯一性", "无重复列名")

    ragged = sum(1 for r in rows if len(r) != len(header))
    if ragged:
        rep.add("fail", "列数一致性", f"{ragged} 行的字段数与表头不一致，解析可能错位")
    else:
        rep.ok("列数一致性", f"全部 {n:,} 行字段数一致")

    counts = Counter(tuple(r) for r in rows)
    dup_rows = sum(c - 1 for c in counts.values() if c > 1)
    if dup_rows:
        sev = "fail" if dup_rows / max(n, 1) > 0.01 else "warn"
        rep.add(sev, "完全重复行", f"{dup_rows:,} 行完全重复（占 {dup_rows / max(n, 1):.2%}）")
    else:
        rep.ok("完全重复行", "无完全重复行")

    empty_cols = [h for h in set(header)
                  if all(is_missing(v) for v in (col_values(header, rows, h) or []))]
    if empty_cols:
        rep.add("warn", "全空列", f"以下列全为空：{sorted(empty_cols)}")

    if not rules:
        rep.add("warn", "规则文件", "未提供 --rules，仅执行了通用检查。"
                                    "建议基于 assets/data-quality-rules.json 定义业务断言")
        return

    # ── 行数区间 ──────────────────────────────────────────────────
    rc = rules.get("row_count")
    if rc:
        lo, hi = rc.get("min"), rc.get("max")
        if lo is not None and n < lo:
            rep.add("fail", "行数下限", f"实际 {n:,} 行 < 期望下限 {lo:,}，疑似上游数据缺失")
        elif hi is not None and n > hi:
            rep.add("fail", "行数上限", f"实际 {n:,} 行 > 期望上限 {hi:,}，疑似重复加载")
        else:
            rep.ok("行数区间", f"{n:,} 行，在 [{lo}, {hi}] 内")

    # ── 必需列存在 ────────────────────────────────────────────────
    required = real_items(rules.get("required_columns"))
    miss = [c for c in required if c not in header]
    if miss:
        rep.add("fail", "必需列", f"缺少列 {miss}（schema 变更？字段被改名？）")
    elif required:
        rep.ok("必需列", f"{len(required)} 个必需列齐全")

    # ── 主键唯一且非空 ────────────────────────────────────────────
    pk = rules.get("primary_key")
    if pk:
        cols = [col_values(header, rows, c) for c in pk]
        if any(c is None for c in cols):
            rep.add("fail", "主键", f"主键列 {pk} 中有列在表里不存在")
        else:
            keys = list(zip(*cols))
            null_keys = sum(1 for k in keys if any(is_missing(v) for v in k))
            kc = Counter(keys)
            dups = [(k, c) for k, c in kc.items() if c > 1]
            if null_keys:
                rep.add("fail", "主键非空", f"{null_keys:,} 行主键含空值")
            if dups:
                rep.add("fail", "主键唯一", f"{len(dups):,} 个主键值重复（共多出 "
                                            f"{sum(c - 1 for _, c in dups):,} 行）",
                        [{"key": list(k), "count": c} for k, c in dups[:5]])
            if not null_keys and not dups:
                rep.ok("主键", f"{pk} 唯一且非空")

    # ── 非空约束 ──────────────────────────────────────────────────
    for c in real_items(rules.get("not_null")):
        vals = col_values(header, rows, c)
        if vals is None:
            rep.add("fail", f"非空[{c}]", "规则引用了表中不存在的列（改名了？还是规则该删）")
            continue
        bad = sum(1 for v in vals if is_missing(v))
        if bad:
            rep.add("fail", f"非空[{c}]", f"{bad:,} 行为空（占 {bad / max(n, 1):.2%}）")
        else:
            rep.ok(f"非空[{c}]", "无空值")

    # ── 缺失率上限（软约束）────────────────────────────────────────
    for c, thr in real_cols(rules.get("missing_rate_max")):
        vals = col_values(header, rows, c)
        if vals is None:
            rep.add("warn", f"缺失率[{c}]", "规则引用了表中不存在的列")
            continue
        rate = sum(1 for v in vals if is_missing(v)) / max(n, 1)
        if rate > thr:
            rep.add("warn", f"缺失率[{c}]", f"{rate:.2%} 超过阈值 {thr:.2%}")
        else:
            rep.ok(f"缺失率[{c}]", f"{rate:.2%} ≤ {thr:.2%}")

    # ── 唯一性（非主键）────────────────────────────────────────────
    for c in real_items(rules.get("unique")):
        vals = col_values(header, rows, c)
        if vals is None:
            continue
        present = [v for v in vals if not is_missing(v)]
        d = len(present) - len(set(present))
        if d:
            rep.add("fail", f"唯一[{c}]", f"{d:,} 个重复值")
        else:
            rep.ok(f"唯一[{c}]", "取值唯一")

    # ── 数值区间 ──────────────────────────────────────────────────
    for c, spec in real_cols(rules.get("ranges")):
        vals = col_values(header, rows, c)
        if vals is None:
            rep.add("fail", f"区间[{c}]", "规则引用了表中不存在的列（改名了？还是规则该删）")
            continue
        lo, hi = spec.get("min"), spec.get("max")
        bad, unparsed, samples = 0, 0, []
        for v in vals:
            if is_missing(v):
                continue
            x = to_num(v)
            if x is None:
                unparsed += 1
                if len(samples) < 5:
                    samples.append(v)
                continue
            if (lo is not None and x < lo) or (hi is not None and x > hi):
                bad += 1
                if len(samples) < 5:
                    samples.append(v)
        if unparsed:
            rep.add("fail", f"区间[{c}]", f"{unparsed:,} 个值无法解析为数值", samples)
        if bad:
            rep.add("fail", f"区间[{c}]", f"{bad:,} 个值超出 [{lo}, {hi}]", samples)
        if not bad and not unparsed:
            rep.ok(f"区间[{c}]", f"全部落在 [{lo}, {hi}]")

    # ── 枚举白名单 ────────────────────────────────────────────────
    for c, allowed in real_cols(rules.get("allowed_values")):
        vals = col_values(header, rows, c)
        if vals is None:
            rep.add("fail", f"枚举[{c}]", "规则引用了表中不存在的列（改名了？还是规则该删）")
            continue
        allow = set(allowed)
        unexpected = Counter(v.strip() for v in vals
                             if not is_missing(v) and v.strip() not in allow)
        if unexpected:
            rep.add("fail", f"枚举[{c}]", f"出现 {len(unexpected)} 个白名单外的值",
                    unexpected.most_common(5))
        else:
            rep.ok(f"枚举[{c}]", f"全部取值在白名单内（{len(allow)} 项）")

    # ── 正则格式 ──────────────────────────────────────────────────
    for c, pattern in real_cols(rules.get("regex")):
        vals = col_values(header, rows, c)
        if vals is None:
            rep.add("fail", f"格式[{c}]", "规则引用了表中不存在的列（改名了？还是规则该删）")
            continue
        rx = re.compile(pattern)
        bad = [v for v in vals if not is_missing(v) and not rx.match(v.strip())]
        if bad:
            rep.add("fail", f"格式[{c}]", f"{len(bad):,} 个值不匹配 /{pattern}/", bad[:5])
        else:
            rep.ok(f"格式[{c}]", "全部匹配")

    # ── 日期格式与范围 ────────────────────────────────────────────
    for c, spec in real_cols(rules.get("dates")):
        vals = col_values(header, rows, c)
        if vals is None:
            rep.add("fail", f"日期[{c}]", "规则引用了表中不存在的列（改名了？还是规则该删）")
            continue
        fmt = spec.get("format", "%Y-%m-%d")
        lo = datetime.strptime(spec["min"], fmt) if spec.get("min") else None
        hi = datetime.strptime(spec["max"], fmt) if spec.get("max") else None
        bad_fmt, out_range, samples = 0, 0, []
        for v in vals:
            if is_missing(v):
                continue
            try:
                d = datetime.strptime(v.strip(), fmt)
            except ValueError:
                bad_fmt += 1
                if len(samples) < 5:
                    samples.append(v)
                continue
            if (lo and d < lo) or (hi and d > hi):
                out_range += 1
                if len(samples) < 5:
                    samples.append(v)
        if bad_fmt:
            rep.add("fail", f"日期[{c}]", f"{bad_fmt:,} 个值不符合格式 {fmt}", samples)
        if out_range:
            rep.add("fail", f"日期[{c}]", f"{out_range:,} 个日期超出 "
                                          f"[{spec.get('min')}, {spec.get('max')}]", samples)
        if not bad_fmt and not out_range:
            rep.ok(f"日期[{c}]", "格式与范围均正确")

    # ── 跨字段时间顺序 ────────────────────────────────────────────
    for pair in real_items(rules.get("ordering")):
        early, late = pair[0], pair[1]
        ve, vl = col_values(header, rows, early), col_values(header, rows, late)
        if ve is None or vl is None:
            rep.add("fail", f"时序[{early}≤{late}]", "规则引用了表中不存在的列（改名了？还是规则该删）")
            continue
        bad = sum(1 for a, b in zip(ve, vl)
                  if not is_missing(a) and not is_missing(b) and a.strip() > b.strip())
        if bad:
            rep.add("fail", f"时序[{early}≤{late}]", f"{bad:,} 行违反时间先后（按字符串比较，"
                                                     f"要求 ISO 格式）")
        else:
            rep.ok(f"时序[{early}≤{late}]", "全部满足")

    # ── 跨字段数值关系 ────────────────────────────────────────────
    for rule in real_items(rules.get("comparisons")):
        left, op, right = rule["left"], rule["op"], rule["right"]
        vl, vr = col_values(header, rows, left), col_values(header, rows, right)
        if vl is None or vr is None:
            rep.add("fail", f"关系[{left}{op}{right}]", "规则引用了表中不存在的列（改名了？还是规则该删）")
            continue
        ops = {"<=": lambda a, b: a <= b, "<": lambda a, b: a < b,
               ">=": lambda a, b: a >= b, ">": lambda a, b: a > b,
               "==": lambda a, b: a == b}
        fn = ops.get(op)
        if not fn:
            rep.add("warn", f"关系[{left}{op}{right}]", f"不支持的运算符 {op}")
            continue
        bad = 0
        for a, b in zip(vl, vr):
            x, y = to_num(a), to_num(b)
            if x is None or y is None:
                continue
            if not fn(x, y):
                bad += 1
        if bad:
            rep.add("fail", f"关系[{left}{op}{right}]", f"{bad:,} 行违反约束")
        else:
            rep.ok(f"关系[{left}{op}{right}]", "全部满足")


def main():
    ap = argparse.ArgumentParser(description="数据质量断言检查（零依赖）")
    ap.add_argument("file")
    ap.add_argument("--rules", help="JSON 规则文件路径")
    ap.add_argument("--sep", default=",")
    ap.add_argument("--encoding", default="utf-8-sig")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--warn-as-error", action="store_true", help="warn 也计入失败")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(f"找不到文件: {path}", file=sys.stderr)
        return 2
    rules = {}
    if args.rules:
        rp = Path(args.rules)
        if not rp.is_file():
            print(f"找不到规则文件: {rp}", file=sys.stderr)
            return 2
        rules = json.loads(rp.read_text(encoding="utf-8"))

    sep = "\t" if args.sep in ("\\t", "tab") else args.sep
    header, rows = load_table(path, sep, args.encoding)
    rep = Report()
    run_checks(header, rows, rules, rep)

    if args.as_json:
        print(json.dumps({"file": str(path), "rows": len(rows),
                          "failed": rep.failed, "warned": rep.warned,
                          "results": rep.items}, ensure_ascii=False, indent=2))
    else:
        icon = {"fail": "[FAIL]", "warn": "[WARN]", "pass": "[ OK ]"}
        print(f"\n数据质量检查: {path}   {len(rows):,} 行 × {len(header)} 列")
        if args.rules:
            print(f"规则文件: {args.rules}")
        print("=" * 84)
        for it in sorted(rep.items, key=lambda x: SEV_ORDER[x["severity"]]):
            print(f"{icon[it['severity']]} {it['check']}: {it['detail']}")
            if it["sample"]:
                print(f"        样例: {it['sample']}")
        print("-" * 84)
        print(f"失败 {rep.failed} / 警告 {rep.warned} / "
              f"通过 {sum(1 for i in rep.items if i['severity'] == 'pass')}")
        if rep.failed:
            print("\n硬断言失败——按 data-pipeline.md 的约定，此时应阻断下游，不要让脏数据扩散。")
        print()

    if rep.failed or (args.warn_as_error and rep.warned):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
