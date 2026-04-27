---
name: onedz
description:
  "Analyzes global detrital zircon U-Pb and Lu-Hf isotope data from the OneDZ database.
  Use whenever the user asks about zircon geochronology, detrital zircon analysis, U-Pb dating,
  Lu-Hf isotopes, age distribution plots (KDE/PDP), concordance diagrams, εHf(t) evolution,
  or geological statistical analysis of zircon ages. Also triggers for queries about zircon data
  filtering, probability density plots, peak detection in age distributions, or exporting
  geochemical data to GeoJSON/Shapefile formats."
version: 1.3.0
languages: [zh, en]
---

<!-- ================================================================= -->
<!--                         中文版 (ZH)                                -->
<!-- ================================================================= -->

# OneDZ — 全球碎屑锆石数据库分析

分析全球最大的碎屑锆石数据库（Li et al., 2025），包含 192 万条 U-Pb 记录和 27 万条 Lu-Hf 记录。提供从数据加载、科学级数据清洗、统计分析、出版级可视化到多格式导出的完整工作流程。

## 🤖 AI 使用指南（必读）

> ⚠️ **重要**: 生成代码前，必须按照以下步骤操作
>
> **目标**: 提高代码生成准确性，减少 API 调用错误，避免常见陷阱

---

### 📁 步骤 0: 创建任务工作目录（每次任务必须首先执行）

**每次收到用户分析任务时，必须首先在当前工作目录下创建独立的任务文件夹，将脚本和所有输出都保存在其中，避免不同任务的文件混在一起。**

#### 0.1 创建目录

```python
from datetime import datetime
from pathlib import Path

# 根据用户需求生成任务名（英文，小写，下划线分隔）
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
TASK_NAME = "australia_analysis"  # ← 根据实际任务修改
TASK_DIR = Path.cwd() / f"{TASK_NAME}_{timestamp}"
TASK_DIR.mkdir(parents=True, exist_ok=True)
print(f"任务目录: {TASK_DIR}")
```

**命名规范**:

| 用户需求 | 任务名 |
|---------|--------|
| 中国锆石数据对比分析 | `china_period_comparison` |
| 澳大利亚锆石数据分析 | `australia_analysis` |
| 对比中国和澳大利亚 | `china_vs_australia` |
| 亚洲白垩纪碎屑锆石分析 | `asia_cretaceous` |

#### 0.2 脚本保存到任务目录

```python
script_path = TASK_DIR / "analysis.py"
```

#### 0.3 配置 OneDZHandler 输出到任务目录

```python
config = OneDZConfig(output_dir=TASK_DIR, use_timestamp_output=False)
handler = OneDZHandler(config=config)
```

#### 0.4 ⚠️ viz 方法输出路径注意事项

`handler.viz.plot_*` 系列方法**不会自动使用** `config.output_dir`，必须传**绝对路径**：

```python
def out(filename):
    return str(TASK_DIR / filename)

# ✅ 自动走 output_dir（只传文件名）
handler.plot_age(df_clean, mode="kde", save="kde.png")
handler.plot_multi_kde({"A": ages_a}, save="comparison.png")
handler.plot_epsilon_hf(df, save="hf.png")
handler.export(df_clean, "data.csv")

# ⚠️ viz 方法需要手动传绝对路径
handler.viz.plot_geographic_distribution(df, geo_level="country", save=out("geo.png"))
handler.viz.plot_rock_type_statistics(df, class_level="Class2", save=out("rock.png"))
handler.viz.plot_temporal_distribution(df, save=out("temporal.png"))
```

#### 0.5 最终目录结构

```
当前工作目录/
└── australia_analysis_20260421_171500/
    ├── analysis.py                 ← 分析脚本
    ├── australia_kde.png           ← 图表输出
    ├── australia_data.csv          ← 数据导出
    └── ...
```

---

### 📋 步骤 1: 查找相关 Example（第一优先级）

**用户提出需求时**，首先执行以下步骤：

#### 1.1 打开 Example 索引
```bash
# 查看快速匹配表
assets/examples/examples_index.md
```

#### 1.2 查找匹配的 Example

在 examples_index.md 的"🎯 快速匹配表"中查找与用户需求最匹配的行。

**示例映射**：
```
用户需求 → 匹配的 Example
─────────────────────────────────
"对比中国和澳大利亚" → regional_comparison
"K-S 统计检验" → regional_comparison
"年龄分布分析" → age_distribution
"峰值检测" → age_distribution
"基础查询" → basic_query
"第一次使用" → basic_query
"Lu-Hf 同位素" → luhf_analysis
"εHf(t)" → luhf_analysis
```

#### 1.3 读取 Example 代码

```python
# 读取匹配的 .py 文件
# 例如：regional_comparison.py
```

#### 1.4 复制修改

**原则**: 复制 Example 代码 → 修改参数 → 适应新需求

**不要从零开始编写！**

---

### 🔍 步骤 1.5: 查询可用数据范围（不确定参数时使用）

当不确定查询参数（国家名、时期名、岩石类型等）是否存在于数据集中时，读取 `assets/examples/onedz_dataset_structure.json`，**无需加载 1.5GB 数据**即可确认。

| 想知道的 | 看 `quick_index` 的哪个字段 | 示例 |
|---------|---------------------------|------|
| 有哪些国家/地区 | `Country_State` (206个) | China, Australia, America... |
| 有哪些大洲 | `Continent` (17个) | Asia, Europe, N_America... |
| 有哪些地质时期 | `Depos.Age (Period)` (96个) | Cretaceous, Jurassic... |
| 有哪些岩石类型 | `Class-1/2/3 Rock Type` | detrital, igneous... |
| 有哪些仪器 | `Mass Spectrometer` (25个) | LA-ICP-MS, SHRIMP... |
| 列的空值率 | `files.*.columns.*.null_count` | Best Age: 71.6% non-null |

**典型用法**：

```python
# 用户问"印度锆石数据"——先确认"印度"在数据集中的确切名称
import json
with open("assets/examples/onedz_dataset_structure.json") as f:
    ds = json.load(f)
countries = ds["quick_index"]["Country_State"]["categories"]
# 找到: "India" 存在 ✅

# 用户问"南极洲"——检查数据量
continent = ds["quick_index"]["Continent"]["categories"]
# 找到: "Antarctica", "Antarctica shelves" — 数据量可能有限
```

---

### 📚 步骤 2: 查阅 API 文档（需要新 API 时）

**如果 Example 中的 API 不够用**，按以下优先级查阅：

#### 2.1 快速参考（第一选择）
```bash
references/quick_reference.md
```
- ✅ 常用 API 参数
- ✅ 代码模板
- ✅ 错误对照表

#### 2.2 完整 API 文档（详细查询）
```bash
references/api_reference.md
```
- ✅ 所有 API 详细说明
- ✅ 参数类型
- ✅ 返回值格式

#### 2.3 工作流示例
```bash
references/workflows.md
```
- ✅ 完整工作流
- ✅ 分步说明

---

### ✅ 步骤 3: 必须遵循的规则

#### 3.1 使用 OneDZHandler API

```python
# ✅ 正确 - 使用高级 API
df = handler.query(country_state="China")

# ❌ 错误 - 绕过 API 直接操作
df = handler.data.filter(pl.col("Country_State") == "China")
```

**原因**：
- API 提供数据验证和错误处理
- API 保证代码稳定性
- API 隐藏内部实现细节

#### 3.2 添加数据验证

```python
# ✅ 正确 - 检查查询结果
df = handler.query(country_state="China")
if df.height == 0:
    print("⚠️ 未找到数据")
    return

# ❌ 错误 - 假设总有数据
df = handler.query(country_state="China")
# 直接处理，可能报错
```

#### 3.3 使用正确的列名和返回值

```python
# ✅ 正确的列名
ages = df["Best Age"].drop_nulls().to_numpy()

# ❌ 错误的列名
ages = df["BestAge"].drop_nulls().to_numpy()

# ✅ 正确的返回值访问
ks_stat = ks_result['statistic']  # D 统计量

# ❌ 错误的返回值访问
ks_stat = ks_result['d_statistic']  # 这个键不存在
```

#### 3.4 使用英文标签

```python
# ✅ 正确 - 英文标签
handler.plot_multi_kde({"China": ages, "Australia": ages_au})

# ⚠️ 可能有问题 - 中文标签
handler.plot_multi_kde({"中国": ages, "澳大利亚": ages_au})
# 可能显示为方块，除非有中文字体
```

#### 3.5 内存优化（自动选择加载方式）

**默认使用惰性查询，不调 load()，避免 OOM：**

```python
# ✅ 内存友好（~0.5 GB）— 推荐
df_china = handler.query_from_csv(country_state="China")
df_china_clean = handler.clean(df_china)

# ❌ 内存浪费（~4 GB），容易 OOM
handler.load(source="csv", table="global_u-pb")
df_china = handler.query(country_state="China")
```

**Lu-Hf join 使用惰性版本：**

```python
# ✅ 内存友好（~1 GB）— 推荐
df_joined = handler.join_from_csv()

# 带预过滤（只要某个区域的 Lu-Hf 数据）
df_china_hf = handler.join_from_csv(upb_filters={"country_state": "China"})
```

**何时使用原有 load() + query()：**
- 内存充足（>16 GB）
- 需要多次不同的查询（>3 次）
- 需要 info()、get_samples() 等依赖全表缓存的方法

#### 3.6 结果必须来自实际运行（禁止编造结论）

```python
# ✅ 正确 — 脚本实际运行，结论来自代码输出
#   先写脚本 → 运行脚本 → 从运行输出中提取结论

# ❌ 错误 — 未运行脚本就编造分析结论
#   "中国锆石中位年龄约 928 Ma" ← 如果没运行代码，这个数字是编的
```

**规则**：
- 所有分析结论**必须来自脚本的实际运行输出**
- 如果脚本运行失败或结果异常，**如实报告错误**，不要编造正常结果
- 如果结果与预期不符（如数据为空、统计值不合理），如实说明情况，不要美化

---

### ❌ 步骤 4: 禁止做的事

| 禁止操作 | 原因 | 替代方案 |
|---------|------|---------|
| ❌ 绕过 OneDZHandler 直接用 polars | API 提供验证和优化 | 使用 `handler.query()` |
| ❌ 假设查询结果非空 | 可能返回空数据 | 检查 `df.height > 0` |
| ❌ 使用中文标签 | 字体可能缺失 | 使用英文标签 |
| ❌ 忽略类型转换 | 列可能是字符串 | 显式转换或使用 `.cast()` |
| ❌ 凭记忆写 API | 参数可能记错 | 查文档或 Example |

---

### 🔧 步骤 5: 错误处理模板

#### 5.1 安全查询模板

```python
def safe_query(handler, **kwargs):
    """安全查询，检查结果"""
    df = handler.query(**kwargs)
    if df.height == 0:
        print(f"⚠️ 查询无结果: {kwargs}")
        return None
    return df

# 使用
df_china = safe_query(handler, country_state="China")
if df_china is None:
    return
```

#### 5.2 类型转换模板

```python
# 提取年龄时处理类型
ages = df["Best Age"].cast(pl.Float64).drop_nulls().to_numpy()
```

#### 5.3 标准分析流程

```python
# 1. 初始化
handler = OneDZHandler()
handler.load(source="csv", table="global_u-pb")

# 2. 查询（带检查）
df = handler.query(country_state="China")
if df.height == 0:
    print("未找到数据")
    return

# 3. 清洗
df_clean = handler.clean(df, concordance_min=0.90)

# 4. 分析
result = handler.analyze(df_clean)

# 5. 可视化
handler.plot_age(df_clean, mode="kde", save="output.png")
```

---

### 🚨 步骤 6: 常见问题速查

| 问题 | 解决方案 | 参考 |
|------|---------|------|
| 找不到相关 Example | 查 `examples_index.md` 的"快速匹配表" | Step 1.1 |
| 不确定 API 参数 | 查 `references/quick_reference.md` | Step 2.1 |
| 需要完整 API 文档 | 查 `references/api_reference.md` | Step 2.2 |
| AttributeError | 查 `quick_reference.md` 的"错误对照表" | Step 2.1 |
| 内存不足 | 使用 `max_records` 参数 | API 文档 |
| 中文显示异常 | 使用英文标签 | Step 3.4 |

---

### 📖 文档查找优先级

```
遇到问题时按此顺序查找：

1. examples_index.md (快速匹配)
   ↓ 找不到匹配的 Example
2. examples/*.py (参考代码)
   ↓ 需要新的 API
3. references/quick_reference.md (API 速查)
   ↓ 需要详细说明
4. references/api_reference.md (完整文档)
```

**原则**:
- 先找现成代码 → 再查文档 → 最后根据通用规则编写
- 复用优于重写

---

### 🎯 Example 使用示例

#### 场景 1: 用户要求"对比中国和澳大利亚"

```
AI 思考流程：
1. 查 examples_index.md → 找到 "regional_comparison"
2. 读取 regional_comparison.py
3. 发现代码完全匹配需求
4. 直接复用，可能只需修改输出文件名
5. 完成！✅
```

#### 场景 2: 用户要求"分析亚洲白垩纪锆石"

```
AI 思考流程：
1. 查 examples_index.md → 找到 "age_distribution"
2. 读取 age_distribution.py
3. 代码分析"亚洲白垩纪"
4. 修改参数：
   - continent="Asia"
   - periods=["Cretaceous"]
5. 完成！✅
```

#### 场景 3: 用户要求"分析欧洲侏罗纪火成岩"

```
AI 思考流程：
1. 查 examples_index.md → 找到 "age_distribution"
2. 读取 age_distribution.py
3. 修改参数：
   - continent="Europe"
   - periods=["Jurassic"]
   - rock_class1=["igneous"]
4. 完成！✅
```

---

### 📊 预期效果

#### Before（无指南）

```
用户: "对比中国和澳大利亚"
↓
AI: 凭记忆生成代码
↓
错误: countries vs country_state
↓
错误: d_statistic vs statistic
↓
结果: 多次迭代，16 分钟
```

#### After（遵循指南）

```
用户: "对比中国和澳大利亚"
↓
AI: 查 examples_index.md → regional_comparison
↓
读取代码 → 复制模板
↓
结果: 一次成功，5 分钟 ✅
```

---

### ✅ 检查清单

生成代码前，确认已完成：

- [ ] 创建任务工作目录（步骤 0）
- [ ] 配置 `OneDZConfig(output_dir=TASK_DIR, use_timestamp_output=False)`
- [ ] viz 方法使用 `out()` 辅助函数传绝对路径
- [ ] 查阅 `examples_index.md` 找到匹配的 Example
- [ ] 不确定参数时查 `onedz_dataset_structure.json`（步骤 1.5）
- [ ] 读取对应的 .py 文件
- [ ] 确认使用 `OneDZHandler` API（不直接操作 polars）
- [ ] 添加数据验证（检查 `df.height > 0`）
- [ ] 使用正确的列名（如 `"Best Age"`）
- [ ] 使用正确的返回值（如 `ks_result['statistic']`）
- [ ] 使用英文标签避免字体问题
- [ ] 结果来自实际运行输出，未运行不编造结论（步骤 3.6）

---

**记住**: 复用现有 Example 代码的成功率远高于从零编写！

---

## 快速开始

### 数据集配置

**OneDZ 需要 CSV 格式数据集** (zircon_upb.csv, zircon_luhf.csv)。

**下载数据**:
- 官方网站: https://onedz.top/DownloadPage.html
- Zenodo: https://zenodo.org/records/17407937

**配置数据路径**:
```bash
# 方法 1: 环境变量（推荐）
export ONEDZ_DATA_PATH="/your/path/to/onedz_csv_20260328/"

# 方法 2: 用户配置文件（永久生效）
mkdir -p ~/.onedz
echo '{"csv_dir": "/your/path/to/onedz_csv_20260328/modified"}' > ~/.onedz/config.json

# 方法 3: 在代码中指定
handler = OneDZHandler(config=OneDZConfig(csv_dir=Path("/your/path/")))
```

初始化 `OneDZHandler()` 时会检查数据集，如未找到会显示友好的提示信息。

### 基本用法

```python
from scripts.onedz_handler import OneDZHandler

# 初始化
handler = OneDZHandler()

# 加载和查询
handler.load()
df = handler.query(periods=["Cretaceous"], continent="Asia")

# 清洗和可视化
df_clean = handler.clean(df)
handler.plot_age(df_clean, mode="kde", save="kde.png")

# 导出
handler.export(df_clean, "output.csv")
```

## 核心工作流程

1. **初始化 Handler** - 创建 `OneDZHandler()` 实例
2. **加载数据** - 使用 `handler.load()` 加载 U-Pb 或 Lu-Hf 表
3. **查询数据** - 按时期、岩石类型、位置、年龄范围等过滤
4. **清洗数据** - 应用质量控制（谐和度、误差标准化）
5. **分析** - 统计分析、峰值检测、K-S 检验
6. **可视化** - 生成 KDE 图、εHf 图、统计图表
7. **导出** - 保存为 CSV、Excel、GeoJSON 或 Shapefile

## 可用脚本

### 环境检查
验证安装：
```bash
python scripts/environment_check.py
```

### 数据探索
探索数据集：
```bash
python scripts/data_explorer.py
```

### CLI 工具
命令行接口用于批量处理：
```bash
onedz query --period Cretaceous --continent Asia -o data.csv
onedz clean --input data.csv -o clean.csv
onedz plot --input clean.csv --plot-type kde -o kde.png
```

## 示例工作流

### 示例 1: 年龄分布分析

```python
from scripts.onedz_handler import OneDZHandler

handler = OneDZHandler()
handler.load()
df = handler.query(periods=["Cretaceous"], continent="Asia")
df_clean = handler.clean(df, concordance_min=0.90)
handler.plot_age(df_clean, mode="kde", save="cretaceous_kde.png")
handler.export(df_clean, "cretaceous_data.csv")
```

### 示例 2: Lu-Hf 同位素演化

```python
handler.load(source="csv", table="global_u-pb")
handler.load(source="csv", table="global_lu-hf")
df_joined = handler.join_upb_luhf()
df_computed = handler.compute_epsilon_hf(df_joined)
handler.plot_epsilon_hf(df_computed, save="epsilon_hf.png")
```

### 示例 3: 区域对比

```python
df_asia = handler.query(periods=["Cretaceous"], continent="Asia")
df_europe = handler.query(periods=["Cretaceous"], continent="Europe")

ages_asia = handler.clean(df_asia)["Best Age"].drop_nulls().to_numpy()
ages_europe = handler.clean(df_europe)["Best Age"].drop_nulls().to_numpy()

ks_result = handler.ks_test(ages_asia, ages_europe)
print(f"K-S p值: {ks_result['p_value']:.3e}")

handler.plot_multi_kde(
    {"Asia": ages_asia, "Europe": ages_europe},
    save="comparison.png"
)
```

### 示例 4: 统计可视化

```python
handler.load()

# 岩石类型统计
handler.viz.plot_rock_type_statistics(
    handler.data,
    class_level="Class1",
    plot_type="bar",
    save="rock_stats.png"
)

# 地理分布
handler.viz.plot_geographic_distribution(
    handler.data,
    geo_level="continent",
    save="geo_dist.png"
)

# 时间分布
handler.viz.plot_temporal_distribution(
    handler.data,
    save="temporal_dist.png"
)
```

## 何时使用此 Skill

当用户提到以下内容时触发此 Skill：
- **锆石分析**: 碎屑锆石、U-Pb 定年、Lu-Hf 同位素
- **年龄分布**: KDE 图、概率密度图、峰值检测
- **数据过滤**: 谐和度、不一致性、地质时期
- **同位素地球化学**: εHf(t) 演化、Hf 模式年龄
- **区域分析**: 地理过滤、大洲级研究
- **导出格式**: GeoJSON、Shapefile、Excel 导出
- **统计图形**: 岩石类型统计、分布图

## 文档

### 参考文档
- **[环境设置](references/environment.md)** - 依赖和安装
- **[数据集指南](references/dataset.md)** - 数据结构和位置
- **[API 参考](references/api_reference.md)** - 完整方法文档
- **[工作流](references/workflows.md)** - 分步示例
- **[CLI 指南](references/cli_guide.md)** - 命令行工具文档

### 示例
查看 `assets/examples/` 获取现成的脚本：
- **[basic_query.py](assets/examples/basic_query.py)** - 简单数据查询
- **[age_distribution.py](assets/examples/age_distribution.py)** - 年龄分布分析
- **[luhf_analysis.py](assets/examples/luhf_analysis.py)** - Lu-Hf 同位素分析
- **[regional_comparison.py](assets/examples/regional_comparison.py)** - 区域对比

## 数据引用

使用此 Skill 的结果时，请引用：

**Li, K., Hu, X., Chai, R., Yang, J. et al. (2025)**. OneDZ: A Global Detrital Zircon Database and Implications for Constructing Giant Geoscience Database. *Earth System Science Data*.

- GitHub: https://github.com/KeranLi/Global-Detrital-Zircon
- Zenodo: https://zenodo.org/records/17407937

## 性能说明

- **U-Pb 表**: 约 192 万条记录，加载时间约 30 秒
- **Lu-Hf 表**: 约 27 万条记录，加载时间约 5 秒
- **查询**: 索引列上亚秒级
- **KDE 计算**: 10 万年龄 <1 秒
- **导出**: CSV 最快，Shapefile 最慢

对于大数据集（>50 万条记录），在查询中使用 `max_records` 参数。

## 版本历史

- **v1.2.0** (2026-04-20): 重构为标准格式，添加 references/ 和 assets/
- **v1.1.0** (2026-04-17): 新增 Phase 5 统计可视化、CLI 增强
- **v1.0.0** (2026-04-16): 初始版本，包含核心功能

<!-- ================================================================= -->
<!--                          English (EN)                              -->
<!-- ================================================================= -->

# OneDZ — Global Detrital Zircon Database Analysis

Analyzes the world's largest detrital zircon database (Li et al., 2025) with 1.92M U-Pb records and 270K Lu-Hf records. Provides complete workflow from data loading through scientific-grade cleaning, statistical analysis, publication-quality visualizations, and multi-format export.

## AI Usage Guide (Required Reading)

> ⚠️ **Important**: Before generating any code, follow the steps below.
> The goal is to improve code generation accuracy and avoid common pitfalls.

### Step 0: Create Task Working Directory

**For every analysis task, create an isolated task directory to keep outputs separate.**

```python
from datetime import datetime
from pathlib import Path

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
TASK_NAME = "australia_analysis"  # ← change per task
TASK_DIR = Path.cwd() / f"{TASK_NAME}_{timestamp}"
TASK_DIR.mkdir(parents=True, exist_ok=True)
config = OneDZConfig(output_dir=TASK_DIR, use_timestamp_output=False)
handler = OneDZHandler(config=config)
```

### Step 1: Match Example Code (Highest Priority)

```bash
# Open the example index
assets/examples/examples_index.md
```

Copy an existing template, modify parameters to fit the user request. **Do not write from scratch.**

### Step 1.5: Check Dataset Structure

When unsure about parameter names (country, period, rock type), read `assets/examples/onedz_dataset_structure.json` instead of loading the 1.5GB CSV.

### Step 2: Read API Docs (Only When Needed)

Priority: `references/quick_reference.md` > `references/api_reference.md` > `references/workflows.md`

### Step 3: Mandatory Rules

1. Use `OneDZHandler` API, never access internals directly
2. Always validate query results (`df.height > 0`)
3. Use correct column names (e.g., `"Best Age"`, `"Country_State"`)
4. Use English labels for plot legends (avoids font issues)
5. Default to lazy queries (`query_from_csv`) to avoid OOM
6. **All conclusions must come from actual script output** — never fabricate results

### Step 4: Prohibited Actions

- ❌ Bypassing OneDZHandler to use polars directly
- ❌ Assuming query results are always non-empty
- ❌ Using Chinese labels in plots
- ❌ Writing APIs from memory instead of checking docs

### Step 5: Error Handling Patterns

```python
def safe_query(handler, **kwargs):
    df = handler.query(**kwargs)
    if df.height == 0:
        print(f"⚠️ No results: {kwargs}")
        return None
    return df
```

## Quick Start

### Dataset Setup

**Download**: https://onedz.top/DownloadPage.html or Zenodo: https://zenodo.org/records/17407937

**Configure data path**:
```bash
# Method 1: Environment variable
export ONEDZ_DATA_PATH="/your/path/to/onedz_csv_20260328/"

# Method 2: User config file (persistent)
mkdir -p ~/.onedz
echo '{"csv_dir": "/your/path/to/onedz_csv_20260328/modified"}' > ~/.onedz/config.json
```

### Basic Usage

```python
from scripts.onedz_handler import OneDZHandler

handler = OneDZHandler()
handler.load()
df = handler.query(periods=["Cretaceous"], continent="Asia")
df_clean = handler.clean(df)
handler.plot_age(df_clean, mode="kde", save="kde.png")
handler.export(df_clean, "output.csv")
```

## Core Workflow

1. **Initialize Handler** - Create `OneDZHandler()` instance
2. **Load Data** - Use `handler.load()` to load U-Pb or Lu-Hf tables
3. **Query Data** - Filter by period, rock type, location, age range, etc.
4. **Clean Data** - Apply quality control (concordance, error standardization)
5. **Analyze** - Statistical analysis, peak detection, K-S tests
6. **Visualize** - Generate KDE plots, εHf diagrams, statistical charts
7. **Export** - Save to CSV, Excel, GeoJSON, or Shapefile

## Example Workflows

### Example 1: Age Distribution

```python
handler = OneDZHandler()
handler.load()
df = handler.query(periods=["Cretaceous"], continent="Asia")
df_clean = handler.clean(df, concordance_min=0.90)
handler.plot_age(df_clean, mode="kde", save="cretaceous_kde.png")
handler.export(df_clean, "cretaceous_data.csv")
```

### Example 2: Lu-Hf Isotope Evolution

```python
handler.load(source="csv", table="global_u-pb")
handler.load(source="csv", table="global_lu-hf")
df_joined = handler.join_upb_luhf()
df_computed = handler.compute_epsilon_hf(df_joined)
handler.plot_epsilon_hf(df_computed, save="epsilon_hf.png")
```

### Example 3: Regional Comparison

```python
df_asia = handler.query(periods=["Cretaceous"], continent="Asia")
df_europe = handler.query(periods=["Cretaceous"], continent="Europe")
ages_asia = handler.clean(df_asia)["Best Age"].drop_nulls().to_numpy()
ages_europe = handler.clean(df_europe)["Best Age"].drop_nulls().to_numpy()
ks_result = handler.ks_test(ages_asia, ages_europe)
handler.plot_multi_kde({"Asia": ages_asia, "Europe": ages_europe}, save="comparison.png")
```

### Example 4: Statistical Visualizations

```python
handler.load()
handler.viz.plot_rock_type_statistics(handler.data, class_level="Class1", save="rock_stats.png")
handler.viz.plot_geographic_distribution(handler.data, geo_level="continent", save="geo_dist.png")
handler.viz.plot_temporal_distribution(handler.data, save="temporal_dist.png")
```

## When to Use This Skill

- **Zircon analysis**: detrital zircon, U-Pb dating, Lu-Hf isotopes
- **Age distributions**: KDE plots, probability density, peak detection
- **Data filtering**: concordance, discordance, geological periods
- **Isotope geochemistry**: εHf(t) evolution, Hf model ages
- **Regional analysis**: geographic filtering, continental studies
- **Export formats**: GeoJSON, Shapefile, Excel export

## Available Scripts

```bash
# Environment check
python scripts/environment_check.py

# CLI tool
onedz query --period Cretaceous --continent Asia -o data.csv
onedz clean --input data.csv -o clean.csv
onedz plot --input clean.csv --plot-type kde -o kde.png
```

## Documentation

- **[Environment Setup](references/environment.md)** - Dependencies and installation
- **[Dataset Guide](references/dataset.md)** - Data structure and locations
- **[API Reference](references/api_reference.md)** - Complete method documentation
- **[Workflows](references/workflows.md)** - Step-by-step examples
- **[CLI Guide](references/cli_guide.md)** - Command-line tool documentation

## Data Citation

**Li, K., Hu, X., Chai, R., Yang, J. et al. (2025)**. OneDZ: A Global Detrital Zircon Database... *Earth System Science Data*.

- GitHub: https://github.com/KeranLi/Global-Detrital-Zircon
- Zenodo: https://zenodo.org/records/17407937

## Performance Notes

- **U-Pb table**: ~1.92M records, loads in ~30 seconds
- **Lu-Hf table**: ~270K records, loads in ~5 seconds
- **KDE computation**: <1 second for 100K ages
- Use `max_records` parameter for datasets >500K records

## Version History

- **v1.2.0** (2026-04-20): Restructured to standard format, added references/ and assets/
- **v1.1.0** (2026-04-17): Added Phase 5 statistical visualizations, CLI enhancements
- **v1.0.0** (2026-04-16): Initial release with core functionality
