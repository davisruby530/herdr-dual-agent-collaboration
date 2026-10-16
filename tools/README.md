# 跨项目通用数据与工程工具箱 (Generic Engineering & Data Toolkit)

本目录包含从大规模实证研究、高可靠数据清洗与学术出版实践中提炼出的**解耦、模型不可知、开箱即用**的工程资产工具，可直接复制到任何新科研与开发项目中。

---

## 🛠️ 工具清单一览

| 工具脚本 | 核心功能 | 解决痛点 | 典型应用场景 |
| :--- | :--- | :--- | :--- |
| **[`build_distribution_zip.py`](./build_distribution_zip.py)** | 跨平台零乱码成果压缩包构建器 | 彻底解决 Windows 解压 macOS 打包文件时的中文字符乱码与系统隐藏文件污染 | 科研成果打包、论文与复现代码向评审人/合作者轻量分发 |
| **[`beautify_academic_docx.py`](./beautify_academic_docx.py)** | 出版级学术 Word 终稿与标准三线表自动排版器 | 解决 Markdown/Pandoc 导出的 docx 表格粗糙、中西文字体混乱、无三线表等问题 | 快速生成符合 CSSCI/SSCI 顶刊标准的审稿 Word 终稿 |
| **[`verify_grounding_assertions.py`](./verify_grounding_assertions.py)** | 原文物理字符切片硬断言校验器 | 彻底消灭大模型信息抽取中的虚构幻觉、引文偏差与坐标偏移 (`source[start:end] == quote`) | LLM 实体识别、因果三元组抽取、政策条文引用、微观案例实证 |
| **[`audit_multiset_integrity.py`](./audit_multiset_integrity.py)** | 大规模数据流水线多重集守恒与分母审计器 | 解决数据处理中样本分母模糊、静默遗漏丢失、重复键与归类重叠问题 | 数据清洗 ETL、全量语料过滤、实证样本分流审计 |

---

## 📖 详细使用指南

### 1. `build_distribution_zip.py`：跨平台零乱码成果包构建

在 macOS 上打包包含中文目录与文档的科研包时，Windows 自带解压或 WinRAR 经常因 GBK/UTF-8 字符集判断失误而发生乱码。本工具强制为每个文件注入 PKZIP 规范的 **Bit 11 (0x800) Language Encoding Flag**，并在打包时自动剔除 `.DS_Store`、`__MACOSX`、`.git`、`__pycache__` 等冗余垃圾。

```bash
# 基本用法：将成果目录打包为 release.zip，并增加顶层目录前缀
python3 tools/build_distribution_zip.py ./my_deliverables ./release.zip --root-prefix "研究成果交付包"
```

---

### 2. `beautify_academic_docx.py`：出版级学术 Word 自动排版器

将任意初稿 docx 快速格式化为顶刊标准排版：
- 全文表格自动转为**标准三线表**（顶底 1.5pt 粗黑线、表头下 0.75pt 细横线、无竖线内横线、表头浅灰 `#F2F2F2` 底色加粗居中、跨页自动重复表头）；
- 底层 XML 强制注入中西文字体分离（正文中文宋体、西文 Times New Roman；标题中文黑体）；
- A4 标准学术版式、正文首行缩进 2 字符、1.35 倍行距。

```bash
# 依赖：pip install python-docx
python3 tools/beautify_academic_docx.py raw_draft.docx publication_ready.docx
```

---

### 3. `verify_grounding_assertions.py`：物理字符切片防幻觉断言器

大模型在做长文本抽取时，容易产生“局部篡改原文”或“伪造切片坐标”的幻觉。本工具逐条核验抽取结果：
$$\text{source\_text}[\text{char\_start}:\text{char\_end}] == \text{extracted\_quote}$$
单字不符或全篇放行 `[0, len)` 立即报错并阻断交付。

```bash
# 对语料库与抽取结果做 100% 物理硬断言对账
python3 tools/verify_grounding_assertions.py \
    path/to/raw_corpus.jsonl \
    path/to/extractions.jsonl \
    path/to/grounding_audit_report.json \
    --id-field id \
    --text-field text \
    --quote-field extracted_quote \
    --start-field char_start \
    --end-field char_end
```

---

### 4. `audit_multiset_integrity.py`：多重集守恒与分母审计器

在大规模实证数据流中把守数学守恒底线：
$$\text{全量输入 } N_{\text{raw}} = \text{有效处理 } N_{\text{valid}} + \text{合法排除 } N_{\text{excluded}}$$
严格断言交集为空、并集完全一致、零重复键、零静默丢弃。

```bash
python3 tools/audit_multiset_integrity.py \
    --raw path/to/all_raw_ids.txt \
    --valid path/to/valid_processed_records.jsonl \
    --excluded path/to/excluded_records.json \
    --id-key id \
    --report path/to/denominator_audit_report.json
```
