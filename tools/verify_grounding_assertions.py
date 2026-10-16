#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_grounding_assertions.py
==============================
大模型信息抽取与源文本物理字符切片硬断言校验器 (Physical Quote Grounding Assertion Verifier)

核心特性：
1. 彻底消灭大模型信息抽取（实体、关系三元组、政策条文、理论假设）中的“假引用与幻觉”。
2. 对抽取结果中的字符级绝对切片坐标 [char_start, char_end] 执行数学硬断言：
       source_text[char_start:char_end] == extracted_quote
3. 严格拦截四类防御性反例：
   - 坐标越界或反向 (char_start >= char_end 或 char_end > len)；
   - 虚假全篇放行 (char_start == 0 且 char_end == len(text))；
   - 空文本或占位符放行；
   - 字符内容与源文不匹配（单字偏差即报错）。

用法：
    python verify_grounding_assertions.py <corpus_file> <extractions_file> [report_output] \
        [--id-field id] [--text-field text] [--quote-field quote] [--start-field start] [--end-field end]
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple


def load_corpus(corpus_path: Path, id_field: str = "id", text_field: str = "text") -> Dict[str, str]:
    """加载原始语料库为 {doc_id: raw_text} 字典"""
    corpus = {}
    if corpus_path.suffix.lower() == ".jsonl":
        with open(corpus_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                doc_id = str(item.get(id_field, ""))
                raw_text = item.get(text_field, "")
                if doc_id:
                    corpus[doc_id] = raw_text
    else:
        with open(corpus_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                # 已经是 key-value 或者带 data 字段
                if "data" in data and isinstance(data["data"], list):
                    items = data["data"]
                else:
                    items = data
            elif isinstance(data, list):
                items = data
            else:
                raise ValueError("不支持的语料库 JSON 结构")

            if isinstance(items, dict):
                for k, v in items.items():
                    corpus[str(k)] = v if isinstance(v, str) else v.get(text_field, "")
            else:
                for item in items:
                    doc_id = str(item.get(id_field, ""))
                    raw_text = item.get(text_field, "")
                    if doc_id:
                        corpus[doc_id] = raw_text

    return corpus


def verify_grounding(
    corpus_path: Path,
    extractions_path: Path,
    report_output: Path = None,
    id_field: str = "doc_id",
    text_field: str = "text",
    quote_field: str = "quote",
    start_field: str = "start",
    end_field: str = "end"
) -> int:
    print(f"[*] 载入原始语料: {corpus_path}")
    corpus = load_corpus(corpus_path, id_field="id", text_field=text_field)
    print(f"    - 成功索引底账文档: {len(corpus):,} 篇")

    print(f"[*] 读取待核验抽取数据: {extractions_path}")
    assertions = []
    if extractions_path.suffix.lower() == ".jsonl":
        with open(extractions_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    assertions.append(json.loads(line))
    else:
        with open(extractions_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assertions = data if isinstance(data, list) else data.get("assertions", [])

    print(f"    - 扫描到待核验物理切片断言: {len(assertions):,} 条")

    passed_count = 0
    failed_count = 0
    failures = []

    for idx, item in enumerate(assertions, 1):
        doc_id = str(item.get(id_field, item.get("paper_id", item.get("id", ""))))
        quote = item.get(quote_field, item.get("extracted_text", item.get("statement", "")))
        start = item.get(start_field, item.get("char_start", None))
        end = item.get(end_field, item.get("char_end", None))

        error_reason = None
        if not doc_id:
            error_reason = "缺少文档唯一 ID"
        elif doc_id not in corpus:
            error_reason = f"文档 ID {doc_id} 在源语料库中不存在"
        elif start is None or end is None:
            error_reason = "缺失物理坐标 start 或 end"
        elif not isinstance(start, int) or not isinstance(end, int):
            error_reason = f"坐标不是整数类型: [{start}, {end}]"
        elif start < 0 or end < 0 or start >= end:
            error_reason = f"坐标范围非法: [{start}, {end}]"
        else:
            raw_text = corpus[doc_id]
            if end > len(raw_text):
                error_reason = f"坐标超出文本总长度 (end={end} > len={len(raw_text)})"
            elif start == 0 and end == len(raw_text) and len(raw_text) > 100:
                error_reason = "疑似虚假全篇放行 (坐标为 [0, len])"
            else:
                sliced = raw_text[start:end]
                if sliced != quote:
                    error_reason = f"物理切片字符不匹配 (预期: '{quote[:30]}...' vs 实际: '{sliced[:30]}...')"

        if error_reason is None:
            passed_count += 1
        else:
            failed_count += 1
            failures.append({
                "assertion_index": idx,
                "doc_id": doc_id,
                "coordinates": [start, end],
                "quote_sample": str(quote)[:50],
                "error": error_reason
            })

    total = passed_count + failed_count
    pass_rate = (passed_count / total * 100) if total > 0 else 0.0

    print("=" * 60)
    print(f"[*] 物理字符切片断言硬校验汇总:")
    print(f"    - 总核验断言数: {total:,} 条")
    print(f"    - 硬断言通过数: {passed_count:,} 条 ({pass_rate:.2f}%)")
    print(f"    - 失败/异常断言数: {failed_count:,} 条")
    print("=" * 60)

    report_data = {
        "total_assertions": total,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "pass_rate_percent": round(pass_rate, 2),
        "failures_sample": failures[:50]
    }

    if report_output:
        report_output.parent.mkdir(parents=True, exist_ok=True)
        with open(report_output, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        print(f"[+] 详细质检报告已保存: {report_output}")

    if failed_count > 0:
        print(f"[FAIL] 存在 {failed_count} 条断言未通过硬切片检验！拒绝放行。", file=sys.stderr)
        return 1
    else:
        print("[SUCCESS] 全量切片 100% 吻合原文！物理断言严密，无幻觉！")
        return 0


def main():
    parser = argparse.ArgumentParser(description="原文物理字符切片硬断言校验器 (防幻觉与坐标漂移)")
    parser.add_argument("corpus", help="原始底账语料库文件路径 (.json 或 .jsonl)")
    parser.add_argument("extractions", help="待检验的抽取结果文件路径 (.json 或 .jsonl)")
    parser.add_argument("report", nargs="?", default=None, help="可选：质检报告输出路径 (.json)")
    parser.add_argument("--id-field", default="id", help="语料与抽取结果中的 ID 字段名 (默认 id)")
    parser.add_argument("--text-field", default="text", help="语料中的正文字段名 (默认 text)")
    parser.add_argument("--quote-field", default="quote", help="抽取记录中的原句字段名 (默认 quote)")
    parser.add_argument("--start-field", default="start", help="抽取记录中的起点坐标字段名 (默认 start)")
    parser.add_argument("--end-field", default="end", help="抽取记录中的终点坐标字段名 (默认 end)")
    args = parser.parse_args()

    sys.exit(verify_grounding(
        corpus_path=Path(args.corpus),
        extractions_path=Path(args.extractions),
        report_output=Path(args.report) if args.report else None,
        id_field=args.id_field,
        text_field=args.text_field,
        quote_field=args.quote_field,
        start_field=args.start_field,
        end_field=args.end_field
    ))


if __name__ == "__main__":
    main()
