#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
beautify_academic_docx.py
=========================
出版级学术 Word 终稿排版与规范三线表重塑工具 (Academic Word Formatter & Three-Line Table Styler)

核心特性：
1. 自动重塑全文所有表格为顶级期刊规范【三线表】：
   - 顶线与底线：1.5 pt (sz=12) 粗黑线；
   - 表头分隔线：0.75 pt (sz=6) 细黑线；
   - 彻底清除竖向边框与内部水平网格线；
   - 表头背景填充 `#F2F2F2` 浅灰底色，表头文字居中加粗；
   - 表格行设置 `cantSplit` 防止跨页截断，表头设置 `tblHeader` 跨页自动重复。
2. 中西文字体深度分离（底层 XML `w:rFonts` 强制注入）：
   - 正文中文：宋体 (SimSun)；正文西文/数字：Times New Roman；
   - 标题中文：黑体 (SimHei)；标题西文：Times New Roman。
3. 学术版式与版心优化：
   - A4 标准学术纸张（上/下页边距 2.54 cm，左/右页边距 2.80 cm）；
   - 正文段落首行自动缩进 2 字符，1.35 倍行距。

用法：
    python beautify_academic_docx.py <input.docx> [output.docx]
"""

import sys
import argparse
from pathlib import Path

try:
    import docx
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls
except ImportError:
    print("[ERROR] 缺失 python-docx 依赖。请先执行: pip install python-docx", file=sys.stderr)
    sys.exit(1)


def set_run_font(run, font_name="SimSun", ascii_font="Times New Roman", size_pt=11.5, bold=False, italic=False, color=None):
    """底层 XML 强制注入中西文字体分离"""
    run.font.name = ascii_font
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color

    rPr = run._r.get_or_add_rPr()
    for child in list(rPr):
        if child.tag.endswith("rFonts"):
            rPr.remove(child)
    rFonts = parse_xml(
        f'<w:rFonts {nsdecls("w")} w:ascii="{ascii_font}" w:hAnsi="{ascii_font}" w:eastAsia="{font_name}" w:cs="{ascii_font}"/>'
    )
    rPr.append(rFonts)


def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    """设置单元格内边距 (dxa)"""
    tcPr = cell._tc.get_or_add_tcPr()
    for child in list(tcPr):
        if child.tag.endswith("tcMar"):
            tcPr.remove(child)
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>'
    )
    tcPr.append(tcMar)


def set_cell_shading(cell, color_hex="F2F2F2"):
    """设置单元格背景底色"""
    tcPr = cell._tc.get_or_add_tcPr()
    for child in list(tcPr):
        if child.tag.endswith("shd"):
            tcPr.remove(child)
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    tcPr.append(shd)


def format_academic_docx(input_file: Path, output_file: Path) -> int:
    if not input_file.exists():
        print(f"[ERROR] 输入文件不存在: {input_file}", file=sys.stderr)
        return 1

    print(f"[*] 载入 Word 文档: {input_file}")
    doc = docx.Document(str(input_file))

    # 1. 设置页面边距 (A4 标准学术版式)
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.8)
        section.right_margin = Cm(2.8)

    # 2. 表格重塑：标准三线表
    table_count = len(doc.tables)
    print(f"[*] 发现表格 {table_count} 个，开始重塑为标准三线表...")
    for idx, table in enumerate(doc.tables, 1):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        tblPr = table._tbl.tblPr

        for child in list(tblPr):
            if child.tag.endswith("tblBorders"):
                tblPr.remove(child)

        # 顶底粗线 (sz=12 为 1.5pt)，无左右外框与内竖横线
        tblBorders = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>'
            f'<w:top w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
            f'<w:bottom w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
            f'<w:left w:val="none"/>'
            f'<w:right w:val="none"/>'
            f'<w:insideH w:val="none"/>'
            f'<w:insideV w:val="none"/>'
            f'</w:tblBorders>'
        )
        tblPr.append(tblBorders)

        for row_idx, row in enumerate(table.rows):
            trPr = row._tr.get_or_add_trPr()
            trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

            is_header = (row_idx == 0)
            if is_header:
                trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

            for cell in row.cells:
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                set_cell_margins(cell, top=100, bottom=100, left=140, right=140)

                if is_header:
                    set_cell_shading(cell, "F2F2F2")
                    tcPr = cell._tc.get_or_add_tcPr()
                    for child in list(tcPr):
                        if child.tag.endswith("tcBorders"):
                            tcPr.remove(child)
                    # 表头下细横线 (sz=6 为 0.75pt)
                    tcBorders = parse_xml(
                        f'<w:tcBorders {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/></w:tcBorders>'
                    )
                    tcPr.append(tcBorders)

                for p in cell.paragraphs:
                    p.paragraph_format.line_spacing = 1.15
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(2)
                    if is_header:
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for r in p.runs:
                        set_run_font(
                            r,
                            font_name="SimSun",
                            ascii_font="Times New Roman",
                            size_pt=10.0 if not is_header else 10.5,
                            bold=is_header
                        )

    # 3. 正文段落与标题格式优化
    print(f"[*] 规范正文段落排版 (缩进、行距与中西文字体分离)...")
    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue

        # 检查是否为标题段落
        is_heading = p.style.name.startswith("Heading") or (text.startswith("第") and "章" in text) or text.startswith("一、") or text.startswith("二、") or text.startswith("三、") or text.startswith("四、") or text.startswith("五、")

        if is_heading:
            p.paragraph_format.first_line_indent = Inches(0)
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(4)
            for r in p.runs:
                set_run_font(r, font_name="SimHei", ascii_font="Times New Roman", size_pt=13.0, bold=True)
        else:
            # 正文段落
            if not p.text.startswith("    ") and not p.text.startswith("\t"):
                p.paragraph_format.first_line_indent = Pt(22)  # 约 2 字符缩进
            p.paragraph_format.line_spacing = 1.35
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            for r in p.runs:
                set_run_font(r, font_name="SimSun", ascii_font="Times New Roman", size_pt=11.5)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_file))
    print(f"[SUCCESS] 出版级美化完成！保存至: {output_file}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="出版级学术 Word 终稿排版与三线表重塑工具")
    parser.add_argument("input", help="待排版的原始 Word 文件 (.docx)")
    parser.add_argument("output", nargs="?", default=None, help="排版后的输出 Word 文件 (.docx) (默认覆盖或生成 _beautified.docx)")
    args = parser.parse_args()

    inp = Path(args.input)
    if args.output:
        out = Path(args.output)
    else:
        out = inp.parent / f"{inp.stem}_beautified.docx"

    sys.exit(format_academic_docx(inp, out))


if __name__ == "__main__":
    main()
