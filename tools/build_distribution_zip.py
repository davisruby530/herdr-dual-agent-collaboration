#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_distribution_zip.py
=========================
跨平台零乱码科研分发成果包压缩工具 (Cross-Platform Anti-Garbled Zip Builder)

核心特性：
1. 强制注入 PKZIP 规范的 Language encoding flag (Bit 11: 0x800)，彻底解决 Windows 10/11
   系统自带解压、WinRAR、7-Zip、360压缩等解压中文文件名乱码的顽疾。
2. 自动递归剔除 macOS 系统特有的 `__MACOSX` 资源分叉、`.DS_Store` 垃圾隐藏文件以及 Git/Python 缓存。
3. 支持设置解压顶层根目录前缀 (Root Prefix)，解压后整洁不散落。

用法：
    python build_distribution_zip.py <source_dir_or_file> [output_zip] [--root-prefix <name>]

示例：
    python build_distribution_zip.py ./my_research_results ./release.zip --root-prefix 成果交付包
"""

import os
import sys
import argparse
import zipfile
from pathlib import Path

# 默认排除的系统垃圾与开发缓存模式
DEFAULT_IGNORE_PATTERNS = {
    ".DS_Store",
    "__MACOSX",
    ".git",
    ".gitignore",
    ".gitattributes",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "node_modules",
}


# 凭据与密钥：分发包会交给评审人和合作者，绝不能带出去
SECRET_DIRS = {".ssh", ".gnupg", ".aws"}
SECRET_NAMES = {".netrc", ".npmrc", ".pypirc", "credentials.json", "auth.json"}
SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx")


def is_secret(part: str) -> bool:
    return (
        part in SECRET_DIRS
        or part in SECRET_NAMES
        or part == ".env"
        or part.startswith(".env.")
        or part.startswith("id_rsa")
        or part.startswith("id_ed25519")
        or part.endswith(SECRET_SUFFIXES)
    )


def should_ignore(path: Path) -> bool:
    for part in path.parts:
        if part in DEFAULT_IGNORE_PATTERNS:
            return True
        if part.endswith(".pyc") or part.endswith(".tmp") or part.endswith(".swp"):
            return True
        if is_secret(part):
            return True
    return False


def build_distribution_zip(
    source_path: Path,
    output_zip: Path,
    root_prefix: str = ""
) -> int:
    source_path = source_path.resolve()
    output_zip = output_zip.resolve()

    if not source_path.exists():
        print(f"[ERROR] 源路径不存在: {source_path}", file=sys.stderr)
        return 1

    print(f"[*] 开始构建跨平台防乱码分发包:")
    print(f"    - 源路径: {source_path}")
    print(f"    - 输出包: {output_zip}")
    if root_prefix:
        print(f"    - 顶层前缀: {root_prefix}/")

    output_zip.parent.mkdir(parents=True, exist_ok=True)

    files_to_pack = []
    if source_path.is_file():
        arcname = f"{root_prefix}/{source_path.name}" if root_prefix else source_path.name
        files_to_pack.append((source_path, arcname))
    else:
        for root, dirs, files in os.walk(source_path):
            current_dir = Path(root)
            if should_ignore(current_dir.relative_to(source_path)):
                continue
            for file in files:
                file_path = current_dir / file
                rel_path = file_path.relative_to(source_path)
                if file_path.resolve() == output_zip:
                    continue
                if should_ignore(rel_path):
                    if any(is_secret(p) for p in rel_path.parts):
                        print(f"  - [跳过凭据] {rel_path.as_posix()}")
                    continue
                if root_prefix:
                    arcname = f"{root_prefix}/{rel_path.as_posix()}"
                else:
                    arcname = rel_path.as_posix()
                files_to_pack.append((file_path, arcname))

    print(f"[*] 扫描到有效交付文件: {len(files_to_pack)} 个")

    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src_file, arcname in files_to_pack:
            try:
                with open(src_file, "rb") as f:
                    data = f.read()
                
                # 显式构造 ZipInfo 并标记 Bit 11 为 1 (启用标准 UTF-8 文件名编码)
                zinfo = zipfile.ZipInfo(arcname)
                zinfo.flag_bits |= 0x800  # Language encoding flag (EFS)
                zinfo.external_attr = 0o644 << 16
                zf.writestr(zinfo, data)
                print(f"  + [UTF-8] {arcname}")
            except Exception as e:
                print(f"  x 打包失败 {src_file}: {e}", file=sys.stderr)
                return 1

    size_mb = output_zip.stat().st_size / (1024 * 1024)
    print(f"[SUCCESS] 压缩包打包完成！总大小: {size_mb:.2f} MB")
    print(f"          文件路径: {output_zip}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="跨平台防乱码分发包构建工具 (UTF-8 Bit 11)")
    parser.add_argument("source", help="需要打包的源文件或目录路径")
    parser.add_argument("output", nargs="?", default=None, help="输出的 zip 文件路径 (默认在源目录下生成同名.zip)")
    parser.add_argument("--root-prefix", default="", help="可选：解压后的顶层根目录名称前缀")
    args = parser.parse_args()

    src = Path(args.source)
    if args.output:
        out = Path(args.output)
    else:
        out = src.parent / f"{src.name}.zip"

    sys.exit(build_distribution_zip(src, out, args.root_prefix))


if __name__ == "__main__":
    main()
