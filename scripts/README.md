# OneDZ 可执行脚本和核心代码

> **最后更新**: 2026-04-20
> **位置**: `onedz-skill/scripts/`

---

## 目录结构

```
scripts/
├── onedz_handler/          # 核心代码包
│   ├── __init__.py
│   ├── analytics.py        # 统计分析
│   ├── cli/                # CLI 命令行工具
│   ├── config.py           # 配置管理
│   ├── data_engine.py      # 数据处理引擎
│   ├── export.py           # 数据导出
│   ├── luhf_calculator.py  # Lu-Hf 计算
│   ├── qc.py               # 质量控制
│   ├── utils.py            # 工具函数
│   └── viz.py              # 可视化
├── environment_check.py    # 环境检查脚本
├── data_explorer.py        # 数据集探索脚本
└── README.md               # 本文件
```

---

## 核心代码包：onedz_handler

这是 OneDZ 的核心处理引擎，包含所有数据加载、清洗、分析和可视化功能。

### 主要模块

- **analytics.py**: 统计分析（KDE、Bootstrap、K-S 检验）
- **cli/**: 命令行接口
- **data_engine.py**: 数据加载和查询引擎
- **export.py**: 多格式数据导出
- **luhf_calculator.py**: Lu-Hf 同位素计算
- **qc.py**: 数据质量控制
- **viz.py**: 可视化功能

### 使用方法

```python
from scripts.onedz_handler import OneDZHandler

handler = OneDZHandler()
handler.load()
df = handler.query(periods=["Cretaceous"])
```

---

## 可执行脚本

### environment_check.py

环境依赖检查脚本。

**功能**:
- 检查 Python 版本
- 验证所有依赖包是否安装
- 测试 OneDZ Handler 导入
- 检查数据集是否存在

**用法**:
```bash
cd onedz-skill
python scripts/environment_check.py
```

**预期输出**:
```
✅ Python 版本: 3.11.x
✅ polars: 0.20.x
✅ pandas: 2.0.x
✅ 所有依赖已安装
```

**适用场景**:
- 首次安装后验证
- 更新依赖后检查
- 排查环境问题

---

### data_explorer.py

OneDZ 数据集快速探索工具。

**功能**:
- 显示数据集基本信息
- 列出所有地质时期
- 列出所有岩石类型
- 列出所有大洲和国家
- 统计每个类别的记录数

**用法**:
```bash
cd onedz-skill
python scripts/data_explorer.py
```

**输出示例**:
```
OneDZ 数据集信息
==================

U-Pb 表:
  总记录数: 1,920,000+
  
地质时期:
  Cretaceous: 250,000 记录
  Jurassic: 180,000 记录
```

**适用场景**:
- 初次了解数据集
- 查询可用分类
- 规划分析策略

---

## 脚本使用建议

### 首次使用流程

1. **检查环境**
   ```bash
   python scripts/environment_check.py
   ```

2. **探索数据**
   ```bash
   python scripts/data_explorer.py
   ```

3. **运行示例**
   ```bash
   python assets/examples/basic_query.py
   ```

### 定期维护

- **更新依赖后**: 运行 `environment_check.py`
- **数据更新后**: 运行 `data_explorer.py`

---

## 导入说明

由于 `onedz_handler` 现在在 `scripts/` 目录下，导入时需要指定完整路径：

```python
from scripts.onedz_handler import OneDZHandler
```

或者在脚本开头添加路径：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from onedz_handler import OneDZHandler
```

---

## 常见问题

### Q: environment_check.py 报错缺少依赖？

**A**: 按照提示安装缺失的包：
```bash
pip install -r requirements.txt
```

### Q: data_explorer.py 找不到数据？

**A**: 确保数据路径正确：
```bash
# 设置环境变量
export ONEDZ_DATA_PATH="/path/to/data/"

# 或在代码中指定
handler = OneDZHandler(data_path="/path/to/data/")
```

### Q: 为什么导入路径变了？

**A**: 为了符合 Claude Code Skill 标准结构，核心代码包放在 `scripts/` 目录中，使整个 skill 结构自包含。

---

## 添加新脚本

如果你创建了新的实用脚本，可以添加到这个目录：

1. **命名规范**: 使用小写和下划线，如 `my_script.py`
2. **添加文档**: 在脚本开头添加文档字符串
3. **更新本文件**: 在这里添加说明

**模板**:
```python
#!/usr/bin/env python3
"""
OneDZ 脚本名称

简要描述脚本功能。

用法:
    python scripts/script_name.py [OPTIONS]

示例:
    python scripts/script_name.py --input data.csv
"""

from scripts.onedz_handler import OneDZHandler

def main():
    # 脚本逻辑
    pass

if __name__ == "__main__":
    main()
```

---

**维护者**: OneDZ Handler Team
**反馈**: 如有问题请提交 Issue
