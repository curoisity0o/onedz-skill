# OneDZ 常见工作流示例

> **最后更新**: 2026-04-20
> **难度**: 初级到中级
> **预计时间**: 每个 workflow 5-15 分钟

---

## 工作流导航

- [工作流 1: 区域年龄谱](#工作流-1-区域年龄谱) - 基础
- [工作流 2: Lu-Hf 同位素演化](#工作流-2-lu-hf-同位素演化) - 中级
- [工作流 3: 区域对比分析](#工作流-3-区域对比分析) - 中级
- [工作流 4: 统计探索](#工作流-4-统计探索) - 中级
- [工作流 5: CLI 管道](#工作流-5-cli-管道) - 高级
- [工作流 6: 论文图表复现](#工作流-6-论文图表复现) - 高级

---

## 工作流 1: 区域年龄谱

**目标**: 生成特定区域和时期的年龄分布图

**难度**: ⭐ 初级
**时间**: 5 分钟

### 完整脚本

```python
from scripts.onedz_handler import OneDZHandler

# 1. 初始化
handler = OneDZHandler()

# 2. 加载数据
handler.load(source="csv", table="global_u-pb")

# 3. 查询数据 - 亚洲白垩纪碎屑锆石
df = handler.query(
    periods=["Cretaceous"],
    rock_class1=["detrital"],
    continent="Asia"
)

print(f"查询到 {len(df)} 条记录")

# 4. 清洗数据
df_clean = handler.clean(
    df,
    concordance_min=0.90,
    concordance_max=1.10,
    age_range=(0, 4000)
)

print(f"清洗后 {len(df_clean)} 条记录")

# 5. 可视化
handler.plot_age(
    df_clean,
    mode="kde",
    age_range=(0, 4000),
    save="asia_cretaceous_kde.png"
)

# 6. 导出数据
handler.export(df_clean, "asia_cretaceous.csv")

print("✅ 完成！")
print("- 图表: asia_cretaceous_kde.png")
print("- 数据: asia_cretaceous.csv")
```

### 输出

- **图表**: `asia_cretaceous_kde.png` - 年龄概率密度图
- **数据**: `asia_cretaceous.csv` - 清洗后的数据

### 变体

```python
# 不同区域
df = handler.query(continent="Europe", periods=["Jurassic"])

# 不同岩石类型
df = handler.query(rock_class1=["igneous"])

# 年龄范围过滤
df = handler.query(age_range=(100, 200))
```

---

## 工作流 2: Lu-Hf 同位素演化

**目标**: 分析锆石 Hf 同位素演化特征

**难度**: ⭐⭐ 中级
**时间**: 10 分钟

### 完整脚本

```python
from scripts.onedz_handler import OneDZHandler

# 1. 初始化
handler = OneDZHandler()

# 2. 加载两个表
handler.load(source="csv", table="global_u-pb")
handler.load(source="csv", table="global_lu-hf")

# 3. 连接表
df_joined = handler.join_upb_luhf(join_key="Ref_Sample_Key")
print(f"连接后 {len(df_joined)} 条记录")

# 4. 过滤数据
df_filtered = handler.query(
    df_joined,
    periods=["Jurassic"],
    continent="Asia"
)

# 5. 计算 εHf(t) 和 TDM
df_computed = handler.compute_epsilon_hf(df_filtered)

# 6. 可视化
# εHf(t) 演化图
handler.plot_epsilon_hf(
    df_computed,
    save="jurassic_epsilon_hf.png"
)

# εHf(t) 分布直方图
handler.plot_epsilon_hf_distribution(
    df_computed,
    save="jurassic_epsilon_hf_dist.png"
)

# TDM 分布
handler.plot_tdm(
    df_computed,
    model="dm1",
    save="jurassic_tdm1_dist.png"
)

# 7. 导出
handler.export(df_computed, "jurassic_luhf.csv")

print("✅ 完成！")
```

### 输出

- `jurassic_epsilon_hf.png` - εHf(t) vs Age 图
- `jurassic_epsilon_hf_dist.png` - εHf(t) 分布直方图
- `jurassic_tdm1_dist.png` - TDM1 分布
- `jurassic_luhf.csv` - 完整数据

---

## 工作流 3: 区域对比分析

**目标**: 统计学对比两个区域的年龄分布

**难度**: ⭐⭐ 中级
**时间**: 15 分钟

### 完整脚本

```python
from scripts.onedz_handler import OneDZHandler
import matplotlib.pyplot as plt

# 1. 初始化
handler = OneDZHandler()
handler.load()

# 2. 查询两个区域
df_asia = handler.query(
    periods=["Cretaceous"],
    continent="Asia"
)

df_europe = handler.query(
    periods=["Cretaceous"],
    continent="Europe"
)

# 3. 清洗并提取年龄
ages_asia = handler.clean(df_asia)["Best Age"].drop_nulls().to_numpy()
ages_europe = handler.clean(df_europe)["Best Age"].drop_nulls().to_numpy()

print(f"亚洲: {len(ages_asia)} 条年龄")
print(f"欧洲: {len(ages_europe)} 条年龄")

# 4. Kolmogorov-Smirnov 检验
ks_result = handler.ks_test(ages_asia, ages_europe, alpha=0.05)

print("\nK-S 检验结果:")
print(f"统计量: {ks_result['statistic']:.4f}")
print(f"p值: {ks_result['p_value']:.4e}")
print(f"显著性差异: {'是' if ks_result['significant'] else '否'}")

# 5. 对比 KDE 图
handler.plot_multi_kde(
    {"Asia": ages_asia, "Europe": ages_europe},
    age_range=(0, 4000),
    save="asia_europe_comparison.png"
)

print("\n✅ 完成！")
print("- 对比图: asia_europe_comparison.png")
```

### 输出

- **K-S 检验结果**: 统计量、p 值、是否显著差异
- **对比图**: `asia_europe_comparison.png`

---

## 工作流 4: 统计探索（Phase 5 新增）

**目标**: 生成统计可视化图表

**难度**: ⭐⭐ 中级
**时间**: 10 分钟

### 完整脚本

```python
from scripts.onedz_handler import OneDZHandler

# 1. 初始化
handler = OneDZHandler()
handler.load(source="csv")

# 2. 岩石类型统计
handler.viz.plot_rock_type_statistics(
    handler.data,
    class_level="Class1",
    plot_type="bar",
    top_n=15,
    save="figure_rock_type_stats.png"
)

# 3. 地理分布
handler.viz.plot_geographic_distribution(
    handler.data,
    geo_level="continent",
    top_n=10,
    save="figure_geo_distribution.png"
)

# 4. 时间分布
handler.viz.plot_temporal_distribution(
    handler.data,
    save="figure_temporal_distribution.png"
)

print("✅ 完成！")
print("- 岩石类型统计: figure_rock_type_stats.png")
print("- 地理分布: figure_geo_distribution.png")
print("- 时间分布: figure_temporal_distribution.png")
```

### 输出

- `figure_rock_type_stats.png` - 岩石类型条形图
- `figure_geo_distribution.png` - 地理分布图
- `figure_temporal_distribution.png` - 时间分布图

---

## 工作流 5: CLI 管道

**目标**: 使用命令行工具进行批量分析

**难度**: ⭐⭐⭐ 高级
**时间**: 5 分钟

### 完整命令

```bash
# 查询亚洲白垩纪数据
onedz query \
  --period Cretaceous \
  --continent Asia \
  -o asia_raw.csv

# 清洗数据
onedz clean \
  --input asia_raw.csv \
  --concordance-min 0.90 \
  -o asia_clean.csv

# 生成 KDE 图
onedz plot \
  --input asia_clean.csv \
  --plot-type kde \
  -o asia_kde.png

# 或使用管道
onedz query --period Cretaceous --continent Asia | \
onedz clean --concordance-min 0.90 | \
onedz plot --plot-type kde -o asia_kde.png
```

### 批量处理

```bash
# 批量生成多个时期的图
for period in Triassic Jurassic Cretaceous; do
  onedz query --period $period -o ${period}.csv
  onedz plot --input ${period}.csv --plot-type kde -o ${period}_kde.png
done
```

---

## 工作流 6: 论文图表复现

**目标**: 生成 Li et al. (2025) 论文中的所有图表

**难度**: ⭐⭐⭐ 高级
**时间**: 30 分钟

### 方法 1: 使用脚本

```python
from scripts.onedz_handler import OneDZHandler

handler = OneDZHandler()
handler.load()

# 生成所有图表
handler.viz.plot_rock_type_statistics(handler.data, class_level="Class1")
handler.viz.plot_geographic_distribution(handler.data, geo_level="continent")
handler.viz.plot_temporal_distribution(handler.data)

print("✅ 所有图表已生成")
```

### 方法 2: 使用专用脚本

```bash
python demo/paper_figures/generate_paper_figures.py
```

### 输出

- Figure 3: 地理和时间分布
- Figure 5: 岩石类型统计
- 所有图表保存为高分辨率 PNG

---

## 通用技巧

### 技巧 1: 查看可用数据

```python
# 查看所有地质时期
print(handler.data["Period"].unique())

# 查看所有岩石类型
print(handler.data["Rock_Class1"].unique())

# 查看所有大洲
print(handler.data["Continent"].unique())
```

### 技巧 2: 保存中间结果

```python
# 保存清洗后的数据
handler.export(df_clean, "intermediate_clean.csv")

# 下次直接加载
df_clean = handler.load(source="csv", path="intermediate_clean.csv")
```

### 技巧 3: 批量处理

```python
regions = ["Asia", "Europe", "North_America"]

for region in regions:
    df = handler.query(continent=region, periods=["Cretaceous"])
    df_clean = handler.clean(df)
    handler.plot_age(df_clean, save=f"{region.lower()}_kde.png")
```

### 技巧 4: 自定义图表

```python
import matplotlib.pyplot as plt

# 使用 Handler 的数据，自定义绘图
ages = df_clean["Best Age"].to_numpy()

plt.figure(figsize=(10, 6))
plt.hist(ages, bins=50, density=True, alpha=0.7)
plt.xlabel("Age (Ma)")
plt.ylabel("Probability Density")
plt.title("Custom Age Distribution")
plt.savefig("custom_plot.png")
```

---

## 常见问题

### Q: 如何加速大数据集的处理？

**A**: 使用 `max_records` 限制查询范围：
```python
df = handler.query(periods=["Cretaceous"], max_records=100000)
```

### Q: 如何生成出版级质量的图？

**A**: 调整 DPI 和图像尺寸：
```python
handler.plot_age(df, save="figure.png", dpi=300, figsize=(12, 8))
```

### Q: 如何分析特定样品？

**A**: 使用样品名称过滤：
```python
df = handler.query(formation="Yixian Formation")
```

---

**下一步**: 查看 [API 参考](api_reference.md) 了解更多方法
