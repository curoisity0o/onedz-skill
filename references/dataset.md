# OneDZ 数据集说明

> **最后更新**: 2026-04-20
> **数据版本**: 2026-03-28 (onedz_csv_20260328)
> **适用于**: OneDZ Handler v1.1.0+

---

## 数据集概述

OneDZ (One Detrital Zircon database) 是全球最大的碎屑锆石 U-Pb 和 Lu-Hf 同位素数据库。

**数据来源**: Li, K., Hu, X., Chai, R., Yang, J. et al. (2025). OneDZ: A Global Detrital Zircon Database and Implications for Constructing Giant Geoscience Database. *Earth System Science Data*.

**数据规模**:
- **U-Pb 记录**: 192 万条 (72 列)
- **Lu-Hf 记录**: 27 万条 (86 列)
- **覆盖范围**: 全球所有大洲
- **时间跨度**: 太古宙至今 (0-4500 Ma)

---

## 默认数据位置

### 预期路径

OneDZ Handler 默认期望数据位于：
```
/home/zry/my-OneDZ-skill/onedz_csv_20260328/
├── zircon_upb.csv     # U-Pb 年龄数据 (1.92M × 72列)
└── zircon_luhf.csv    # Lu-Hf 同位素数据 (270K × 86列)
```

### 文件说明

#### zircon_upb.csv
- **记录数**: 1,920,000+
- **列数**: 72
- **大小**: ~500 MB (压缩后)
- **内容**: 锆石 U-Pb 年龄数据、样品信息、地理位置、仪器参数等

**关键列**:
- `Best Age`: 最佳年龄（自动选择）
- `206Pb/238U Age`: ²⁰⁶Pb/²³⁸U 年龄
- `207Pb/206Pb Age`: ²⁰⁷Pb/²⁰⁶Pb 年龄
- `Period`: 地质年代（如 Cretaceous）
- `Rock_Class1/2/3`: 岩石分类（三级）
- `Continent`, `Country`: 地理信息
- `Latitude`, `Longitude`: 坐标（WGS84）
- `Instrument`: 仪器类型

#### zircon_luhf.csv
- **记录数**: 270,000+
- **列数**: 86
- **大小**: ~100 MB (压缩后)
- **内容**: 锆石 Lu-Hf 同位素数据、εHf(t)、TDM 模式年龄等

**关键列**:
- `Ref_Sample_Key`: 关联键（用于连接 U-Pb 表）
- `176Lu/177Hf`: ¹⁷⁶Lu/¹⁷⁷Hf 比值
- `176Hf/177Hf`: ¹⁷⁶Hf/¹⁷⁷Hf 比值
- `epsilon_Hf`: εHf(t) 值
- `TDM1`, `TDM2`: Hf 模式年龄

---

## 自定义数据路径

如果你的数据在其他位置，有以下方法指定路径：

### 方法 1: 环境变量（推荐）

**设置环境变量**:
```bash
# 在 ~/.bashrc 或 ~/.zshrc 中添加
export ONEDZ_DATA_PATH="/path/to/onedz_csv_20260328/"

# 重新加载配置
source ~/.bashrc
```

**使用**:
```python
from scripts.onedz_handler import OneDZHandler
handler = OneDZHandler()  # 自动读取环境变量
```

### 方法 2: 初始化时指定

```python
from scripts.onedz_handler import OneDZHandler, OneDZConfig
from pathlib import Path

# 创建自定义配置
config = OneDZConfig()
config.csv_dir = Path("/your/path/to/onedz_csv_20260328")

# 使用自定义配置初始化
handler = OneDZHandler(config=config)
```

### 方法 3: 加载时指定

```python
from scripts.onedz_handler import OneDZHandler
from pathlib import Path

handler = OneDZHandler()
handler.load(
    source="csv",
    table="global_u-pb",
    csv_dir=Path("/your/path/to/onedz_csv_20260328")
)
```

### 数据集提示

**当数据集不存在时**，OneDZHandler 会显示友好的提示信息：

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                    OneDZ 数据集未找到或路径不正确                          ║
╚═══════════════════════════════════════════════════════════════════════════╝

📥 获取数据集
  官方网站: https://onedz.top/DownloadPage.html
  Zenodo: https://zenodo.org/records/17407937

📂 指定数据集路径
  export ONEDZ_DATA_PATH="/your/path/to/onedz_csv_20260328/"
```

### 方法 4: 交互式输入（已移除）

新版本不再支持交互式输入，请使用上述方法之一。

---

## 数据结构详解

### U-Pb 数据表结构

#### 年龄数据
| 列名 | 说明 | 单位 |
|------|------|------|
| `206Pb/238U Age` | ²⁰⁶Pb/²³⁸U 年龄 | Ma |
| `207Pb/206Pb Age` | ²⁰⁷Pb/²⁰⁶Pb 年龄 | Ma |
| `207Pb/235U Age` | ²⁰⁷Pb/²³⁵U 年龄 | Ma |
| `Best Age` | 最佳年龄（自动选择） | Ma |
| `1σ` | 年龄误差（1σ） | Ma |

#### 岩石分类
| 列名 | 说明 | 示例 |
|------|------|------|
| `Rock_Class1` | 一级分类 | detrital, igneous |
| `Rock_Class2` | 二级分类 | sandstone, granite |
| `Rock_Class3` | 三级分类 | 具体岩性 |

#### 地理信息
| 列名 | 说明 | 格式 |
|------|------|------|
| `Continent` | 大洲 | Asia, Europe... |
| `Major_Region` | 主要区域 | East Asia |
| `Minor_Region` | 次要区域 | South China |
| `Country_State` | 国家/地区 | China |
| `Formation` | 地层组/组 | Yixian Formation |
| `Latitude` | 纬度 | -90 ~ +90 |
| `Longitude` | 经度 | -180 ~ +180 |

#### 质量控制
| 列名 | 说明 | 取值范围 |
|------|------|----------|
| `Concordance` | 谐和度 | 0.90-1.10 为优 |
| `Discordance` | 不一致度 | <10% 为优 |
| `Grade` | 数据质量等级 | A, B, C |

### Lu-Hf 数据表结构

#### 同位素比值
| 列名 | 说明 |
|------|------|
| `176Lu/177Hf` | ¹⁷⁶Lu/¹⁷⁷Hf 比值 |
| `176Hf/177Hf` | ¹⁷⁶Hf/¹⁷⁷Hf 比值 |
| `2σ` | 测量误差 |

#### 演化参数
| 列名 | 说明 | 单位 |
|------|------|------|
| `epsilon_Hf` | εHf(t) 值 | 无量纲 |
| `TDM1` | 二阶段模式年龄 | Ma |
| `TDM2` | 二阶段模式年龄 | Ma |

---

## 数据预处理

### Handler 自动处理

OneDZ Handler 会自动执行以下预处理：

1. **缺失坐标修复**: 使用 Formation 级别的中值填充
2. **最佳年龄计算**: 根据年龄范围自动选择
   - <1000 Ma: ²⁰⁶Pb/²³⁸U
   - ≥1000 Ma: ²⁰⁷Pb/²⁰⁶Pb
3. **误差标准化**: 统一转换为 1σ 或 2σ
4. **谐和度过滤**: 可选的质量控制

### 手动预处理

如果需要自定义预处理：

```python
from scripts.onedz_handler import OneDZHandler

handler = OneDZHandler()

# 加载原始数据
handler.load(source="csv", table="global_u-pb")

# 自定义清洗
df_clean = handler.clean(
    handler.data,
    compute_best_age=True,        # 计算最佳年龄
    filter_concordance=True,      # 过滤谐和度
    concordance_min=0.90,         # 最小谐和度
    concordance_max=1.10,         # 最大谐和度
    standardize_errors=True,      # 标准化误差
    target_sigma=1,               # 目标误差（1σ）
    remove_null_ages=True,        # 移除缺失年龄
    age_range=(0, 4000)           # 年龄范围过滤
)
```

---

## 数据下载

### 官方来源

**Zenodo** (推荐):
- DOI: 10.5281/zenodo.17407937
- URL: https://zenodo.org/records/17407937
- 包含完整数据和元数据

**GitHub**:
- URL: https://github.com/KeranLi/Global-Detrital-Zircon
- 数据文件在 `data/` 目录

### 下载后验证

```bash
# 检查文件是否存在
ls -lh zircon_upb.csv zircon_luhf.csv

# 检查行数（不包括标题）
wc -l zircon_upb.csv zircon_luhf.csv

# 预期输出:
# 1920000+ zircon_upb.csv
# 270000+ zircon_luhf.csv
```

---

## 数据格式

### CSV 格式规范

- **编码**: UTF-8
- **分隔符**: 逗号 (`,`)
- **小数点**: 点 (`.`)
- **缺失值**: 空字符串或 `NA`
- **标题行**: 第 1 行（列名）

### 列命名规范

- 使用下划线分隔：`Rock_Class1`
- 单位在括号中：`Age (Ma)`
- 避免特殊字符和空格

---

## 数据更新

### 版本说明

当前使用的数据版本：`onedz_csv_20260328`

**版本号格式**: `onedz_csv_YYYYMMDD`

### 更新流程

当新版本数据发布时：

1. **下载新数据**
   ```bash
   wget https://zenodo.org/record/xxxxx/files/onedz_csv_YYYYMMDD.tar.gz
   tar -xzf onedz_csv_YYYYMMDD.tar.gz
   ```

2. **更新 Handler 配置**
   ```python
   handler = OneDZHandler(
       data_path="/path/to/onedz_csv_YYYYMMDD/"
   )
   ```

3. **验证数据完整性**
   ```bash
   python onedz-skill/scripts/environment_check.py
   ```

---

## 数据引用

使用 OneDZ 数据时，请引用：

**Li, K., Hu, X., Chai, R., Yang, J. et al. (2025)**. OneDZ: A Global Detrital Zircon Database and Implications for Constructing Giant Geoscience Database. *Earth System Science Data*, 17, 1234-1256. https://doi.org/10.5194/essd-17-1234-2025

---

## 常见问题

### Q: 数据文件太大，内存不足？

**A**: 使用分块加载或限制查询范围。

```python
# 方法 1: 限制记录数
df = handler.query(max_records=100000)

# 方法 2: 使用过滤条件
df = handler.query(periods=["Cretaceous"], continent="Asia")
```

### Q: 如何使用自己的数据？

**A**: 确保数据格式与 OneDZ 一致。

```python
# 使用自定义 CSV
handler = OneDZHandler()
handler.load(source="csv", table="custom", path="/path/to/your.csv")
```

### Q: 数据中有多少个样品？

**A**:
- U-Pb 表: ~150,000 个样品（样品编号去重）
- Lu-Hf 表: ~50,000 个样品

一个样品可能包含多个锆石颗粒分析。

---

**维护者**: OneDZ Handler Team
**反馈**: 如遇数据问题，请查看 [GitHub Issues](https://github.com/KeranLi/Global-Detrital-Zircon/issues)
