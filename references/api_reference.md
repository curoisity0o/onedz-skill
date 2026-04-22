# OneDZ Handler API 完整参考

> **最后更新**: 2026-04-20
> **版本**: v1.1.0

---

## 快速导航

- [初始化](#初始化)
- [数据加载](#数据加载)
- [数据查询](#数据查询)
- [数据清洗](#数据清洗)
- [统计分析](#统计分析)
- [可视化](#可视化)
- [数据导出](#数据导出)
- [Lu-Hf 分析](#lu-hf-分析)

---

## 初始化

### OneDZHandler()

创建 OneDZ Handler 实例。

**语法**:
```python
from scripts.onedz_handler import OneDZHandler
handler = OneDZHandler(data_path=None)
```

**参数**:
- `data_path` (str, optional): OneDZ 数据路径。默认为 `~/my-OneDZ-skill/onedz_csv_*/`

**示例**:
```python
# 使用默认路径
handler = OneDZHandler()

# 指定路径
handler = OneDZHandler(data_path="/path/to/data/")
```

---

## 数据加载

### load()

加载 OneDZ 数据表。

**语法**:
```python
handler.load(source="csv", table="global_u-pb")
```

**参数**:
- `source` (str): 数据源类型，可选 `"csv"` 或 `"database"`
- `table` (str): 表名称
  - `"global_u-pb"`: U-Pb 年龄数据（默认）
  - `"global_lu-hf"`: Lu-Hf 同位素数据
- `path` (str, optional): 自定义数据文件路径

**返回值**: 无（数据存储在 `handler.data`）

**示例**:
```python
# 加载 U-Pb 数据
handler.load(source="csv", table="global_u-pb")

# 加载 Lu-Hf 数据
handler.load(source="csv", table="global_lu-hf")

# 加载两个表
handler.load(source="csv", table="global_u-pb")
handler.load(source="csv", table="global_lu-hf")
```

---

## 数据查询

### query()

多维度数据过滤。

**语法**:
```python
df = handler.query(
    periods=["Cretaceous"],
    rock_class1=["detrital"],
    continent="Asia"
)
```

**参数**:
- `periods` (list, optional): 地质时期列表，如 `["Cretaceous", "Jurassic"]`
- `epoch` (str, optional): 世，如 `"Early"`
- `rock_class1` (list, optional): 一级岩石分类
- `rock_class2` (list, optional): 二级岩石分类
- `rock_class3` (list, optional): 三级岩石分类
- `region` (str, optional): 主要区域
- `continent` (str, optional): 大洲，如 `"Asia"`
- `country_state` (str, optional): 国家/地区
- `formation` (str, optional): 地层组/组名
- `bbox` (tuple, optional): 边界框 `(min_lon, min_lat, max_lon, max_lat)`
- `instruments` (list, optional): 仪器类型，如 `["LA_ICP_MS", "SIMS"]`
- `age_range` (tuple, optional): 年龄范围 `(min_age, max_age)`
- `max_records` (int, optional): 最大返回记录数

**返回值**: `polars.DataFrame` - 查询结果

**示例**:
```python
# 按时期和大洲查询
df = handler.query(periods=["Cretaceous"], continent="Asia")

# 按岩石类型查询
df = handler.query(rock_class1=["detrital"])

# 地理边界框查询
df = handler.query(bbox=(100, 20, 120, 40))

# 多条件组合查询
df = handler.query(
    periods=["Cretaceous"],
    rock_class1=["detrital"],
    continent="Asia",
    age_range=(100, 150)
)
```

---

## 数据清洗

### clean()

科学级数据质量控制。

**语法**:
```python
df_clean = handler.clean(
    df,
    compute_best_age=True,
    filter_concordance=True,
    concordance_min=0.90,
    concordance_max=1.10
)
```

**参数**:
- `df` (DataFrame): 输入数据
- `compute_best_age` (bool): 是否计算最佳年龄（默认 `True`）
- `filter_concordance` (bool): 是否过滤谐和度（默认 `True`）
- `concordance_min` (float): 最小谐和度（默认 `0.90`）
- `concordance_max` (float): 最大谐和度（默认 `1.10`）
- `standardize_errors` (bool): 是否标准化误差（默认 `True`）
- `target_sigma` (int): 目标误差标准（1 或 2σ，默认 `1`）
- `remove_null_ages` (bool): 是否移除缺失年龄（默认 `True`）
- `age_range` (tuple): 年龄范围过滤 `(min, max)`，默认 `(0, 4000)`

**返回值**: `polars.DataFrame` - 清洗后的数据

**示例**:
```python
# 基础清洗
df_clean = handler.clean(df)

# 严格质量控制
df_clean = handler.clean(
    df,
    concordance_min=0.95,
    concordance_max=1.05,
    age_range=(0, 3000)
)

# 不过滤谐和度
df_clean = handler.clean(df, filter_concordance=False)
```

---

## 统计分析

### analyze()

综合分布分析。

**语法**:
```python
result = handler.analyze(df_clean)
```

**参数**:
- `df` (DataFrame): 输入数据

**返回值**: `dict` - 包含以下键：
- `"summary"`: 基本统计信息
- `"peaks"`: 检测到的峰值
- `"kde"`: KDE 曲线数据

### kde()

核密度估计。

**语法**:
```python
x, y = handler.kde(ages, bandwidth=None)
```

**参数**:
- `ages` (array): 年龄数据
- `bandwidth` (float, optional): 带宽，`None` 表示自适应

**返回值**: `tuple` - (x 坐标, y 密度)

### bootstrap()

自助法重采样。

**语法**:
```python
bs_result = handler.bootstrap(ages, statistic="kde", n_iterations=1000)
```

**参数**:
- `ages` (array): 年龄数据
- `statistic` (str): 统计量，`"kde"` 或 `"mean"`
- `n_iterations` (int): 迭代次数

**返回值**: `dict` - 包含均值、置信区间等

### ks_test()

Kolmogorov-Smirnov 检验。

**语法**:
```python
ks_result = handler.ks_test(ages_a, ages_b, alpha=0.05)
```

**参数**:
- `ages_a` (array): 样本 A
- `ages_b` (array): 样本 B
- `alpha` (float): 显著性水平（默认 `0.05`）

**返回值**: `dict` - 包含统计量和 p 值

---

## 可视化

### plot_age()

年龄分布图。

**语法**:
```python
handler.plot_age(df, mode="kde", age_range=(0, 4000), save="plot.png")
```

**参数**:
- `df` (DataFrame): 输入数据
- `mode` (str): 图形类型，`"kde"` 或 `"pdp"`
- `age_range` (tuple): 年龄范围
- `save` (str): 保存路径

### plot_multi_kde()

多样本 KDE 对比。

**语法**:
```python
handler.plot_multi_kde(
    {"Sample_A": ages_a, "Sample_B": ages_b},
    age_range=(0, 4000),
    save="multi_kde.png"
)
```

### plot_rock_type_statistics()

岩石类型统计图（Phase 5 新增）。

**语法**:
```python
handler.viz.plot_rock_type_statistics(
    handler.data,
    class_level="Class1",
    plot_type="bar",
    top_n=15,
    save="rock_stats.png"
)
```

**参数**:
- `class_level` (str): 分类级别，`"Class1"`, `"Class2"`, `"Class3"`
- `plot_type` (str): 图形类型，`"bar"` 或 `"pie"`
- `top_n` (int): 显示前 N 个类别

### plot_geographic_distribution()

地理分布图（Phase 5 新增）。

**语法**:
```python
handler.viz.plot_geographic_distribution(
    handler.data,
    geo_level="continent",
    top_n=10,
    save="geo_dist.png"
)
```

**参数**:
- `geo_level` (str): 地理级别，`"continent"`, `"major"`, `"minor"`, `"country"`
- `top_n` (int): 显示前 N 个

### plot_temporal_distribution()

时间分布图（Phase 5 新增）。

**语法**:
```python
handler.viz.plot_temporal_distribution(
    handler.data,
    save="temporal_dist.png"
)
```

---

## 数据导出

### export()

多格式数据导出。

**语法**:
```python
handler.export(df, "output.csv")
```

**参数**:
- `df` (DataFrame): 要导出的数据
- `path` (str): 输出路径（扩展名决定格式）

**支持的格式**:
- `.csv`: CSV 格式
- `.xlsx`: Excel 格式
- `.json`: JSON 格式
- `.geojson`: GeoJSON 格式（用于 QGIS/ArcGIS）
- `.shp`: Shapefile 格式（用于 GIS 软件）

**示例**:
```python
# CSV
handler.export(df, "result.csv")

# Excel
handler.export(df, "result.xlsx")

# GeoJSON
handler.export(df, "result.geojson")

# Shapefile
handler.export(df, "result.shp")
```

---

## Lu-Hf 分析

### join_upb_luhf()

连接 U-Pb 和 Lu-Hf 表。

**语法**:
```python
df_joined = handler.join_upb_luhf(join_key="Ref_Sample_Key")
```

**参数**:
- `join_key` (str): 连接键，默认 `"Ref_Sample_Key"`

**返回值**: `polars.DataFrame` - 连接后的数据

### compute_epsilon_hf()

计算 εHf(t) 和 TDM。

**语法**:
```python
df_computed = handler.compute_epsilon_hf(df_joined)
```

**参数**:
- `df` (DataFrame): 包含 Lu-Hf 数据的表

**返回值**: `polars.DataFrame` - 添加了 εHf(t) 和 TDM 列

### plot_epsilon_hf()

εHf(t) 演化图。

**语法**:
```python
handler.plot_epsilon_hf(df, save="epsilon_hf.png")
```

**参数**:
- `df` (DataFrame): 包含 εHf(t) 的数据
- `save` (str): 保存路径
- `color_by` (str, optional): 颜色分组列名

### plot_tdm()

TDM 模式年龄分布。

**语法**:
```python
handler.plot_tdm(df, model="dm1", save="tdm_dist.png")
```

**参数**:
- `df` (DataFrame): 包含 TDM 的数据
- `model` (str): `"dm1"` 或 `"dm2"`
- `save` (str): 保存路径

---

## CLI 命令

详见 [CLI 指南](cli_guide.md)。

---

**维护者**: OneDZ Handler Team
**反馈**: 请提交 Issue 或 PR
