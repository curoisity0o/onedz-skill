# OneDZ Skill for Claude Code

[English](#english) | **中文**

一个基于 [OneDZ 全球碎屑锆石数据库](https://github.com/KeranLi/Global-Detrital-Zircon) (.csv 格式) 二次开发的 Claude Code 技能包，由 **Zhangry** 开发。

> **数据来源**: Li, K., Hu, X., Chai, R., Yang, J. et al. (2025): OneDZ: A Global Detrital Zircon Database and Implications for Constructing Giant Geoscience Database, *Earth Syst. Sci. Data Discuss.* [preprint], https://doi.org/10.5194/essd-2025-157, in review, 2025.
>
> - 数据库 GitHub: https://github.com/KeranLi/Global-Detrital-Zircon
> - Zenodo: https://zenodo.org/records/17407937
> - OneDZ 官网: https://onedz.top

---

## 这是什么

本技能包将 OneDZ 数据库的 **.csv 格式**数据（192 万条 U-Pb 记录、27 万条 Lu-Hf 记录）封装为 Claude Code Skill，让用户可以通过自然语言指令完成锆石地质分析,使用此技能需要单独下载数据集，如果有需求可以使用其中的 `/scripts/fix_dataset.py` 脚本进行一遍数据集的错误格式修正。

**使用示例:**
```
/onedz 对比中国和印度的锆石数据
/onedz 全球各大洲锆石年龄分布对比
/onedz 分析亚洲白垩纪碎屑锆石
```

**工作流程:**
1. AI 读取技能指南 (SKILL.md)
2. 从示例模板库中匹配最合适的代码
3. 生成完整的 Python 分析脚本
4. 自动运行并返回结果（KDE 图、K-S 检验、统计表、CSV 导出）

## 交互式演示

**[打开 HTML 演示](assets/demo/onedz_skill_demo.html)** — 可视化展示 Skill 工作流程，含两个真实分析实例。

## 声明

- 本项目由 **Zhangry** 基于 OneDZ 数据库独立开发
- OneDZ 数据库的版权归 Li et al. (2025) 原作者团队所有
- 如有问题或建议，请在本仓库提交 Issue，**非** OneDZ 官方支持

## 数据集

本技能包使用 OneDZ 数据库的 **.csv 格式**数据文件，需要单独下载并放置到本地。

**当前适配版本: `onedz_csv_20260328`**

| 文件 | 记录数 | 列数 | 大小 |
|------|--------|------|------|
| zircon_upb.csv | ~192 万 | 72 | ~1.2 GB |
| zircon_luhf.csv | ~27 万 | 86 | ~164 MB |

**下载:**
- **[GitHub Release (推荐)](https://github.com/curoisity0o/onedz-skill/releases/tag/dataset-v20260328)** — 已修正格式的版本，解压即用
- OneDZ 官网: https://onedz.top/DownloadPage.html
- Zenodo (原始版本): https://zenodo.org/records/17407937

> **注意**: 当前 Skill 代码基于 `onedz_csv_20260328` 版本的列名（如 `Best Age`、`Depos.Age (Period)`、`Class-1 Rock Type`）。新版数据集（Zenodo #19690702）已重命名列（如 `Best_age`、`Depos_Age_Period`）并改为分片格式，需要适配后才能使用。可使用 `/scripts/fix_dataset.py` 对下载的数据集进行格式修正。

## 技能架构

```
onedz-skill/
├── SKILL.md              # 技能入口（AI 优先读取）
├── SKILL_ZH.md           # 中文版入口
├── scripts/              # 核心处理逻辑
│   └── onedz_handler/    # OneDZHandler API
├── assets/
│   └── examples/
│       ├── examples_index.md              # AI 快速匹配表
│       ├── regional_comparison.py         # 两区域对比模板
│       ├── grouped_comparison.py          # 多分组对比模板
│       ├── age_distribution.py            # 年龄分布分析
│       ├── basic_query.py                 # 基础查询
│       ├── luhf_analysis.py               # Lu-Hf 同位素分析
│       ├── onedz_dataset_structure.json   # 轻量数据索引 (~50KB)
│       └── ...
├── assets/demo/                        # 交互式演示
│   ├── onedz_skill_demo.html          # HTML 演示页面
│   ├── china_india_comparison.png     # 示例1 结果图
│   └── all_continents_kde.png         # 示例2 结果图
└── references/
    ├── api_reference.md    # 完整 API 文档
    ├── quick_reference.md  # 快速参考
    ├── workflows.md        # 工作流示例
    └── ...
```

## AI 工作流程

| 步骤 | 操作 | 说明 |
|------|------|------|
| 0 | 创建任务目录 | 每次分析输出隔离 |
| 1 | 匹配 examples_index.md | 找到最佳代码模板 |
| 1.5 | 检查 dataset_structure.json | 无需加载数据即可验证参数 |
| 2 | 查阅 API 文档（按需） | 模板不够用时补充 |
| 3 | 生成 & 执行脚本 | 基于模板修改参数 |
| 4 | 返回结果 | 图表、统计、导出 |

**核心原则:** 复用 > 修改 > 重写

## 核心API

```python
from scripts.onedz_handler import OneDZHandler, OneDZConfig

handler = OneDZHandler(config=OneDZConfig(output_dir="./output"))
handler.load(source="csv", table="global_u-pb")

df = handler.query(country_state="China", periods=["Cretaceous"])
df_clean = handler.clean(df, concordance_min=0.90)
result = handler.analyze(df_clean)
handler.plot_age(df_clean, mode="kde", save="kde.png")
handler.export(df_clean, "output.csv")

ks = handler.ks_test(ages_a, ages_b)
handler.plot_multi_kde({"China": ages_cn, "India": ages_in}, save="compare.png")
```

## 安装

```bash
pip install -r requirements.txt
python scripts/environment_check.py  # 验证

# 设置数据路径
export ONEDZ_DATA_PATH="/path/to/onedz_csv/"
# 或在代码中指定: OneDZConfig(csv_dir=Path("/path/to/"))
```

## 示例结果

### 中国 vs 印度对比

| 指标 | China | India |
|------|-------|-------|
| 原始记录 | 829,781 | 16,186 |
| 清洗后 | 524,049 | 11,969 |
| 中位年龄 (Ma) | 1,098 | 1,759 |
| K-S 检验 | D=0.2078, p≈0 | **显著差异** |

### 全球大洲对比

7 个大洲两两比较，**21/21 组 K-S 检验全部显著**。

| 大洲 | N (clean) | 中位年龄 (Ma) |
|------|-----------|---------------|
| Asia | 697,877 | 991 |
| N_America | 318,061 | 1,427 |
| S_America | 133,112 | 1,157 |
| Europe | 102,462 | 978 |
| Africa | 97,906 | 1,184 |
| Australia_Papua | 38,880 | 1,638 |
| Antarctica | 19,823 | 975 |

## 版本

- **v1.2.0** (2026-04-20): 重组结构，新增示例系统、分组对比模板
- **v1.1.0** (2026-04-17): Phase 5 可视化，CLI 增强
- **v1.0.0** (2026-04-16): 初始发布

## 许可

本技能包由 **Zhangry** 开发，仅供研究使用。OneDZ 数据库（.csv 格式）版权归 Li et al. (2025) 原作者团队所有，使用请遵守其许可条款。

---

<a id="english"></a>

# OneDZ Skill for Claude Code

**English** | [中文](#)

A Claude Code skill built on top of the [OneDZ global detrital zircon database](https://github.com/KeranLi/Global-Detrital-Zircon) (.csv format). Developed by **Zhangry**.

> **Data source**: Li, K., Hu, X., Chai, R., Yang, J. et al. (2025): OneDZ: A Global Detrital Zircon Database and Implications for Constructing Giant Geoscience Database, *Earth Syst. Sci. Data Discuss.* [preprint], https://doi.org/10.5194/essd-2025-157, in review, 2025.
>
> - Database GitHub: https://github.com/KeranLi/Global-Detrital-Zircon
> - Zenodo: https://zenodo.org/records/17407937
> - Website: https://onedz.top

---

## What It Does

This skill wraps the OneDZ database's **.csv format** data (1.92M U-Pb records, 270K Lu-Hf records) into a Claude Code skill for natural-language zircon analysis. The dataset must be downloaded separately. If needed, use the included `/scripts/fix_dataset.py` script to fix formatting errors in the dataset.

**Example commands:**
```
/onedz Compare China and India zircon data
/onedz Global continent zircon age distribution comparison
/onedz Analyze Cretaceous detrital zircons in Asia
```

**Workflow:**
1. AI reads the skill guidelines (SKILL.md)
2. Matches the best code template from examples
3. Generates a complete Python analysis script
4. Runs it and returns results (KDE plots, K-S tests, statistics, CSV exports)

## Interactive Demo

**[Open HTML Demo](assets/demo/onedz_skill_demo.html)** — Visual walkthrough with two real analysis examples.

## Disclaimer

- This project is developed by **Zhangry** based on the OneDZ database
- OneDZ database is copyrighted by Li et al. (2025)
- For issues or suggestions, open an Issue in this repo — **not** official OneDZ support

## Dataset

This skill uses the OneDZ database in **.csv format**, which must be downloaded separately.

**Currently adapted version: `onedz_csv_20260328`**

| File | Records | Columns | Size |
|------|---------|---------|------|
| zircon_upb.csv | ~1.92M | 72 | ~1.2 GB |
| zircon_luhf.csv | ~270K | 86 | ~164 MB |

**Download:**
- **[GitHub Release (Recommended)](https://github.com/curoisity0o/onedz-skill/releases/tag/dataset-v20260328)** — Format-corrected version, ready to use after unzip
- OneDZ Website: https://onedz.top/DownloadPage.html
- Zenodo (original version): https://zenodo.org/records/17407937

> **Note**: The current Skill code is based on column names from `onedz_csv_20260328` (e.g., `Best Age`, `Depos.Age (Period)`, `Class-1 Rock Type`). The newer Zenodo dataset (#19690702) has renamed columns and split-file format, which is not yet supported.

## Architecture

```
onedz-skill/
├── SKILL.md / SKILL_ZH.md   # Skill entry files
├── scripts/onedz_handler/    # Core API (OneDZHandler)
├── assets/examples/          # Reusable code templates
└── references/               # API documentation
```

## AI Workflow

| Step | Action | Description |
|------|--------|-------------|
| 0 | Create task directory | Isolate outputs per analysis |
| 1 | Match examples_index.md | Find best code template |
| 1.5 | Check dataset_structure.json | Validate params without loading data |
| 2 | Read API docs (if needed) | Fill gaps not covered by template |
| 3 | Generate & run script | Based on template, modified for user |
| 4 | Return results | Plots, statistics, exports |

**Core principle:** Reuse > Modify > Rewrite

## Core API

```python
from scripts.onedz_handler import OneDZHandler, OneDZConfig

handler = OneDZHandler(config=OneDZConfig(output_dir="./output"))
handler.load(source="csv", table="global_u-pb")

df = handler.query(country_state="China")
df_clean = handler.clean(df, concordance_min=0.90)
result = handler.analyze(df_clean)
handler.plot_age(df_clean, mode="kde", save="kde.png")
handler.export(df_clean, "output.csv")
```

## Installation

```bash
pip install -r requirements.txt
python scripts/environment_check.py
export ONEDZ_DATA_PATH="/path/to/onedz_csv/"
```

## Example Results

### China vs India

| Metric | China | India |
|--------|-------|-------|
| Raw records | 829,781 | 16,186 |
| Clean records | 524,049 | 11,969 |
| Median age (Ma) | 1,098 | 1,759 |
| K-S test | D=0.2078, p≈0 | **Significant** |

### Global Continent Comparison

7 continents, **21/21 pairwise K-S tests significant**.

| Continent | N (clean) | Median (Ma) |
|-----------|-----------|-------------|
| Asia | 697,877 | 991 |
| N_America | 318,061 | 1,427 |
| S_America | 133,112 | 1,157 |
| Europe | 102,462 | 978 |
| Africa | 97,906 | 1,184 |
| Australia_Papua | 38,880 | 1,638 |
| Antarctica | 19,823 | 975 |

## Version

- **v1.2.0** (2026-04-20): Restructured, examples system, grouped_comparison template
- **v1.1.0** (2026-04-17): Phase 5 visualizations, CLI
- **v1.0.0** (2026-04-16): Initial release

## License

Developed by **Zhangry** for research use. The OneDZ database (.csv format) is copyrighted by Li et al. (2025) — please follow their license terms.
