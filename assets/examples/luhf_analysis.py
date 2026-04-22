#!/usr/bin/env python3
"""
OneDZ Lu-Hf 同位素分析示例

展示如何进行 Lu-Hf 同位素数据处理和可视化。

用法:
    python onedz-skill/assets/examples/luhf_analysis.py

输出:
    - luhf_joined.csv (连接后的数据)
    - luhf_computed.csv (计算 εHf 后的数据)
    - luhf_epsilon_hf.png (εHf 演化图)
    - luhf_tdm1_dist.png (TDM1 分布图)
"""

from scripts.onedz_handler import OneDZHandler

def main():
    print("=" * 60)
    print("OneDZ Lu-Hf 同位素分析示例")
    print("=" * 60)

    # 1. 初始化
    print("\n[1] 初始化 OneDZ Handler...")
    handler = OneDZHandler()
    print("✅ Handler 初始化成功")

    # 2. 加载两个表
    print("\n[2] 加载 U-Pb 和 Lu-Hf 数据...")
    handler.load(source="csv", table="global_u-pb")
    handler.load(source="csv", table="global_lu-hf")
    print("✅ 数据加载成功")

    # 3. 连接表
    print("\n[3] 连接 U-Pb 和 Lu-Hf 表...")
    df_joined = handler.join_upb_luhf(join_key="Ref_Sample_Key")
    print(f"✅ 连接成功，共 {len(df_joined):,} 条记录")

    # 4. 过滤数据（示例：亚洲侏罗纪）
    print("\n[4] 过滤数据（亚洲侏罗纪）...")
    df_filtered = handler.query(
        df_joined,
        periods=["Jurassic"],
        continent="Asia"
    )
    print(f"✅ 过滤后 {len(df_filtered):,} 条记录")

    # 5. 计算 εHf(t) 和 TDM
    print("\n[5] 计算 εHf(t) 和 TDM...")
    df_computed = handler.compute_epsilon_hf(df_filtered)
    print(f"✅ 计算完成")

    # 显示 εHf 统计
    if "epsilon_Hf" in df_computed.columns:
        epsilon_hf = df_computed["epsilon_Hf"].drop_nulls().to_numpy()
        print(f"  - εHf 范围: {epsilon_hf.min():.1f} ~ {epsilon_hf.max():.1f}")
        print(f"  - εHf 平均: {epsilon_hf.mean():.1f}")

    # 6. 导出连接后的数据
    print("\n[6] 导出数据...")
    handler.export(df_joined, "luhf_joined.csv")
    handler.export(df_computed, "luhf_computed.csv")
    print("✅ 数据已导出")

    # 7. 可视化
    print("\n[7] 生成可视化...")

    # εHf(t) 演化图
    print("  - 生成 εHf(t) 演化图...")
    handler.plot_epsilon_hf(
        df_computed,
        save="luhf_epsilon_hf.png"
    )
    print("    ✅ luhf_epsilon_hf.png")

    # TDM1 分布图
    print("  - 生成 TDM1 分布图...")
    handler.plot_tdm(
        df_computed,
        model="dm1",
        save="luhf_tdm1_dist.png"
    )
    print("    ✅ luhf_tdm1_dist.png")

    # εHf 分布直方图
    print("  - 生成 εHf 分布直方图...")
    handler.plot_epsilon_hf_distribution(
        df_computed,
        save="luhf_epsilon_hf_dist.png"
    )
    print("    ✅ luhf_epsilon_hf_dist.png")

    print("\n" + "=" * 60)
    print("✅ Lu-Hf 分析完成！")
    print("=" * 60)
    print("\n输出文件:")
    print("  - luhf_joined.csv")
    print("  - luhf_computed.csv")
    print("  - luhf_epsilon_hf.png")
    print("  - luhf_tdm1_dist.png")
    print("  - luhf_epsilon_hf_dist.png")

if __name__ == "__main__":
    main()
