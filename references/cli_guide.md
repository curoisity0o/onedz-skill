# OneDZ CLI 命令行工具完整指南

> **最后更新**: 2026-04-20
> **版本**: v1.1.0+

---

## 快速开始

### 安装 CLI

```bash
cd /home/zry/my-OneDZ-skill
pip install -e .
```

验证安装：
```bash
onedz --version
onedz --help
```

---

## 命令概览

| 命令 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `query` | 多维数据查询 | 无 | CSV |
| `clean` | 数据清洗 | CSV | CSV |
| `analyze` | 统计分析 | CSV | TXT |
| `plot` | 可视化 | CSV | PNG |
| `export` | 格式转换 | CSV | 多格式 |
| `luhf` | Lu-Hf 分析 | CSV | CSV/PNG |
| `info` | 数据集信息 | 无 | TXT |

---

## 核心命令详解

### 1. query - 数据查询

查询特定条件的数据。

**基本语法**:
```bash
onedz query [OPTIONS] -o OUTPUT.csv
```

**常用选项**:
- `--period TEXT`: 地质时期（如 Cretaceous）
- `--continent TEXT`: 大洲（如 Asia）
- `--country TEXT`: 国家
- `--rock-class1 TEXT`: 一级岩石分类
- `--instrument TEXT`: 仪器类型
- `--age-range MIN MAX`: 年龄范围
- `--max-records INTEGER`: 最大记录数
- `-o, --output PATH`: 输出文件

**示例**:
```bash
# 查询亚洲白垩纪数据
onedz query --period Cretaceous --continent Asia -o asia.csv

# 查询特定年龄范围
onedz query --age-range 100 200 -o age_range.csv

# 查询特定岩石类型
onedz query --rock-class1 detrital -o detrital.csv

# 组合查询
onedz query --period Jurassic --continent Europe --max-records 10000 -o jurassic_europe.csv
```

---

### 2. clean - 数据清洗

科学级数据质量控制。

**基本语法**:
```bash
onedz clean --input INPUT.csv [OPTIONS] -o OUTPUT.csv
```

**清洗选项**:
- `--input PATH`: 输入文件（必需）
- `--concordance-min FLOAT`: 最小谐和度（默认 0.90）
- `--concordance-max FLOAT`: 最大谐和度（默认 1.10）
- `--age-min INTEGER`: 最小年龄（Ma）
- `--age-max INTEGER`: 最大年龄（Ma）
- `--no-best-age`: 不计算最佳年龄
- `--no-standardize`: 不标准化误差
- `-o, --output PATH`: 输出文件

**示例**:
```bash
# 基础清洗
onedz clean --input raw.csv -o clean.csv

# 严格质量控制
onedz clean --input raw.csv --concordance-min 0.95 --concordance-max 1.05 -o clean.csv

# 年龄范围过滤
onedz clean --input raw.csv --age-min 0 --age-max 3000 -o clean.csv

# 不过滤谐和度
onedz clean --input raw.csv --no-best-age -o clean.csv
```

---

### 3. analyze - 统计分析

计算统计信息和峰值检测。

**基本语法**:
```bash
onedz analyze --input INPUT.csv [OPTIONS] -o OUTPUT.txt
```

**分析选项**:
- `--input PATH`: 输入文件（必需）
- `--peaks`: 执行峰值检测
- `--peaks-threshold FLOAT`: 峰值阈值（默认 0.05）
- `--bootstrap`: 执行自助法
- `--n-iterations INTEGER`: 迭代次数（默认 1000）
- `-o, --output PATH`: 输出文件

**示例**:
```bash
# 基本统计
onedz analyze --input data.csv -o stats.txt

# 峰值检测
onedz analyze --input data.csv --peaks -o stats_with_peaks.txt

# 自助法不确定度
onedz analyze --input data.csv --bootstrap --n-iterations 5000 -o bootstrap.txt
```

---

### 4. plot - 可视化

生成各种类型的图表。

**基本语法**:
```bash
onedz plot --input INPUT.csv --plot-type TYPE [OPTIONS] -o OUTPUT.png
```

**图表类型**:

| 类型 | 说明 | 特定选项 |
|------|------|----------|
| `kde` | 年龄概率密度（KDE） | `--age-range`, `--bandwidth` |
| `pdp` | 概率密度图 | `--age-range` |
| `epsilon_hf` | εHf(t) 演化图 | `--color-by` |
| `tdm` | TDM 模式年龄分布 | `--model dm1\|dm2` |
| `rock_type_stats` | 岩石类型统计 | `--class-level`, `--top-n`, `--plot-format` |
| `geo_distribution` | 地理分布 | `--geo-level`, `--top-n` |
| `temporal_distribution` | 时间分布 | 无 |

**通用选项**:
- `--input PATH`: 输入文件（必需）
- `--plot-type TEXT`: 图表类型（必需）
- `--dpi INTEGER`: 图像分辨率（默认 300）
- `--fig-size WIDTH HEIGHT`: 图像尺寸
- `-o, --output PATH`: 输出文件

**示例**:
```bash
# KDE 图
onedz plot --input data.csv --plot-type kde -o kde.png

# 指定年龄范围
onedz plot --input data.csv --plot-type kde --age-range 0 3000 -o kde.png

# εHf(t) 演化图
onedz plot --input luhf.csv --plot-type epsilon_hf -o epsilon_hf.png

# 按大洲着色
onedz plot --input luhf.csv --plot-type epsilon_hf --color-by Continent -o epsilon_hf.png

# TDM 分布
onedz plot --input luhf.csv --plot-type tdm --model dm2 -o tdm2.png

# 岩石类型统计
onedz plot --input data.csv --plot-type rock_type_stats --class-level Class1 --plot-format bar -o rock_stats.png

# 地理分布
onedz plot --input data.csv --plot-type geo_distribution --geo-level continent --top-n 10 -o geo_dist.png

# 时间分布
onedz plot --input data.csv --plot-type temporal_distribution -o temporal_dist.png
```

---

### 5. export - 格式转换

导出为多种格式。

**基本语法**:
```bash
onedz export --input INPUT.csv --output OUTPUT.ext
```

**支持格式**:
- `.csv`: CSV 格式
- `.xlsx`: Excel 格式
- `.json`: JSON 格式
- `.geojson`: GeoJSON 格式
- `.shp`: Shapefile 格式

**示例**:
```bash
# 导出为 Excel
onedz export --input data.csv --output result.xlsx

# 导出为 GeoJSON
onedz export --input data.csv --output result.geojson

# 导出为 Shapefile
onedz export --input data.csv --output result.shp
```

---

### 6. luhf - Lu-Hf 分析

Lu-Hf 同位素数据处理。

**子命令**:
- `join`: 连接 U-Pb 和 Lu-Hf 表
- `compute`: 计算 εHf(t) 和 TDM

**6.1 join - 连接表**
```bash
onedz luhf join [OPTIONS] -o OUTPUT.csv
```

**选项**:
- `--join-key TEXT`: 连接键（默认 Ref_Sample_Key）
- `-o, --output PATH`: 输出文件

**示例**:
```bash
# 基础连接
onedz luhf join -o joined.csv

# 自定义连接键
onedz luhf join --join-key Sample_ID -o joined.csv
```

**6.2 compute - 计算 εHf(t)**
```bash
onedz luhf compute --input INPUT.csv -o OUTPUT.csv
```

**示例**:
```bash
# 计算
onedz luhf compute --input joined.csv -o computed.csv
```

**完整工作流**:
```bash
# 连接 → 计算 → 可视化
onedz luhf join -o joined.csv
onedz luhf compute --input joined.csv -o computed.csv
onedz plot --input computed.csv --plot-type epsilon_hf -o epsilon.png
```

---

### 7. info - 数据集信息

显示数据集元数据。

**语法**:
```bash
onedz info
```

**输出**:
```
OneDZ 数据集信息
==================

数据路径: /path/to/onedz_csv_20260328/

U-Pb 表:
  记录数: 1,920,000+
  列数: 72
  时间范围: 0 - 4500 Ma

Lu-Hf 表:
  记录数: 270,000+
  列数: 86

地理覆盖:
  大洲: 7
  国家: 100+
  样品数: 150,000+
```

---

## 管道操作

CLI 支持管道操作，可以实现工作流自动化。

### 基本管道

```bash
# 查询 → 清洗 → 绘图
onedz query --period Cretaceous --continent Asia | \
onedz clean --concordance-min 0.90 | \
onedz plot --plot-type kde -o cretaceous_kde.png
```

### 批量处理

```bash
# 批量处理多个时期
for period in Triassic Jurassic Cretaceous; do
  onedz query --period $period | \
  onedz clean | \
  onedz plot --plot-type kde -o ${period}_kde.png
done
```

### 复杂工作流

```bash
# 查询 → 清洗 → 分析 → 绘图 → 导出
onedz query --continent Asia | \
onedz clean --age-min 0 --age-max 4000 | \
tee intermediate.csv | \
onedz analyze --peaks -o stats.txt && \
onedz plot --input intermediate.csv --plot-type kde -o kde.png && \
onedz export --input intermediate.csv --output result.geojson
```

---

## 高级用法

### 自定义配置文件

创建 `config.yaml`:
```yaml
cleaning:
  concordance_min: 0.95
  concordance_max: 1.05
  age_min: 0
  age_max: 4000

plot:
  dpi: 300
  fig_size: [12, 8]
```

使用配置：
```bash
onedz clean --config config.yaml --input raw.csv -o clean.csv
```

### 日志记录

```bash
# 启用详细日志
onedz --verbose query --period Cretaceous -o data.csv

# 保存日志
onedz --log-file analysis.log query --period Cretaceous -o data.csv
```

### 并行处理

```bash
# 并行处理多个查询
for continent in Asia Europe Africa; do
  (onedz query --continent $continent --period Cretaceous -o ${continent}.csv &)
done
wait
```

---

## 常见问题

### Q: 如何查看命令的帮助？

**A**:
```bash
onedz COMMAND --help
# 例如
onedz query --help
```

### Q: 如何处理大数据集？

**A**: 使用 `--max-records` 限制：
```bash
onedz query --max-records 10000 -o sample.csv
```

### Q: 管道操作失败怎么办？

**A**: 检查中间步骤：
```bash
# 保存中间结果
onedz query --period Cretaceous -o step1.csv
onedz clean --input step1.csv -o step2.csv
onedz plot --input step2.csv --plot-type kde -o result.png
```

### Q: 如何批量生成图表？

**A**: 使用 Shell 脚本：
```bash
#!/bin/bash
for period in Triassic Jurassic Cretaceous; do
  onedz query --period $period -o ${period}.csv
  onedz plot --input ${period}.csv --plot-type kde -o ${period}_kde.png
done
```

---

## 性能优化

### 加速查询

```bash
# 只查询需要的列
onedz query --period Cretaceous --columns "Best Age,Latitude,Longitude" -o data.csv

# 限制记录数
onedz query --max-records 1000 -o sample.csv
```

### 内存优化

```bash
# 分块处理
onedz query --period Cretaceous --chunk-size 10000 -o data.csv
```

---

**下一步**: 查看 [工作流示例](workflows.md) 了解完整分析流程
