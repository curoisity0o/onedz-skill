#!/usr/bin/env python3
"""
为 modified/ 目录中的修正后 CSV 生成 onedz_dataset_structure.json。

流式处理，内存友好（< 500MB），不会导致 WSL 崩溃。
用法：python3 generate_structure.py [input_dir]
默认：/home/zry/my_earth/data/raw/OneDZ/onedz_csv_20260328/modified
"""

import csv
import json
import sys
import time
from collections import OrderedDict
from pathlib import Path


# 分类的列：unique 值 < 这个阈值时视为分类列，收集所有 categories
CATEGORY_THRESHOLD = 500

# 高基数列中保留的最大 unique 样本数（用于 set 内存控制）
MAX_UNIQUE_SET_SIZE = 50000

# sample_values 保留数
SAMPLE_SIZE = 10


def analyze_csv(file_path: Path, label: str) -> dict:
    """
    流式扫描 CSV，收集每列的统计信息。
    返回与原始 onedz_dataset_structure.json files section 相同的结构。
    """
    print(f"\n分析: {label}")
    print(f"文件: {file_path} ({file_path.stat().st_size / 1024 / 1024:.0f} MB)")

    stats = {}  # col_name → {null_count, unique_set, sample_values, first_value}

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        total_rows = 0

        # 初始化
        for col in fieldnames:
            stats[col] = {
                'null_count': 0,
                'unique_set': set(),
                'unique_overflow': False,  # 是否超过了 MAX_UNIQUE_SET_SIZE
                'sample_values': [],
            }

        for row in reader:
            total_rows += 1
            for col in fieldnames:
                val = row.get(col, '')
                col_stat = stats[col]

                if val is None or val.strip() == '':
                    col_stat['null_count'] += 1
                    continue

                val = val.strip()

                # unique 追踪（内存保护）
                if not col_stat['unique_overflow'] and len(col_stat['unique_set']) < MAX_UNIQUE_SET_SIZE:
                    col_stat['unique_set'].add(val)
                    if len(col_stat['unique_set']) >= MAX_UNIQUE_SET_SIZE:
                        col_stat['unique_overflow'] = True

                # sample values（取前 N 个非空值）
                if len(col_stat['sample_values']) < SAMPLE_SIZE:
                    col_stat['sample_values'].append(val)

            if total_rows % 500_000 == 0:
                print(f"  ... {total_rows:,} 行", flush=True)

    print(f"  完成: {total_rows:,} 行, {len(fieldnames)} 列")

    # 构建 JSON 结构
    columns = OrderedDict()
    quick_index = OrderedDict()

    for col in fieldnames:
        s = stats[col]
        non_null = total_rows - s['null_count']
        null_ratio = round(s['null_count'] / total_rows * 100, 2) if total_rows > 0 else 0

        unique_count = len(s['unique_set'])
        is_categorical = unique_count < CATEGORY_THRESHOLD and unique_count > 0

        # 判断 data_type：如果 unique 少或是空值比例高 → text
        data_type = "text"

        entry = {
            "data_type": data_type,
            "total_rows": total_rows,
            "non_null_count": non_null,
            "null_count": s['null_count'],
            "null_ratio": null_ratio,
            "unique_count": unique_count,
            "sample_values": s['sample_values'][:SAMPLE_SIZE],
            "categories": sorted(s['unique_set']) if is_categorical else None,
        }
        columns[col] = entry

        # quick_index：只收录有 categories 的列
        if is_categorical:
            quick_index[col] = {
                "files": [file_path.name],
                "categories": sorted(s['unique_set']),
            }

    return {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "total_rows": total_rows,
        "total_columns": len(fieldnames),
        "columns": columns,
    }, quick_index


def main():
    start = time.time()

    # 输入目录
    if len(sys.argv) > 1:
        input_dir = Path(sys.argv[1])
    else:
        input_dir = Path("/home/zry/my_earth/data/raw/OneDZ/onedz_csv_20260328/modified")

    upb_path = input_dir / "zircon_upb.csv"
    luhf_path = input_dir / "zircon_luhf.csv"

    for f in [upb_path, luhf_path]:
        if not f.exists():
            print(f"错误: 文件不存在 {f}", file=sys.stderr)
            sys.exit(1)

    print("OneDZ 数据集结构分析 (修正后)")
    print(f"输入目录: {input_dir}")

    # 分析两个文件
    upb_info, upb_qi = analyze_csv(upb_path, "U-Pb")
    luhf_info, luhf_qi = analyze_csv(luhf_path, "Lu-Hf")

    # 合并 quick_index（upb 的 categories 和 luhf 的 categories 取并集）
    quick_index = OrderedDict()
    for qi in [upb_qi, luhf_qi]:
        for col, info in qi.items():
            if col in quick_index:
                existing = quick_index[col]
                existing_files = existing["files"]
                for fn in info["files"]:
                    if fn not in existing_files:
                        existing_files.append(fn)
                existing_cats = set(existing["categories"])
                existing_cats.update(info["categories"])
                existing["categories"] = sorted(existing_cats)
            else:
                quick_index[col] = info

    # 汇总
    total_records = upb_info["total_rows"] + luhf_info["total_rows"]
    total_columns = upb_info["total_columns"] + luhf_info["total_columns"]

    result = OrderedDict([
        ("dataset_name", "OneDZ Database (Modified)"),
        ("version", "20260328-modified"),
        ("description", "修正后的全球碎屑锆石数据库 - 包含 U-Pb 和 Lu-Hf 同位素数据（格式已标准化）"),
        ("source_dir", str(input_dir)),
        ("summary", OrderedDict([
            ("total_files", 2),
            ("total_records", total_records),
            ("total_columns", total_columns),
            ("files", ["zircon_upb.csv", "zircon_luhf.csv"]),
        ])),
        ("quick_index", quick_index),
        ("files", OrderedDict([
            ("zircon_upb.csv", upb_info),
            ("zircon_luhf.csv", luhf_info),
        ])),
    ])

    # 输出
    output_path = input_dir / "onedz_dataset_structure.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"生成完成！耗时 {elapsed:.1f} 秒")
    print(f"输出: {output_path}")
    print(f"总记录: {total_records:,}")
    print(f"分类列 (quick_index): {len(quick_index)} 个")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
