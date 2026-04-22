#!/usr/bin/env python3
"""
OneDZ 数据集快速探索脚本
========================

帮助用户快速了解 OneDZ 数据集的内容和结构

生成时间: 2026-04-20
目的: 探索性分析，了解数据集的维度和范围
"""

from scripts.onedz_handler import OneDZHandler


def explore_dataset():
    """探索 OneDZ 数据集的基本信息"""
    print("=" * 70)
    print("🔍 OneDZ 数据集快速探索")
    print("=" * 70)

    handler = OneDZHandler()

    # 加载数据
    print("\n📦 加载 U-Pb 数据...")
    handler.load(source="csv", table="global_u-pb")
    df = handler.data

    print(f"\n📊 数据集基本信息:")
    print(f"   总记录数: {df.height:,}")
    print(f"   总列数: {df.width}")
    print(f"   数据来源: Li et al. (2025) OneDZ Database")

    # 探索关键维度
    print(f"\n🔑 关键维度探索:")

    # 1. 地质年代分布
    print(f"\n   1️⃣  地质年代 (Period):")
    if "Period" in df.columns:
        period_counts = df["Period"].drop_nulls().value_counts().sort("count", descending=True)
        print(f"      不同年代数: {period_counts.height}")
        print(f"      Top 10 年代:")
        for row in period_counts.head(10).iter_rows():
            period = row[0] if row[0] else "Unknown"
            count = row[1]
            print(f"         • {period:<20} {count:>10,} 条")

    # 2. 岩石类型分布
    print(f"\n   2️⃣  岩石类型 (Class-1):")
    if "Rock_Class1" in df.columns:
        rock_counts = df["Rock_Class1"].drop_nulls().value_counts().sort("count", descending=True)
        print(f"      不同类型数: {rock_counts.height}")
        print(f"      Top 10 类型:")
        for row in rock_counts.head(10).iter_rows():
            rock_type = row[0] if row[0] else "Unknown"
            count = row[1]
            print(f"         • {rock_type:<30} {count:>10,} 条")

    # 3. 地理分布（大洲）
    print(f"\n   3️⃣  地理分布 (Continent):")
    if "Continent" in df.columns:
        continent_counts = df["Continent"].drop_nulls().value_counts().sort("count", descending=True)
        print(f"      大洲数: {continent_counts.height}")
        for row in continent_counts.iter_rows():
            continent = row[0] if row[0] else "Unknown"
            count = row[1]
            print(f"         • {continent:<20} {count:>10,} 条")

    # 4. 国家/地区分布
    print(f"\n   4️⃣  国家/地区 (Country) - Top 15:")
    if "Country" in df.columns:
        country_counts = df["Country"].drop_nulls().value_counts().sort("count", descending=True)
        print(f"      不同国家/地区数: {country_counts.height}")
        for row in country_counts.head(15).iter_rows():
            country = row[0] if row[0] else "Unknown"
            count = row[1]
            print(f"         • {country:<30} {count:>10,} 条")

    # 5. 仪器类型
    print(f"\n   5️⃣  分析仪器:")
    if "Instrument" in df.columns:
        instrument_counts = df["Instrument"].drop_nulls().value_counts().sort("count", descending=True)
        for row in instrument_counts.iter_rows():
            instrument = row[0] if row[0] else "Unknown"
            count = row[1]
            print(f"         • {instrument:<40} {count:>10,} 条")

    # 6. 年龄范围
    print(f"\n   6️⃣  年龄范围 (Best Age):")
    if "Best Age" in df.columns:
        ages = df["Best Age"].drop_nulls()
        print(f"      有效年龄记录: {len(ages):,}")
        print(f"      最小年龄: {ages.min():.1f} Ma")
        print(f"      最大年龄: {ages.max():.1f} Ma")
        print(f"      平均年龄: {ages.mean():.1f} Ma")
        print(f"      中位数: {ages.median():.1f} Ma")

    # 数据完整性
    print(f"\n📋 数据完整性:")
    for col in df.columns:
        null_count = df[col].null_count()
        null_pct = null_count / df.height * 100
        if null_pct < 50:  # 只显示缺失率低于50%的列
            print(f"   • {col:<30} 缺失率: {null_pct:>5.1f}%")

    print(f"\n💡 常见分析维度:")
    print(f"   • 按时代分析: Cretaceous, Jurassic, Triassic, 等")
    print(f"   • 按岩石类型: detrital, igneous, 等")
    print(f"   • 按地理位置: Asia, Europe, North America, 或具体国家")
    print(f"   • 按年龄范围: 如 (100, 500) Ma")
    print(f"   • 组合查询: 时代 + 地区 + 岩石类型")

    print(f"\n🎯 建议的入门分析:")
    print(f"   1. 查询特定国家的数据 (如 China, USA)")
    print(f"   2. 分析特定时代的锆石 (如 Cretaceous)")
    print(f"   3. 对比不同地区的年龄分布")
    print(f"   4. 探索特定岩石类型的特征")

    print(f"\n{'='*70}")
    print(f"✅ 探索完成！现在您可以开始自己的分析了")
    print(f"{'='*70}")


if __name__ == "__main__":
    explore_dataset()
