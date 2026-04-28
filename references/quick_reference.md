# OneDZ API 快速参考（AI 专用）

> **最后更新**: 2026-04-28
> **用途**: AI 生成代码时的快速查询手册

---

## 💡 内存优化规则（重要）

> U-Pb 表 1.5 GB，全表加载需要 2-3 GB 内存，7.6 GB 机器容易 OOM。

### 默认使用惰性方法（不调 load()）

```python
# ✅ 推荐：惰性查询（~0.5 GB）
df_china = handler.query_from_csv(country_state="China")

# ✅ 推荐：惰性 join（~1 GB）
df_joined = handler.join_from_csv()
df_china_hf = handler.join_from_csv(upb_filters={"country_state":China"})

# ❌ 避免：全表加载（~4 GB，容易 OOM）
handler.load(source="csv", table="global_u-pb")
```

### 惰性 API

| 方法 | 用途 | 内存 | 参数 |
|------|------|------|------|
| `handler.query_from_csv(**kwargs)` | 惰性查询 | ~0.5 GB | 与 query() 完全一致 |
| `handler.join_from_csv(join_key, how, upb_filters)` | 惰性 join | ~1 GB | upb_filters 为可选过滤条件 |

### 何时使用 load() + query()

- 内存充足（>16 GB）
- 需要多次不同查询（>3 次）
- 需要 `handler.info()` 等依赖全表缓存的方法

---

## 🔥 最常用的 5 个 API

### 1. handler.query() - 数据查询

**完整签名**:
```python
df = handler.query(
    periods: List[str] = None,           # 地质时期
    epoch: str = None,                   # 世
    rock_class1: List[str] = None,       # 一级岩石分类
    rock_class2: List[str] = None,       # 二级岩石分类
    rock_class3: List[str] = None,       # 三级岩石分类
    region: str = None,                  # 区域
    continent: str = None,               # 大洲
    country_state: str = None,           # 国家/地区 ⭐ 注意参数名
    bbox: Tuple = None,                  # 边界框
    instruments: List[str] = None,       # 仪器类型
    age_range: Tuple = None,             # 年龄范围
    formation: str = None,               # 地层
    max_records: int = None              # 最大记录数
) -> pl.DataFrame
```

**常见用法**:
```python
# 按国家（⭐ 最常见）
df = handler.query(country_state="China")  # ✅ 单个字符串
# df = handler.query(countries=["China"])  # ❌ 错误：没有这个参数

# 按大洲
df = handler.query(continent="Asia")

# 按时期
df = handler.query(periods=["Cretaceous"])  # ⚠️ 列表

# 组合查询
df = handler.query(
    periods=["Cretaceous"],
    continent="Asia",
    rock_class1=["detrital"],
    age_range=(100, 150)
)
```

**⚠️ 参数陷阱**:
| 错误用法 | 正确用法 | 原因 |
|---------|---------|------|
| `countries=["China"]` | `country_state="China"` | 参数名错误 |
| `country_state=["China"]` | `country_state="China"` | 应该是字符串不是列表 |
| `period="Cretaceous"` | `periods=["Cretaceous"]` | 参数名 + 列表 |

**返回值**: `pl.DataFrame`
- 检查是否为空: `if df.height == 0:`

---

### 2. handler.clean() - 数据清洗

**完整签名**:
```python
df_clean = handler.clean(
    df: pl.DataFrame,
    compute_best_age: bool = True,       # 计算最佳年龄
    filter_concordance: bool = True,     # 过滤谐和度
    concordance_min: float = None,       # 谐和度下限（默认 0.90）
    concordance_max: float = None,       # 谐和度上限（默认 1.10）
    standardize_errors: bool = True,     # 标准化误差
    target_sigma: int = 1,               # 目标标准差
    remove_null_ages: bool = True,       # 移除空年龄
    age_range: Tuple = None              # 年龄范围
) -> pl.DataFrame
```

**常见用法**:
```python
# 标准清洗
df_clean = handler.clean(df, concordance_min=0.90)

# 严格清洗
df_clean = handler.clean(
    df,
    concordance_min=0.95,
    concordance_max=1.05
)

# 年龄范围过滤
df_clean = handler.clean(df, age_range=(0, 4500))
```

**典型清洗率**: 70-95%

---

### 3. handler.ks_test() - K-S 统计检验

**完整签名**:
```python
result = handler.ks_test(
    ages_a: np.ndarray,
    ages_b: np.ndarray,
    alpha: float = 0.05
) -> Dict
```

**返回值结构** ⭐ **重要**:
```python
{
    "statistic": float,     # ✅ D 统计量（注意键名！）
    "p_value": float,       # p 值
    "significant": bool,    # 是否显著差异
    "conclusion": str       # 结论文本描述
}
```

**常见用法**:
```python
# 准备数据
ages_china = df_china["Best Age"].drop_nulls().to_numpy()
ages_australia = df_australia["Best Age"].drop_nulls().to_numpy()

# K-S 检验
ks_result = handler.ks_test(ages_china, ages_australia)

# 访问结果 ⭐ 注意键名
d_stat = ks_result['statistic']    # ✅ 正确
# d_stat = ks_result['d_statistic'] # ❌ 错误：这个键不存在

p_val = ks_result['p_value']
is_sig = ks_result['significant']

print(f"D = {d_stat:.4f}, p = {p_val:.3e}")
print(f"结论: {ks_result['conclusion']}")
```

---

### 4. handler.plot_multi_kde() - 多样品 KDE 对比

**完整签名**:
```python
fig = handler.plot_multi_kde(
    data_dict: Dict[str, np.ndarray],  # 标签 -> 年龄数组
    age_range: Tuple = (0, 4000),
    save: str = None
) -> plt.Figure
```

**常见用法**:
```python
# 准备数据
ages_china = df_china["Best Age"].drop_nulls().to_numpy()
ages_australia = df_australia["Best Age"].drop_nulls().to_numpy()

# 画图
handler.plot_multi_kde(
    {"China": ages_china, "Australia": ages_australia},  # ⭐ 英文标签
    age_range=(0, 4000),
    save="comparison.png"
)
```

**⚠️ 标签陷阱**:
```python
# ✅ 正确 - 英文标签
{"China": ages, "Australia": ages_au}

# ⚠️ 可能有问题 - 中文标签（需要中文字体）
{"中国": ages, "澳大利亚": ages_au}
# 可能显示为方块
```

---

### 5. handler.analyze() - 年龄分布分析

**完整签名**:
```python
result = handler.analyze(
    df: pl.DataFrame,
    age_col: str = "Best Age"
) -> Dict
```

**返回值结构**:
```python
{
    "summary": Dict,      # 基本统计
    "peaks": List,        # 峰值列表
    "kde": Tuple,         # KDE 数据
    "bootstrap_mean": Dict # Bootstrap 均值
}
```

**常见用法**:
```python
# 分析
result = handler.analyze(df_clean)

# 提取统计
summary = result["summary"]
print(f"样本数: {summary['n']}")
print(f"平均值: {summary['mean']:.1f}")
print(f"中位数: {summary['median']:.1f}")

# 提取峰值
peaks = result["peaks"]
for i, peak in enumerate(peaks[:5], 1):
    print(f"峰值 {i}: {peak['age']:.1f} ± {peak['uncertainty']:.1f} Ma")
```

---

## 📋 其他重要 API

### handler.plot_age() - 单样品年龄分布

```python
handler.plot_age(
    df: pl.DataFrame,
    mode: str = "kde",                    # "kde" 或 "pdp"
    age_range: Tuple = (0, 4000),
    show_peaks: bool = True,
    save: str = None
)
```

**用法**:
```python
handler.plot_age(
    df_clean,
    mode="kde",
    age_range=(0, 4000),
    show_peaks=True,
    save="age_distribution.png"
)
```

---

### handler.join_upb_luhf() - 连接 U-Pb 和 Lu-Hf 表

```python
df_joined = handler.join_upb_luhf(
    join_key: str = "Ref_Sample_Key",  # "Ref_Sample_Key" 或 "Sample&Grain"
    how: str = "inner"
)
```

**前提**: 必须先加载两个表
```python
handler.load(source="csv", table="global_u-pb")
handler.load(source="csv", table="global_lu-hf")
df_joined = handler.join_upb_luhf()
```

---

### handler.compute_epsilon_hf() - 计算 εHf(t)

```python
df_computed = handler.compute_epsilon_hf(
    df: pl.DataFrame,
    hf_col: str = "176Hf/177Hf",
    lu_col: str = "176Lu/177Hf",
    age_col: str = "Best Age",
    compute_tdm: bool = True
)
```

---

## 🚨 错误对照表

### API 调用错误

| 错误信息 | 原因 | 正确做法 |
|---------|------|---------|
| `TypeError: query() got an unexpected keyword argument 'countries'` | 参数名错误 | 使用 `country_state` |
| `KeyError: 'd_statistic'` | 返回值键名错误 | 使用 `ks_result['statistic']` |
| `KeyError: 'BestAge'` | 列名错误 | 使用 `df["Best Age"]` |
| `AttributeError: 'OneDZHandler' object has no attribute 'data_path'` | 属性不存在 | 使用 `handler.config.csv_dir` |

### 数据类型错误

| 错误信息 | 原因 | 正确做法 |
|---------|------|---------|
| `Mean of empty slice` | 数据为空 | 检查 `if len(ages) > 0` |
| `DeprecationWarning: is_in ambiguous` | Polars 版本问题 | 添加 `strict=False` |
| `invalid value encountered in divide` | 除零或空数据 | 检查数据有效性 |

### 画图错误

| 错误信息 | 原因 | 正确做法 |
|---------|------|---------|
| `Glyph missing from font` | 缺少中文字体 | 使用英文标签 |
| 中文显示为方块 | 字体缺失 | 使用英文标签或安装中文字体 |

---

## 📐 常用数据列名

### U-Pb 数据
```python
"Best Age"          # 最佳年龄 ⭐
"Best Age 1S"       # 1σ 误差
"Best Age 2S"       # 2σ 误差
"206Pb/238U Age"    # 206Pb/238U 年龄
"207Pb/206Pb Age"   # 207Pb/206Pb 年龄
"Discord ratio"     # 谐和度比值
"Country_State"     # 国家/地区 ⭐
"Continent"         # 大洲
"Period"            # 地质时期
```

### Lu-Hf 数据
```python
"176Hf/177Hf"       # Hf 同位素比值
"176Lu/177Hf"       # Lu/Hf 比值
"εHf(t)"            # εHf(t) 值（计算后）
"TDM1", "TDM2"      # 地壳模式年龄（计算后）
```

---

## 🎯 代码模板

### 模板 1: 区域对比（最常用）

```python
from scripts.onedz_handler import OneDZHandler
import polars as pl

handler = OneDZHandler()
handler.load(source="csv", table="global_u-pb")

# 查询
df_china = handler.query(country_state="China")
df_australia = handler.query(country_state="Australia")

# 检查
if df_china.height == 0 or df_australia.height == 0:
    print("未找到数据")
    exit()

# 清洗
df_china_clean = handler.clean(df_china, concordance_min=0.90)
df_australia_clean = handler.clean(df_australia, concordance_min=0.90)

# 提取年龄
china_ages = df_china_clean["Best Age"].drop_nulls().to_numpy()
australia_ages = df_australia_clean["Best Age"].drop_nulls().to_numpy()

# K-S 检验
ks_result = handler.ks_test(china_ages, australia_ages)
print(f"D = {ks_result['statistic']:.4f}")
print(f"p = {ks_result['p_value']:.3e}")

# 画图
handler.plot_multi_kde(
    {"China": china_ages, "Australia": australia_ages},
    save="comparison.png"
)
```

### 模板 2: 单区域分析

```python
from scripts.onedz_handler import OneDZHandler

handler = OneDZHandler()
handler.load(source="csv", table="global_u-pb")

# 查询
df = handler.query(
    periods=["Cretaceous"],
    continent="Asia",
    rock_class1=["detrital"]
)

if df.height == 0:
    print("未找到数据")
    exit()

# 清洗
df_clean = handler.clean(df, concordance_min=0.90)

# 分析
result = handler.analyze(df_clean)
summary = result["summary"]
peaks = result["peaks"]

# 画图
handler.plot_age(df_clean, mode="kde", show_peaks=True, save="kde.png")
```

---

## 🔍 快速查找

### 我想...

| 需求 | 使用哪个 API | 参考 Example |
|------|-------------|-------------|
| 查询特定国家数据 | `handler.query(country_state=...)` | regional_comparison |
| 对比两个区域 | `handler.ks_test()` + `plot_multi_kde()` | regional_comparison |
| 分析年龄分布 | `handler.analyze()` + `plot_age()` | age_distribution |
| 计算谐和度 | `handler.clean()` | all examples |
| 分析 Hf 同位素 | `compute_epsilon_hf()` | luhf_analysis |
| 生成分析报告 | `AnalysisContext` + `ReportGenerator` | report_generation |
| 导出数据 | `handler.export()` | basic_query |

---

## 📞 文档导航

- **完整 API**: `references/api_reference.md`
- **工作流**: `references/workflows.md`
- **Example 索引**: `assets/examples/examples_index.md`

---

**最后提示**: 不确定时，先查 `examples_index.md` 找到匹配的 Example，复制其代码！
