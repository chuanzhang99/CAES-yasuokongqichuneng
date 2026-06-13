"""命令行入口。

用法示例：
    python cli.py
    python cli.py --check
    python cli.py --export result.txt
    python cli.py --input-dir data --check --export out.txt
"""

import argparse
import os
import sys
from typing import Dict

from caes_calc.calculations import run_all_calculations
from caes_calc.persistence import load_inputs
from caes_calc.validation import validate


# Windows 控制台默认 GBK，强制 stdout/stderr 使用 UTF-8 以避免中文乱码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


SECTION_TITLES = {
    "compression": "压缩机计算结果",
    "expansion": "膨胀机计算结果",
    "thermal": "导热油与盐穴计算结果",
    "system": "系统汇总",
}


def format_value(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def print_results(results: Dict[str, Dict]):
    for key, title in SECTION_TITLES.items():
        print(f"\n=== {title} ===")
        for param, val in results[key].items():
            print(f"{param}: {format_value(val)}")


def export_results(results: Dict[str, Dict], filepath: str):
    with open(filepath, "w", encoding="utf-8") as file:
        for key, title in SECTION_TITLES.items():
            file.write(f"{title}\n")
            file.write("参数,值\n")
            for param, val in results[key].items():
                file.write(f"{param},{format_value(val)}\n")
            file.write("\n")


def main():
    parser = argparse.ArgumentParser(description="非补燃压缩空气储能参数计算")
    parser.add_argument("--input-dir", default="data", help="输入数据目录（默认：data）")
    parser.add_argument("--export", metavar="FILE", help="导出结果到指定 txt 文件")
    parser.add_argument("--check", action="store_true", help="运行数据检查并打印警告")
    args = parser.parse_args()

    inputs = load_inputs(args.input_dir)
    results = run_all_calculations(inputs)

    print_results(results)

    if args.check:
        warnings = validate(inputs)
        print("\n=== 数据检查结果 ===")
        if warnings:
            for warning in warnings:
                print(warning)
        else:
            print("所有计算值均在预期范围内")

    if args.export:
        export_results(results, args.export)
        print(f"\n结果已导出到：{os.path.abspath(args.export)}")


if __name__ == "__main__":
    main()
