# OneDZ 输出目录管理

## 功能概述

OneDZ Skill 现在支持统一的输出目录管理，所有分析结果（图表、数据文件等）都会自动保存到带时间戳的输出目录中，避免文件散落和版本混乱。

## 默认行为

### 自动创建时间戳目录

当你初始化 `OneDZHandler` 时，会自动创建一个带时间戳的输出目录：

```python
handler = OneDZHandler()
# 输出: 📁 输出目录: onedz_output/onedz_output_20260420_160517
```

### 目录结构

```
onedz_output/
├── onedz_output_20260420_160517/
│   ├── china_data.csv
│   ├── australia_data.csv
│   ├── china_kde.png
│   ├── australia_kde.png
│   └── china_australia_kde.png
└── onedz_output_20260420_161230/
    └── (另一次运行的文件)
```

## 使用方法

### 1. 自动输出管理（推荐）

使用 `handler.save_figure()` 和 `handler.export()` 方法：

```python
from scripts.onedz_handler import OneDZHandler
import matplotlib.pyplot as plt

# 初始化handler
handler = OneDZHandler()

# 加载和分析数据
handler.load()
df = handler.query(periods=["Cretaceous"])
df_clean = handler.clean(df)

# 生成图表
fig = handler.plot_age_distribution(df_clean, mode="kde")
handler.save_figure(fig, "cretaceous_kde.png")  # 自动保存到时间戳目录
plt.close(fig)

# 导出数据
handler.export(df_clean, "cretaceous_data.csv")  # 自动保存到时间戳目录
```

### 2. 自定义输出路径

如果你想使用自定义的输出目录或禁用时间戳：

```python
from scripts.onedz_handler import OneDZHandler, OneDZConfig
from pathlib import Path

# 自定义配置
config = OneDZConfig(
    output_dir=Path("./my_output"),      # 自定义基础目录
    use_timestamp_output=False,           # 禁用时间戳
)

handler = OneDZHandler(config=config)
# 所有输出将保存到: ./my_output/
```

### 3. 获取输出路径

如果需要知道当前的输出路径：

```python
output_path = handler.get_output_path("my_file.csv")
print(output_path)  # onedz_output/onedz_output_20260420_160517/my_file.csv
```

## 配置选项

### OneDZConfig 输出相关参数

```python
@dataclass
class OneDZConfig:
    # 输出目录配置
    output_dir: Path = Path("./onedz_output")      # 基础输出目录
    use_timestamp_output: bool = True               # 是否使用时间戳子目录
    timestamp_format: str = "%Y%m%d_%H%M%S"         # 时间戳格式
```

### 修改时间戳格式

```python
config = OneDZConfig(
    timestamp_format="%Y-%m-%d_%H-%M-%S"  # 2026-04-20_16-05-17
)
handler = OneDZHandler(config=config)
```

## 完整示例

```python
#!/usr/bin/env python3
from pathlib import Path
import matplotlib.pyplot as plt
from scripts.onedz_handler import OneDZHandler

# 1. 初始化handler
handler = OneDZHandler()

# 2. 加载数据
handler.load(source="csv", table="global_u-pb")

# 3. 查询和清洗数据
df = handler.data.filter(
    pl.col("Country_State") == "China"
)
df_clean = handler.clean(df, concordance_min=0.90)

# 4. 统计分析
china_ages = df_clean["Best Age"].drop_nulls().to_numpy()
print(f"平均年龄: {china_ages.mean():.1f} Ma")

# 5. 可视化
fig = handler.plot_age_distribution(df_clean, mode="kde")
handler.save_figure(fig, "china_age_distribution.png")
plt.close(fig)

# 6. 导出数据
handler.export(df_clean, "china_cleaned_data.csv")

# 7. 查看输出目录
print(f"所有文件已保存到: {handler._timestamped_output_dir}")
```

## 优势

1. **组织性**: 所有输出文件自动按时间组织
2. **版本控制**: 每次运行都有独立的输出目录
3. **可追溯性**: 从目录名就能知道分析时间
4. **避免覆盖**: 不会意外覆盖之前的结果
5. **易于管理**: 可以轻松删除旧的分析结果

## 注意事项

1. **磁盘空间**: 每次运行都会创建新目录，注意定期清理
2. **大文件**: 如果导出的数据文件很大，注意磁盘容量
3. **路径引用**: 使用 `handler.get_output_path()` 而不是硬编码路径

## 清理旧输出

```bash
# 删除所有输出目录
rm -rf onedz_output/

# 只删除特定日期之前的输出
find onedz_output/ -type d -name "onedz_output_*" -mtime +7 -exec rm -rf {} \;

# 保留最近3次的输出
cd onedz_output/
ls -td onedz_output_* | tail -n +4 | xargs rm -rf
```

---

**更新时间**: 2026-04-20
**OneDZ版本**: v1.2.0+
