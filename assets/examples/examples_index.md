# Examples 快速索引（AI 专用）

> 💡 **AI 使用指南**: 当用户提出需求时，先查找此文件匹配最相关的 example，然后读取对应的 .py 文件参考实现。

> **最后更新**: 2026-04-22
> **版本**: 1.1.0

---

## 🎯 快速匹配表

| 用户需求描述 | 最佳 Example | 文件名 | 难度 | 关键 API |
|-------------|-------------|--------|-----|---------|
| 对比两个区域/国家的锆石数据 | `regional_comparison` | regional_comparison.py | ⭐⭐ | query, ks_test, plot_multi_kde |
| K-S 统计检验 | `regional_comparison` | regional_comparison.py | ⭐⭐ | ks_test |
| **按时期分组对比** | **`grouped_comparison`** | **grouped_comparison.py** | ⭐⭐⭐ | query, clean, analyze, ks_test, plot_multi_kde |
| **按岩石类型分组对比** | **`grouped_comparison`** | **grouped_comparison.py** | ⭐⭐⭐ | grouped_comparison (改 GROUP_COLUMN) |
| **按大洲分组对比** | **`grouped_comparison`** | **grouped_comparison.py** | ⭐⭐⭐ | grouped_comparison (不设 QUERY_PARAMS) |
| **任意维度分组** | **`grouped_comparison`** | **grouped_comparison.py** | ⭐⭐⭐ | 改 GROUP_COLUMN + GROUP_VALUES |
| 年龄分布 KDE 图 | `age_distribution` | age_distribution.py | ⭐⭐ | analyze, plot_age |
| 峰值检测 | `age_distribution` | age_distribution.py | ⭐⭐ | analyze (peaks) |
| 基础数据查询 | `basic_query` | basic_query.py | ⭐ | query, export |
| 学习基本用法 | `basic_query` | basic_query.py | ⭐ | - |
| Lu-Hf 同位素分析 | `luhf_analysis` | luhf_analysis.py | ⭐⭐⭐ | join_upb_luhf, compute_epsilon_hf |
| εHf(t) 计算 | `luhf_analysis` | luhf_analysis.py | ⭐⭐⭐ | compute_epsilon_hf |
| 地理分布图 | `age_distribution` | age_distribution.py | ⭐⭐ | plot_geographic_distribution |
| 谐和度质量控制 | `concordance_qc` | concordance_qc.py | ⭐⭐ | compute_concordance, filter_concordance |
| 物源综合判别 (U-Pb+Lu-Hf) | `provenance_analysis` | provenance_analysis.py | ⭐⭐⭐ | query_from_csv + engine.luhf |
| 不确定查询参数是否有效 | **查 dataset JSON** | onedz_dataset_structure.json | - | - |

---

## 🔄 组合场景建议

当用户需求不能直接匹配单个 Example 时，按以下方式组合：

| 用户需求 | 主 Example | 修改方式 |
|---------|-----------|---------|
| "中国不同地质时期对比" | `grouped_comparison` | QUERY_PARAMS={country_state="China"}, GROUP_COLUMN="Depos.Age (Period)" |
| "亚洲各国锆石对比" | `grouped_comparison` | QUERY_PARAMS={continent="Asia"}, GROUP_COLUMN="Country_State", GROUP_VALUES=None (自动检测) |
| "全球火成岩 vs 沉积岩" | `grouped_comparison` | QUERY_PARAMS={}, GROUP_COLUMN="Class-1 Rock Type" |
| "某区域白垩纪 vs 侏罗纪" | `regional_comparison` | 两次 query(periods=[...]) 分别查询 |
| "某区域全面分析+Lu-Hf" | `age_distribution` + `luhf_analysis` | 先 age_distribution 做年龄分析，再 luhf_analysis 做 Hf 分析 |
| "按年龄区间分段统计" | `grouped_comparison` | GROUP_COLUMN 换成用 age_range 分桶 |

---

## 📁 Example 详细说明

### 1. basic_query - 基础查询

**使用场景**：
- ✅ 用户第一次使用 OneDZ
- ✅ 简单的数据查询和导出
- ✅ 学习基本 API 调用

**关键代码模式**：
```python
# 初始化
handler = OneDZHandler()
handler.load(source="csv", table="global_u-pb")

# 查询（多种方式）
df = handler.query(
    periods=["Cretaceous"],      # 按时期
    continent="Asia",             # 按大洲
    rock_class1=["detrital"]      # 按岩石类型
)

# 清洗
df_clean = handler.clean(df, concordance_min=0.90)

# 导出
handler.export(df_clean, "output.csv")
```

**文件**: `basic_query.py`

---

### 2. regional_comparison - 区域对比（⭐ 重点推荐）

**使用场景**：
- ✅ **对比中国和澳大利亚**（这是最常见的问题！）
- ✅ 任何两个区域的锆石数据对比
- ✅ K-S 统计检验验证差异显著性
- ✅ 生成对比 KDE 图

**关键代码模式**：
```python
# ✅ 正确的查询方式
df_china = handler.query(country_state="China")  # 注意：不是 'countries'
df_australia = handler.query(country_state="Australia")

# 清洗
df_china_clean = handler.clean(df_china, concordance_min=0.90)
df_australia_clean = handler.clean(df_australia, concordance_min=0.90)

# 提取年龄（注意列名）
china_ages = df_china_clean["Best Age"].drop_nulls().to_numpy()  # 是 'Best Age' 不是 'BestAge'
australia_ages = df_australia_clean["Best Age"].drop_nulls().to_numpy()

# ✅ K-S 检验 - 注意返回值键名
ks_result = handler.ks_test(china_ages, australia_ages)
print(f"D-statistic: {ks_result['statistic']}")  # ✅ 正确：'statistic'
# print(f"D-statistic: {ks_result['d_statistic']}")  # ❌ 错误：没有这个键

# 对比图
handler.plot_multi_kde(
    {"China": china_ages, "Australia": australia_ages},  # 使用英文标签
    save="comparison.png"
)
```

**⚠️ 常见错误修正**：
| 错误用法 | 正确用法 | 说明 |
|---------|---------|------|
| `handler.query(countries=["China"])` | `handler.query(country_state="China")` | 参数名错误 |
| `ks_result['d_statistic']` | `ks_result['statistic']` | 返回值键名错误 |
| `df["BestAge"]` | `df["Best Age"]` | 列名错误 |
| 直接处理 | `if df.height > 0:` 检查 | 未检查空数据 |
| `{"中国": ages}` | `{"China": ages}` | 中文标签可能显示异常 |

**文件**: `regional_comparison.py`

---

### 3. age_distribution - 年龄分布分析

**使用场景**：
- ✅ 分析特定区域和时期的年龄分布
- ✅ 生成 KDE 图并标注峰值
- ✅ 多种可视化组合（地理分布、岩石类型统计）

**关键代码模式**：
```python
# 复杂查询
df = handler.query(
    periods=["Cretaceous"],
    rock_class1=["detrital"],
    continent="Asia"
)

# 完整分析
result = handler.analyze(df_clean)
summary = result["summary"]  # 基本统计
peaks = result["peaks"]      # 峰值列表

# 多种图表
handler.plot_age(df_clean, mode="kde", show_peaks=True)  # KDE + 峰值
handler.viz.plot_geographic_distribution(df_clean, geo_level="country")  # 地理分布
handler.viz.plot_rock_type_statistics(df_clean, class_level="Class2")  # 岩石类型
```

**文件**: `age_distribution.py`

---

### 4. luhf_analysis - Lu-Hf 同位素分析

**使用场景**：
- ✅ Hf 同位素组成分析
- ✅ εHf(t) 演化趋势
- ✅ 地壳模式年龄（TDM）计算

**关键代码模式**：
```python
# 加载两个表
handler.load(source="csv", table="global_u-pb")
handler.load(source="csv", table="global_lu-hf")

# 表连接
df_joined = handler.join_upb_luhf(join_key="Ref_Sample_Key")

# 计算 εHf(t) 和 TDM
df_computed = handler.compute_epsilon_hf(df_joined)

# 可视化
handler.plot_epsilon_hf(df_computed, save="epsilon_hf.png")
handler.plot_tdm(df_computed, save="tdm.png")
```

**文件**: `luhf_analysis.py`

---

### 5. concordance_qc - 谐和度质量控制

**使用场景**：
- ✅ 评估不同谐和度阈值下的数据保留率
- ✅ 多阈值对比分析（宽松/标准/严格）
- ✅ 数据质量评估

**关键代码模式**：
```python
handler = OneDZHandler()
df = handler.query_from_csv(continent="Asia", rock_class1=["detrital"])
df_conc = handler.qc.compute_concordance(df)

# 不同阈值对比
for lo, hi in [(0.80, 1.20), (0.90, 1.10), (0.95, 1.05)]:
    df_filt = handler.qc.filter_concordance(df_conc, concordance_min=lo, concordance_max=hi)
    print(f"  {lo}-{hi}: {df_filt.height:,} ({df_filt.height/df.height*100:.1f}%)")

handler.plot_multi_kde(age_data, save="concordance_comparison.png")
```

**文件**: `concordance_qc.py`

---

### 6. provenance_analysis - 物源综合判别（U-Pb + Lu-Hf）

**使用场景**：
- ✅ 综合利用 U-Pb 年龄峰和 Lu-Hf εHf(t) 判别物源
- ✅ 古老地壳再循环 vs 新生地壳判别
- ✅ 内存友好的两阶段分析

**关键代码模式**：
```python
# Phase 1: U-Pb (lazy, ~0.5 GB)
df_upb = handler.query_from_csv(country_state="China", rock_class1=["detrital"])
df_clean = handler.clean(df_upb, concordance_min=0.90)
result = handler.analyze(df_clean)  # peaks + summary

# Free U-Pb memory
handler.engine._upb_df = None
gc.collect()

# Phase 2: Lu-Hf (direct table, ~0.2 GB)
handler.load(source="csv", table="global_lu-hf")
luhf = handler.engine.luhf
df_luhf = luhf.filter(pl.col("Country_State") == "China")
df_valid = df_luhf.drop_nulls(subset=["εHf(t)", "U-Pb Age (Ma)"])

# εHf(t) is PRE-COMPUTED in the Lu-Hf table
eps = df_valid["εHf(t)"].cast(pl.Float64).to_numpy()
```

**重要提醒**：
- εHf(t) 在 Lu-Hf 表中已预计算，无需再调 compute_epsilon_hf()
- Lu-Hf 表年龄列是 "U-Pb Age (Ma)"（不是 "Best Age"）
- 低内存机器（<16GB）必须先释放 U-Pb 再加载 Lu-Hf

**文件**: `provenance_analysis.py`

---

## 🔑 API 快速查找

### handler.query()
**常见用法**：
```python
handler.query(periods=["Cretaceous"])           # 按时期
handler.query(continent="Asia")                 # 按大洲
handler.query(country_state="China")            # 按国家
handler.query(age_range=(100, 200))             # 按年龄范围
handler.query(rock_class1=["detrital"])         # 按岩石类型
```

**出现位置**: `basic_query.py`, `regional_comparison.py`, `age_distribution.py`

---

### handler.clean()
**常见用法**：
```python
handler.clean(df, concordance_min=0.90)         # 基本清洗
handler.clean(df, concordance_min=0.95, concordance_max=1.05)  # 严格清洗
handler.clean(df, age_range=(0, 4500))          # 年龄范围过滤
```

**出现位置**: 所有 examples

---

### handler.ks_test()
**返回值结构**：
```python
{
    "statistic": float,     # ✅ D 统计量（注意键名）
    "p_value": float,       # p 值
    "significant": bool,    # 是否显著
    "conclusion": str       # 结论文本
}
```

**出现位置**: `regional_comparison.py`

---

### handler.plot_multi_kde()
**用法**：
```python
handler.plot_multi_kde(
    {"Label1": ages1, "Label2": ages2},  # 字典：标签 -> 年龄数组
    age_range=(0, 4000),
    save="comparison.png"
)
```

**出现位置**: `regional_comparison.py`

---

## 🔄 AI 使用流程

### 生成代码时的标准流程

```
1. 理解用户需求
   ↓
2. 查看本文件的"快速匹配表"
   ↓
3. 找到最匹配的 example
   ↓
4. 读取对应的 .py 文件
   ↓
5. 复制代码模板
   ↓
6. 根据用户需求修改参数
   ↓
7. 检查"常见错误修正"避免陷阱
```

### 原则

> **复用 > 修改 > 重写**

- ✅ 优先复用已有 example
- ✅ 修改参数适应新需求
- ❌ 避免从零开始编写

---

## 📚 相关文档

- **完整 API 文档**: `references/api_reference.md`
- **快速参考**: `references/quick_reference.md`
- **工作流示例**: `references/workflows.md`

---

## 💾 文件清单

- `basic_query.py` - 基础查询（2390 字节）
- `age_distribution.py` - 年龄分布（7627 字节）
- `regional_comparison.py` - 区域对比（9533 字节）
- `luhf_analysis.py` - Lu-Hf 分析（3055 字节）
- `concordance_qc.py` - 谐和度质量控制（~3 KB）
- `provenance_analysis.py` - 物源综合判别（~5 KB）

总大小: ~30 KB 可复用代码

---

**最后提示**: 当用户提出的问题与某个 example 匹配时，直接复用该 example 的代码模式，只需修改查询参数即可！
