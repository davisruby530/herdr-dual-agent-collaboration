#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_multiset_integrity.py
===========================
大规模数据流水线多重集守恒与分母闭合审计工具 (Multiset Integrity & Denominator Accounting Auditor)

核心特性：
1. 彻底解决数据清洗与实证统计中“样本分母模糊”、“数据静默丢失”和“非法重复计数”问题。
2. 严格核算数学守恒闭环：
       全量输入原始样本集 (N_raw) == 规则有效处理集 (N_valid) + 显式合法排除集 (N_excluded)
3. 严格核验三大数学公理：
   - 全覆盖公理（无静默丢弃）：input_ids == valid_ids ∪ excluded_ids
   - 互斥公理（无重叠归类）：valid_ids ∩ excluded_ids == ∅
   - 唯一性公理（无重复键）：len(ids) == len(set(ids))

用法：
    python audit_multiset_integrity.py --raw <file> --valid <file> [--excluded <file>] [--id-key id] [--report <file>]

输入文件支持 JSON、JSONL 或纯文本每行一个 ID (TXT)。
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Set, List, Dict, Any


class MissingIdError(ValueError):
    """记录缺少唯一 ID。缺 ID 的记录无法对账，必须显式失败而不是当作空串放行。"""


def record_id(item: Any, id_key: str, filepath: Path, position: int) -> str:
    """取记录的唯一 ID；依次尝试 id_key、paper_id、doc_id，全部缺失或为空则报错"""
    if not isinstance(item, dict):
        value = item
    else:
        value = next(
            (item[k] for k in (id_key, "paper_id", "doc_id") if item.get(k) not in (None, "")),
            None,
        )
    if value is None or str(value) == "":
        raise MissingIdError(f"{filepath} 第 {position} 条记录缺少唯一 ID 字段 '{id_key}'")
    return str(value)


def extract_ids_from_file(filepath: Path, id_key: str = "id") -> List[str]:
    """通用提取文件中的唯一标识符列表 (保持原始出现顺序)"""
    if not filepath.exists():
        raise FileNotFoundError(f"文件不存在: {filepath}")

    ids = []
    suffix = filepath.suffix.lower()

    if suffix == ".jsonl":
        with open(filepath, "r", encoding="utf-8") as f:
            position = 0
            for line in f:
                line = line.strip()
                if line:
                    position += 1
                    ids.append(record_id(json.loads(line), id_key, filepath, position))
    elif suffix == ".json":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get("items"), list):
                data = data["items"]
            if isinstance(data, list):
                ids = [record_id(item, id_key, filepath, i) for i, item in enumerate(data, 1)]
            elif isinstance(data, dict):
                # 字典的键本身就是 ID
                ids = [record_id(k, id_key, filepath, i) for i, k in enumerate(data.keys(), 1)]
    else:
        # TXT 每行一个 ID
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                val = line.strip()
                if val and not val.startswith("#"):
                    ids.append(val)

    return ids


def audit_multiset(
    raw_file: Path,
    valid_file: Path,
    excluded_file: Path = None,
    id_key: str = "id",
    report_output: Path = None
) -> int:
    print(f"[*] 启动全量输入输出多重集对账审计:")
    print(f"    - 全量输入源 (Raw): {raw_file}")
    print(f"    - 有效处理集 (Valid): {valid_file}")
    if excluded_file:
        print(f"    - 合法排除集 (Excluded): {excluded_file}")

    try:
        raw_ids = extract_ids_from_file(raw_file, id_key=id_key)
        valid_ids = extract_ids_from_file(valid_file, id_key=id_key)
        excluded_ids = extract_ids_from_file(excluded_file, id_key=id_key) if excluded_file else []
    except MissingIdError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return 1

    n_raw = len(raw_ids)
    n_valid = len(valid_ids)
    n_excluded = len(excluded_ids)

    set_raw = set(raw_ids)
    set_valid = set(valid_ids)
    set_excluded = set(excluded_ids)

    # 1. 唯一性公理检查
    raw_dups = n_raw - len(set_raw)
    valid_dups = n_valid - len(set_valid)
    excluded_dups = n_excluded - len(set_excluded)

    # 2. 互斥性公理检查 (valid 与 excluded 不能重叠)
    overlap = set_valid.intersection(set_excluded)

    # 3. 守恒闭合检查
    accounted_set = set_valid.union(set_excluded)
    missing_ids = set_raw - accounted_set       # 静默丢失
    unexpected_ids = accounted_set - set_raw    # 凭空多出

    # 4. 计数守恒：在无重复的前提下，N_raw == N_valid + N_excluded
    count_balanced = n_raw == n_valid + n_excluded

    is_conserved = (
        len(missing_ids) == 0
        and len(unexpected_ids) == 0
        and len(overlap) == 0
        and raw_dups == 0
        and valid_dups == 0
        and excluded_dups == 0
        and count_balanced
    )

    print("=" * 65)
    print(f"[*] 多重集守恒审计结果:")
    print(f"    - 原始全集分母 (N_raw):      {n_raw:,} 篇 (唯一键: {len(set_raw):,})")
    print(f"    - 有效处理集合 (N_valid):    {n_valid:,} 篇 (唯一键: {len(set_valid):,})")
    print(f"    - 显式合法排除 (N_excluded): {n_excluded:,} 篇 (唯一键: {len(set_excluded):,})")
    print(f"    - 闭环合计 (Valid+Excluded): {n_valid + n_excluded:,} 篇")
    print("-" * 65)
    print(f"    - 重复项排查: Raw={raw_dups}, Valid={valid_dups}, Excluded={excluded_dups}")
    print(f"    - 互斥冲突数 (Overlap):      {len(overlap)} 个")
    print(f"    - 静默遗漏数 (Missing):      {len(missing_ids)} 个")
    print(f"    - 异常多出数 (Unexpected):   {len(unexpected_ids)} 个")
    print("=" * 65)

    report = {
        "status": "PASSED" if is_conserved else "FAILED",
        "counts": {
            "n_raw": n_raw,
            "n_raw_unique": len(set_raw),
            "n_valid": n_valid,
            "n_valid_unique": len(set_valid),
            "n_excluded": n_excluded,
            "n_excluded_unique": len(set_excluded),
            "valid_ratio_percent": round(n_valid / n_raw * 100, 2) if n_raw > 0 else 0.0,
            "excluded_ratio_percent": round(n_excluded / n_raw * 100, 2) if n_raw > 0 else 0.0,
        },
        "integrity_checks": {
            "is_conserved": is_conserved,
            "count_balanced": count_balanced,
            "raw_duplicates": raw_dups,
            "valid_duplicates": valid_dups,
            "excluded_duplicates": excluded_dups,
            "overlap_count": len(overlap),
            "missing_count": len(missing_ids),
            "unexpected_count": len(unexpected_ids),
        },
        "samples": {
            "missing_sample": list(missing_ids)[:20],
            "overlap_sample": list(overlap)[:20],
            "unexpected_sample": list(unexpected_ids)[:20],
        }
    }

    if report_output:
        report_output.parent.mkdir(parents=True, exist_ok=True)
        with open(report_output, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"[+] 审计报告已归档: {report_output}")

    if not is_conserved:
        print("[FAIL] 多重集对账失败！存在重复键、静默丢弃、归类冲突、额外多出 ID 或计数不守恒！", file=sys.stderr)
        return 1

    print("[SUCCESS] 多重集数学守恒 100% 成立！分母流向完全闭合且可审计！")
    return 0


def main():
    parser = argparse.ArgumentParser(description="大规模数据流水线多重集守恒与分母闭合审计工具")
    parser.add_argument("--raw", required=True, help="原始全量输入文件路径")
    parser.add_argument("--valid", required=True, help="处理后的有效输出文件路径")
    parser.add_argument("--excluded", default=None, help="可选：显式过滤/排除的记录文件路径")
    parser.add_argument("--id-key", default="id", help="记录中唯一 ID 字段名 (默认 id)")
    parser.add_argument("--report", default=None, help="可选：审计报告输出 JSON 文件路径")
    args = parser.parse_args()

    sys.exit(audit_multiset(
        raw_file=Path(args.raw),
        valid_file=Path(args.valid),
        excluded_file=Path(args.excluded) if args.excluded else None,
        id_key=args.id_key,
        report_output=Path(args.report) if args.report else None
    ))


if __name__ == "__main__":
    main()
