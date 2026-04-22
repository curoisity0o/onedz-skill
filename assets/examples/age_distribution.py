#!/usr/bin/env python3
"""
================================================================================
✅ AI 友好示例 - 年龄分布分析（Age Distribution Analysis）
================================================================================

此示例已验证可直接运行，展示完整的年龄分布分析流程。

【AI 使用指南】
1. 这是一个完整的分析示例，包含多种可视化
2. 当用户需要"年龄分布分析"或"峰值检测"时，参考此示例
3. 可根据需要修改查询参数适应不同区域和时期

【关键 API】
- handler.query(periods=[...], continent=..., rock_class1=[...])  # 复杂查询
- handler.clean(df, concordance_min=0.90)  # 数据清洗
- handler.analyze(df_clean)  # 完整分析（返回 summary, peaks, kde 等）
- handler.plot_age(df, mode="kde", show_peaks=True)  # KDE 图 + 峰值标注
- handler.viz.plot_geographic_distribution(df, geo_level="country")  # 地理分布
- handler.viz.plot_rock_type_statistics(df, class_level="Class2")  # 岩石类型统计

【适用场景】
- ✅ 分析特定区域和时期的年龄分布
- ✅ 检测年龄峰值并标注
- ✅ 生成多种可视化图表
- ✅ 完整的统计分析

【代码位置】
完整代码: assets/examples/age_distribution.py
索引文件: assets/examples/examples_index.md

================================================================================

亚洲白垩纪碎屑锆石自动分析脚本
================================

此脚本由 OneDZ Skill 自动生成，执行完整的碎屑锆石分析工作流。

生成时间: 2026-04-20
任务: 亚洲白垩纪锆石分析
"""

import sys
from pathlib import Path

# 导入 OneDZ Handler
from scripts.onedz_handler import OneDZHandler


def main():
    print("=" * 70)
    print("🌏 亚洲白垩纪碎屑锆石分析 - OneDZ Skill 自动生成")
    print("=" * 70)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 第 1 步: 初始化并加载数据
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n📦 [1/5] 初始化 OneDZ Handler...")

    handler = OneDZHandler()
    handler.load(source="csv", table="global_u-pb")

    print(f"✅ 已加载全球 U-Pb 数据: {handler.data.height:,} 条记录")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 第 2 步: 查询目标数据
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n🔍 [2/5] 查询亚洲白垩纪碎屑锆石...")

    df = handler.query(
        periods=["Cretaceous"],      # 白垩纪 (145-66 Ma)
        rock_class1=["detrital"],    # 碎屑岩
        continent="Asia"             # 亚洲
    )

    print(f"✅ 查询结果: {df.height:,} 条记录")

    if df.height == 0:
        print("❌ 未找到匹配数据，分析终止。")
        return None

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 第 3 步: 科学级数据清洗
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n🧹 [3/5] 数据清洗 (协调度过滤 + 最佳年龄计算)...")

    df_clean = handler.clean(
        df,
        compute_best_age=True,        # 自动选择最佳年龄
        filter_concordance=True,      # 过滤不协调数据
        concordance_min=0.90,         # 90% 下限
        concordance_max=1.10,         # 110% 上限
        standardize_errors=True,      # 标准化误差
        target_sigma=1,               # 统一为 1σ
        remove_null_ages=True,        # 移除空值
        age_range=(0, 4500)           # 地球年龄范围
    )

    cleaning_rate = df_clean.height / df.height * 100
    print(f"✅ 清洗完成: {df.height:,} → {df_clean.height:,} 条记录")
    print(f"   清洗率: {cleaning_rate:.1f}%")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 第 4 步: 统计分析
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n📊 [4/5] 统计分析与峰值检测...")

    result = handler.analyze(df_clean)

    # 提取统计结果
    summary = result["summary"]
    peaks = result["peaks"]

    # 打印统计摘要
    print("\n   📈 基本统计:")
    print(f"      样本数:     {summary['n']:,}")
    print(f"      年龄范围:   {summary['min']:.1f} - {summary['max']:.1f} Ma")
    print(f"      平均年龄:   {summary['mean']:.1f} ± {summary['std']:.1f} Ma")
    print(f"      中位数:     {summary['median']:.1f} Ma")
    print(f"      四分位距:   {summary['q25']:.1f} - {summary['q75']:.1f} Ma")

    # 打印峰值信息
    if len(peaks) > 0:
        print(f"\n   🏔️  检测到 {len(peaks)} 个年龄峰值:")
        for i, peak in enumerate(peaks[:5], 1):
            print(f"      峰值 {i}: {peak['age']:.1f} ± {peak['uncertainty']:.1f} Ma")
    else:
        print("\n   ⚠️  未检测到明显峰值")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 第 5 步: 可视化与导出
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n🎨 [5/5] 生成可视化图表...")

    # 5.1 KDE 年龄分布图
    kde_file = "asia_cretaceous_kde.png"
    handler.plot_age(
        df_clean,
        mode="kde",
        age_range=(0, 4000),
        show_peaks=True,
        save=kde_file
    )
    print(f"   ✅ KDE 图: {kde_file}")

    # 5.2 地理分布图
    geo_file = "asia_cretaceous_geo.png"
    handler.viz.plot_geographic_distribution(
        df_clean,
        geo_level="country",
        top_n=15,
        save=geo_file
    )
    print(f"   ✅ 地理分布: {geo_file}")

    # 5.3 岩石类型统计 (Class-2)
    rock_file = "asia_cretaceous_rock.png"
    handler.viz.plot_rock_type_statistics(
        df_clean,
        class_level="Class2",
        plot_type="bar",
        top_n=10,
        save=rock_file
    )
    print(f"   ✅ 岩石类型: {rock_file}")

    # 5.4 导出清洗后的数据
    data_file = "asia_cretaceous_data.csv"
    handler.export(df_clean, data_file)
    print(f"   ✅ 数据导出: {data_file}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 最终摘要
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n" + "=" * 70)
    print("🎉 分析完成！")
    print("=" * 70)

    print(f"\n📁 生成文件:")
    print(f"   1. {kde_file}        - 年龄分布 KDE 图")
    print(f"   2. {geo_file}        - 地理分布图")
    print(f"   3. {rock_file}        - 岩石类型统计")
    print(f"   4. {data_file}        - 清洗后数据 (CSV)")

    print(f"\n📊 关键发现:")
    print(f"   • 有效样本: {summary['n']:,} 个")
    print(f"   • 年龄跨度: {summary['min']:.0f} - {summary['max']:.0f} Ma")
    print(f"   • 主要年龄: {summary['median']:.0f} Ma (中位数)")
    if len(peaks) > 0:
        print(f"   • 最大峰值: {peaks[0]['age']:.0f} ± {peaks[0]['uncertainty']:.0f} Ma")

    print(f"\n💡 提示:")
    print(f"   此脚本由 OneDZ Skill 自动生成")
    print(f"   可重复执行，结果完全可重现")
    print(f"   数据来源: Li et al. (2025) OneDZ Database")

    return {
        "df_clean": df_clean,
        "summary": summary,
        "peaks": peaks,
        "files": [kde_file, geo_file, rock_file, data_file]
    }


if __name__ == "__main__":
    result = main()
