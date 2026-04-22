# OneDZ 示例脚本

> **最后更新**: 2026-04-20
> **难度**: 初级到中级
> **位置**: `onedz-skill/assets/examples/`

---

## 示例列表

### 1. basic_query.py - 基础查询

**难度**: ⭐ 初级
**时间**: 3 分钟
**输出**: `basic_query_output.csv`

展示最基本的数据查询流程。

**包含内容**:
- 初始化 Handler
- 加载数据
- 基础查询（按时期、大洲、岩石类型）
- 数据清洗
- 基本统计
- 数据导出

**运行**:
```bash
python onedz-skill/assets/examples/basic_query.py
```

**适合人群**: 完全新手

---

### 2. age_distribution.py - 年龄分布分析

**难度**: ⭐⭐ 初级
**时间**: 5 分钟
**输出**: CSV、图表

亚洲白垩纪锆石年龄分布分析（完整案例）。

**包含内容**:
- 复杂查询条件
- 数据清洗（谐和度过滤）
- 年龄分布 KDE 图
- 峰值检测和标注
- 地理分布图
- 数据导出

**运行**:
```bash
python onedz-skill/assets/examples/age_distribution.py
```

**适合人群**: 有一定基础

---

### 3. luhf_analysis.py - Lu-Hf 同位素分析

**难度**: ⭐⭐ 中级
**时间**: 8 分钟
**输出**: CSV、多张图表

Lu-Hf 同位素数据处理完整流程。

**包含内容**:
- 加载 U-Pb 和 Lu-Hf 两个表
- 表连接（join）
- 计算 εHf(t) 和 TDM
- εHf(t) 演化图
- TDM 分布图
- εHf 分布直方图

**运行**:
```bash
python onedz-skill/assets/examples/luhf_analysis.py
```

**适合人群**: 熟悉基础操作

---

### 4. regional_comparison.py - 区域对比分析

**难度**: ⭐⭐ 中级
**时间**: 10 分钟
**输出**: 统计结果、对比图

中国和澳大利亚锆石年龄分布对比。

**包含内容**:
- 查询两个区域
- K-S 统计检验
- 多样本 KDE 对比图
- 统计结果解释

**运行**:
```bash
python onedz-skill/assets/examples/regional_comparison.py
```

**适合人群**: 需要统计对比

---

## 使用建议

### 学习路径

**第 1 步**: 运行 `basic_query.py`
- 了解基本流程
- 熟悉 API 调用
- 查看输出数据

**第 2 步**: 修改 `basic_query.py`
- 改变查询条件
- 尝试不同的清洗参数
- 理解每个步骤

**第 3 步**: 运行 `age_distribution.py`
- 学习完整分析流程
- 了解可视化选项
- 复制代码适应你的需求

**第 4 步**: 根据需求选择
- 需要 Lu-Hf 分析 → `luhf_analysis.py`
- 需要区域对比 → `regional_comparison.py`

### 自定义示例

**方法 1: 修改现有示例**
```bash
# 复制示例
cp onedz-skill/assets/examples/basic_query.py my_analysis.py

# 编辑修改
nano my_analysis.py

# 运行
python my_analysis.py
```

**方法 2: 从零开始**
```python
from onedz_handler import OneDZHandler

# 初始化
handler = OneDZHandler()

# 加载数据
handler.load()

# 你的查询
df = handler.query(
    periods=["Cretaceous"],
    continent="Your_Continent"
)

# 清洗
df_clean = handler.clean(df)

# 可视化
handler.plot_age(df_clean, save="my_plot.png")
```

---

## 示例脚本模板

创建你自己的示例时，可以参考这个模板：

```python
#!/usr/bin/env python3
"""
OneDZ 示例标题

简要描述示例的功能和用途。

用法:
    python onedz-skill/assets/examples/your_example.py

输出:
    - output1.csv (数据)
    - output1.png (图表)

作者: Your Name
日期: 2026-04-20
"""

from onedz_handler import OneDZHandler

def main():
    print("=" * 60)
    print("OneDZ 示例标题")
    print("=" * 60)

    # 1. 初始化
    print("\n[1] 初始化...")
    handler = OneDZHandler()

    # 2. 加载数据
    print("\n[2] 加载数据...")
    handler.load()

    # 3. 查询
    print("\n[3] 查询数据...")
    df = handler.query(...)

    # 4. 清洗
    print("\n[4] 清洗数据...")
    df_clean = handler.clean(df)

    # 5. 可视化
    print("\n[5] 生成图表...")
    handler.plot_age(df_clean, save="output.png")

    # 6. 导出
    print("\n[6] 导出数据...")
    handler.export(df_clean, "output.csv")

    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
```

---

## 常见修改

### 修改查询区域

```python
# 原始
df = handler.query(continent="Asia")

# 修改为你的区域
df = handler.query(continent="Europe")
# 或
df = handler.query(country_state="China")
```

### 修改时间范围

```python
# 按时期
df = handler.query(periods=["Cretaceous"])

# 按年龄范围（Ma）
df = handler.query(age_range=(100, 200))
```

### 修改清洗参数

```python
# 更严格
df_clean = handler.clean(df, concordance_min=0.95, concordance_max=1.05)

# 更宽松
df_clean = handler.clean(df, concordance_min=0.80, concordance_max=1.20)
```

### 修改图表

```python
# KDE 图
handler.plot_age(df_clean, mode="kde", save="kde.png")

# PDP 图
handler.plot_age(df_clean, mode="pdp", save="pdp.png")

# 自定义年龄范围
handler.plot_age(df_clean, age_range=(0, 500), save="custom.png")
```

---

## 输出文件说明

运行示例后会生成以下文件：

### 数据文件 (CSV)
- 包含查询和清洗后的数据
- 可用 Excel、文本编辑器打开
- 可导入其他分析工具

### 图表文件 (PNG)
- 高分辨率（默认 300 DPI）
- 可直接用于论文或报告
- 可用图像查看器打开

---

## 故障排除

### Q: 脚本报错找不到数据？

**A**: 检查数据路径：
```python
handler = OneDZHandler(data_path="/your/path/to/data/")
```

### Q: 图表中文显示为方块？

**A**: 使用英文标签或安装中文字体：
```python
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
```

### Q: 内存不足？

**A**: 限制查询范围：
```python
df = handler.query(max_records=10000)
```

---

**下一步**: 查看完整文档以了解更多功能
