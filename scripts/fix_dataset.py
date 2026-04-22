#!/usr/bin/env python3
"""
OneDZ 数据集格式修正脚本 (流式版)

修正 zircon_upb.csv 和 zircon_luhf.csv 的格式问题，输出到 modified/ 目录。
原数据文件不会被修改。

特性：
- 流式逐行处理，内存占用极低（< 100MB），不会导致 WSL 崩溃
- 不修改列名，与 skill 的 config.py Cols 定义兼容
- 修正编码乱码、拼写错误、大小写不一致等问题
"""

import csv
import re
import sys
from pathlib import Path

# ============================================================
# 路径配置
# ============================================================
# 支持命令行参数或默认路径
if len(sys.argv) > 1:
    INPUT_DIR = Path(sys.argv[1])
else:
    INPUT_DIR = Path("/home/zry/my_earth/data/raw/OneDZ/onedz_csv_20260328")

OUTPUT_DIR = INPUT_DIR / "modified"
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================
# 编码乱码修复映射
# ============================================================

def _build_mojibake_map():
    """构建修复映射，按长度降序排列以优先匹配长字符串"""
    pairs = [
        # 鈥 是 U+9212 (CJK)，通常代表 – (en-dash U+2013)
        # 鈥揗C鈥揑CP鈥揗S → –MC–ICP–MS
        ('鈥揗C鈥揑CP鈥揗S', '-MC-ICP-MS'),
        ('鈥揗C鈥揑CP', '-MC-ICP'),
        ('鈥揗C', '-MC'),
        ('鈥揑CP', '-ICP'),
        ('鈥揗S', '-MS'),
        ('鈥揗', '-M'),
        ('鈥揃', '-C'),
        ('鈥?', '-'),
        # 聽 是 U+807D，通常代表 non-breaking space 或普通空格
        ('聽', ' '),
        # 其他常见乱码
        ('脟', '\u00c7'),  # Ç
        ('锛?', '('),
        ('锛?', '('),
    ]
    # 按长度降序排列
    pairs.sort(key=lambda x: -len(x[0]))
    return dict(pairs)


MOJIBAKE_MAP = _build_mojibake_map()


def fix_mojibake(text):
    """修复常见的编码乱码字符"""
    if not text:
        return text
    for bad, good in MOJIBAKE_MAP.items():
        text = text.replace(bad, good)
    return text


def normalize_dashes(text):
    """将各种 Unicode 连字符统一为 ASCII 连字符 -"""
    if not text:
        return text
    for char in ['\u2013', '\u2014', '\u2212', '\u2010']:  # en-dash, em-dash, minus, hyphen
        text = text.replace(char, '-')
    return text


# ============================================================
# 各列修正规则
# ============================================================

# --- Mineral ---
MINERAL_CORRECT = {
    'zircom': 'zircon',
    'zircon ': 'zircon',
    'Zircon': 'zircon',
    'LA-ICP-MS': 'zircon',  # 方法名混入矿物列
}

def fix_mineral(v):
    v = v.strip()
    return MINERAL_CORRECT.get(v, v)


# --- Mass Spectrometer ---
def fix_mass_spectrometer(v):
    """标准化 Mass Spectrometer 列"""
    v = v.strip()
    if not v:
        return v

    # 先修复编码和统一连字符
    v = fix_mojibake(v)
    v = normalize_dashes(v)
    v = v.strip()

    # 长描述文本 → 简化（它们本质上是 LA-ICP-MS）
    long_desc_patterns = [
        (r'GeoLas2005.*?(LA|ICP|MS).*?质谱.*', 'LA-ICP-MS'),
        (r'Agilent.*?ICP.*?MS.*?laser.*', 'LA-ICP-MS'),
        (r'New Wave.*?laser.*', 'LA-ICP-MS'),
        (r'7500a.*?ICP-MS', 'LA-ICP-MS'),
        (r'Nu Plasma.*?ICP-MS', 'MC-ICP-MS'),
    ]
    for pat, replacement in long_desc_patterns:
        if re.search(pat, v, re.IGNORECASE):
            return replacement

    # 大小写统一并去除多余空格
    v = re.sub(r'\s+', ' ', v).strip()

    # 标准化映射（小写比较）
    vl = v.lower()

    # LA-ICP-MS 系列变体
    if vl in ('la-icp-ms', 'la_icp_ms', 'la-icpms', 'laicp-ms', 'laicpms',
              'la-icp-ma', 'la icp-ms', 'la-icp-ms u-pb'):
        return 'LA-ICP-MS'

    # LA-MC-ICP-MS 系列
    if vl in ('la-mc-icp-ms', 'la_mc_icp_ms', 'la_mc_icpms)', 'la-mc-icpms'):
        return 'LA-MC-ICP-MS'

    # MC-ICP-MS 系列
    if vl in ('mc-icp-ms', 'mc-icp-ms', 'mc_icp_ms', 'mc-icp-ms', 'mc-icpms',
              'mc-icp-ms/q-icp-ms', 'mc-icp-ms\u548cq-icp-ms'):  # 最后一个是中文"和"
        return 'MC-ICP-MS' if 'q' not in vl else 'MC-ICP-MS/Q-ICP-MS'

    # Q-ICP-MS
    if vl in ('q-icp-ms', 'q-icp_ms'):
        return 'Q-ICP-MS'

    # ICP-MS
    if vl in ('icp-ms', 'icpms'):
        return 'ICP-MS'

    # SHRIMP
    if vl in ('shrimp', 'shrimp ii', 'shrimp\u2161'):  # Ⅱ = U+2161
        return 'SHRIMP II' if 'ii' in vl or '\u2161' in vl else 'SHRIMP'

    # SIMS
    if vl in ('sims',):
        return 'SIMS'

    # ID-TIMS
    if vl in ('id-tims', 'id_tims'):
        return 'ID-TIMS'

    # LASS
    if vl == 'lass':
        return 'LASS'

    # LA-SF-ICP-MS
    if vl == 'la-sf-icp-ms':
        return 'LA-SF-ICP-MS'

    # 组合方法
    if vl == 'la-icp-ms and la-mc-icp-ms' or vl == 'la-icp-ma and la-mc-icp-ms':
        return 'LA-ICP-MS + LA-MC-ICP-MS'
    if vl == 'la-mc-icp-ms and shrimp' or vl == 'la-mc-icp-ms and shrimp ':
        return 'LA-MC-ICP-MS + SHRIMP'
    if vl == 'la-icp-ms and shrimp':
        return 'LA-ICP-MS + SHRIMP'
    if vl == 'la-icp-ms&la-q-icp-ms':
        return 'LA-ICP-MS + LA-Q-ICP-MS'
    if vl == 'la-icp-ms/la-icp-ma':
        return 'LA-ICP-MS'

    # 位置信息混入 → 保留原始值但标记
    # Beijing, Nanjing University, Shan'xi, Xi'an Center... 这些是 Spectrometer Location
    # 不是 Mass Spectrometer，但原数据就是这样的，我们只修复编码，不改数据归属

    # Single-zircon evaporation
    if vl == 'single-zircon evaporation':
        return 'Single-zircon evaporation'

    return v


# --- Comment ---
def fix_comment(v):
    """修正 Comment 列的编码问题"""
    v = v.strip()
    v = fix_mojibake(v)
    # mélange 编码修复
    v = re.sub(r'me\?lange', 'm\xe9lange', v)
    v = re.sub(r'me\xb4lange', 'm\xe9lange', v)
    v = re.sub(r'me\u00b4lange', 'm\xe9lange', v)
    # 去除单独的中文句号
    if v == '\u3002':
        v = ''
    return v


# --- Continent ---
BAD_CONTINENT_VALUES = {
    'China', 'Eastern China', 'Tajikistan', 'Uruguay',
    'Continental Basin', 'Baoshan Terrane',
    'Central Asian Orogenic Belt', 'North China Block',
    'Northen China', 'Southen China',
}

def fix_continent(v):
    v = v.strip()
    if not v:
        return v
    # 样本编号模式
    if re.match(r'^PMR-\d+-\d+$', v):
        return ''
    # 以数字开头的非纯数字（如 "0inling Orogenic Belt"）
    if re.match(r'^\d', v) and not v.isdigit():
        return ''
    # 已知错误值
    if v in BAD_CONTINENT_VALUES:
        return ''
    return v


# --- Class-1 Rock Type ---
ROCK_TYPE_1_CORRECT = {
    'derital': 'detrital',
    'dietrial': 'detrital',
}

def fix_rock_type_1(v):
    v = v.strip()
    return ROCK_TYPE_1_CORRECT.get(v, v)


# --- Spectrometer Location ---
def fix_spectrometer_location(v):
    v = v.strip()
    if not v:
        return v
    v = fix_mojibake(v)
    v = normalize_dashes(v)
    # non-breaking space → normal space
    v = v.replace('\xa0', ' ')
    v = re.sub(r'\s+', ' ', v)
    return v.strip()


# --- Member ---
def fix_member(v):
    v = v.strip()
    if not v:
        return v
    v = fix_mojibake(v)
    return v


# ============================================================
# 通用文本清理（应用于所有列）
# ============================================================

def clean_text_general(v):
    """通用文本清理：修复编码、统一连字符、去首尾空格、non-breaking space"""
    if not v:
        return v
    v = v.strip()
    v = v.replace('\xa0', ' ')
    v = fix_mojibake(v)
    return v


# ============================================================
# 流式处理函数
# ============================================================

# 列名 → 修正函数映射（upb 和 luhf 共用列名）
COLUMN_FIXERS_COMMON = {
    'Mineral': fix_mineral,
    'Mass Spectrometer': fix_mass_spectrometer,
    'Comment': fix_comment,
    'Continent': fix_continent,
    'Spectrometer Location': fix_spectrometer_location,
    'Class-1 Rock Type': fix_rock_type_1,
    'Member': fix_member,
}

# 统计数据结构
class Stats:
    def __init__(self):
        self.total = 0
        self.fixed = {}  # column_name → count

    def record(self, col, original, fixed):
        if original != fixed:
            self.fixed[col] = self.fixed.get(col, 0) + 1

    def report(self):
        print(f"  总行数: {self.total:,}")
        for col, count in sorted(self.fixed.items()):
            print(f"  {col}: 修正 {count:,} 行")


def process_file(input_path: Path, output_path: Path, label: str):
    """
    流式处理 CSV 文件：逐行读取、修正、写入，内存占用极低。
    """
    print(f"\n{'='*60}")
    print(f"处理: {label}")
    print(f"输入: {input_path}")
    print(f"输出: {output_path}")
    print(f"{'='*60}")

    stats = Stats()

    with open(input_path, 'r', encoding='utf-8', errors='replace') as fin, \
         open(output_path, 'w', encoding='utf-8', newline='') as fout:

        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            stats.total += 1
            for col, val in row.items():
                fixer = COLUMN_FIXERS_COMMON.get(col)
                if fixer:
                    fixed = fixer(val)
                    stats.record(col, val.strip(), fixed)
                    row[col] = fixed
                else:
                    # 通用清理
                    cleaned = clean_text_general(val)
                    row[col] = cleaned

            writer.writerow(row)

            # 每 50 万行打印进度
            if stats.total % 500_000 == 0:
                print(f"  ... 已处理 {stats.total:,} 行", flush=True)

    stats.report()
    return stats


# ============================================================
# 主函数
# ============================================================

def main():
    import time
    start = time.time()

    print("OneDZ 数据集格式修正 (流式处理)")
    print(f"输入目录: {INPUT_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")

    upb_input = INPUT_DIR / "zircon_upb.csv"
    luhf_input = INPUT_DIR / "zircon_luhf.csv"

    # 检查输入文件
    for f in [upb_input, luhf_input]:
        if not f.exists():
            print(f"错误: 文件不存在 {f}", file=sys.stderr)
            sys.exit(1)
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  {f.name}: {size_mb:.0f} MB")

    # 处理
    upb_stats = process_file(upb_input, OUTPUT_DIR / "zircon_upb.csv", "U-Pb")
    luhf_stats = process_file(luhf_input, OUTPUT_DIR / "zircon_luhf.csv", "Lu-Hf")

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"修正完成！耗时 {elapsed:.1f} 秒")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
