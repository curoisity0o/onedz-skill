#!/usr/bin/env python3
"""
================================================================================
✅ AI 友好示例 - 基础查询（Basic Query）
================================================================================

此示例已验证可直接运行，适合第一次使用 OneDZ 的用户。

【AI 使用指南】
1. 这是最简单的示例，展示基本工作流
2. 当用户第一次使用或需要简单查询时，参考此示例
3. 代码简洁，易于理解和修改

【关键 API】
- handler.load(source="csv", table="global_u-pb")  # 加载数据
- handler.query(periods=[...], continent=..., rock_class1=[...])  # 多条件查询
- handler.clean(df, concordance_min=0.90)  # 数据清洗
- handler.export(df_clean, filename)  # 数据导出

【适用场景】
- ✅ 用户第一次使用 OneDZ
- ✅ 需要简单的数据查询和导出
- ✅ 学习基本 API 调用
- ✅ 了解 OneDZ 工作流程

【工作流程】
1. 初始化 Handler
2. 加载 U-Pb 数据
3. 执行查询（按时期、大洲、岩石类型）
4. 数据清洗
5. 基本统计
6. 导出数据

【常见查询方式】
- handler.query(periods=["Cretaceous"])  # 按时期
- handler.query(continent="Asia")  # 按大洲
- handler.query(rock_class1=["detrital"])  # 按岩石类型
- handler.query(country_state="China")  # 按国家
- handler.query(age_range=(100, 200))  # 按年龄范围

【代码位置】
完整代码: assets/examples/basic_query.py
索引文件: assets/examples/examples_index.md

================================================================================

OneDZ 基础查询示例

展示如何进行基本的数据查询和分析。

用法:
    python onedz-skill/assets/examples/basic_query.py

输出:
    - 查询结果统计
    - basic_query_output.csv (导出的数据)
"""

from scripts.onedz_handler import OneDZHandler

def main():
    print("=" * 60)
    print("OneDZ 基础查询示例")
    print("=" * 60)

    # 1. 初始化 Handler
    print("\n[1] 初始化 OneDZ Handler...")
    handler = OneDZHandler()
    print("✅ Handler 初始化成功")

    # 2. 加载数据
    print("\n[2] 加载 U-Pb 数据...")
    handler.load(source="csv", table="global_u-pb")
    print(f"✅ 数据加载成功，共 {len(handler.data):,} 条记录")

    # 3. 基础查询示例
    print("\n[3] 执行查询...")

    # 示例 1: 查询特定时期
    print("\n示例 1: 查询白垩纪数据")
    cretaceous = handler.query(periods=["Cretaceous"])
    print(f"  - 白垩纪记录: {len(cretaceous):,} 条")

    # 示例 2: 查询特定大洲
    print("\n示例 2: 查询亚洲数据")
    asia = handler.query(continent="Asia")
    print(f"  - 亚洲记录: {len(asia):,} 条")

    # 示例 3: 组合查询
    print("\n示例 3: 组合查询（白垩纪 + 亚洲 + 碎屑岩）")
    df = handler.query(
        periods=["Cretaceous"],
        continent="Asia",
        rock_class1=["detrital"]
    )
    print(f"  - 查询结果: {len(df):,} 条")

    # 4. 数据清洗
    print("\n[4] 数据清洗...")
    df_clean = handler.clean(
        df,
        concordance_min=0.90,
        concordance_max=1.10
    )
    print(f"  - 清洗前: {len(df):,} 条")
    print(f"  - 清洗后: {len(df_clean):,} 条")
    print(f"  - 过滤比例: {(1 - len(df_clean)/len(df))*100:.1f}%")

    # 5. 基本统计
    print("\n[5] 基本统计...")
    ages = df_clean["Best Age"].drop_nulls().to_numpy()
    print(f"  - 年龄范围: {ages.min():.1f} - {ages.max():.1f} Ma")
    print(f"  - 平均年龄: {ages.mean():.1f} Ma")
    print(f"  - 中位数年龄: {sorted(ages)[len(ages)//2]:.1f} Ma")

    # 6. 导出数据
    print("\n[6] 导出数据...")
    output_file = "basic_query_output.csv"
    handler.export(df_clean, output_file)
    print(f"✅ 数据已导出到: {output_file}")

    print("\n" + "=" * 60)
    print("✅ 分析完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
