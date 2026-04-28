# 环境依赖说明

> **最后更新**: 2026-04-28
> **适用于**: OneDZ Handler v1.2.0+

---

## Python 版本要求

- **最低版本**: Python ≥ 3.11
- **推荐版本**: Python 3.11 或 3.12

**检查 Python 版本**:
```bash
python --version
```

---

## 核心依赖包（15个）

### 数据处理引擎
```
polars>=0.20.0       # 高性能数据处理引擎
pandas>=2.0.0        # 数据分析
numpy>=1.24.0        # 数值计算
```

### 可视化
```
matplotlib>=3.7.0    # 绘图库
```

### 地理数据处理
```
geopandas>=0.14.0    # 地理数据处理
shapely>=2.0.0       # 几何运算
```

### 统计分析
```
scipy>=1.11.0        # 统计分析
scikit-learn>=1.3.0  # 机器学习（用于聚类）
```

### 报告生成
```
nbformat>=5.9.0      # Notebook 生成
jupyter>=1.0.0       # nbconvert HTML 导出
plotly>=5.15.0       # 交互式可视化
```

### 数据导出
```
openpyxl>=3.1.0      # Excel 导出
```

### CLI 和配置
```
click>=8.0.0         # CLI 框架
pyyaml>=6.0          # YAML 配置文件
```

### 实用工具
```
tqdm>=4.65.0         # 进度条
jinja2>=3.1.0        # 模板引擎
```

### 数据库（可选）
```
pymysql>=1.1.0       # MySQL 连接
sqlalchemy>=2.0.0    # ORM 框架
```

---

## 安装方法

### 方法 1: pip 安装（推荐）

**从项目根目录**:
```bash
cd /path/to/my-OneDZ-skill
pip install -r requirements.txt
```

**或从 PyPI 安装**（如果已发布）:
```bash
pip install onedz-handler
```

### 方法 2: conda 安装

```bash
# 使用 conda 安装主要依赖
conda install -c conda-forge polars pandas numpy scipy matplotlib geopandas

# 使用 pip 安装剩余依赖
pip install openpyxl click pyyaml tqdm jinja2 scikit-learn shapely
```

### 方法 3: 从源码安装（开发模式）

```bash
cd /path/to/my-OneDZ-skill
pip install -e .
```

**优势**:
- 可以直接修改代码并立即生效
- 无需重新安装即可更新

### 方法 4: 使用虚拟环境（推荐）

**创建虚拟环境**:
```bash
# 使用 venv
python -m venv onedz-env
source onedz-env/bin/activate  # Linux/Mac
# 或
onedz-env\Scripts\activate  # Windows

# 使用 conda
conda create -n onedz python=3.11
conda activate onedz
```

**然后安装依赖**:
```bash
pip install -r requirements.txt
```

---

## 环境灵活性

✅ **不限于特定环境** - OneDZ Handler 可以使用：

- **venv** 虚拟环境
- **conda** 环境
- **pyenv** 管理
- **Poetry** 或 **Pipenv** 等工具
- 系统 Python（不推荐，可能污染系统环境）

✅ **任何安装方式** - 只要确保依赖已安装即可

---

## 验证安装

### 快速检查（5秒）

```bash
python -c "import polars, pandas, matplotlib, geopandas; print('✅ 核心依赖已安装')"
```

### 完整检查

```bash
# 运行环境检查脚本
python onedz-skill/scripts/environment_check.py
```

**预期输出**:
```
✅ Python 版本: 3.11.x
✅ polars: 0.20.x
✅ pandas: 2.0.x
✅ numpy: 1.24.x
✅ matplotlib: 3.7.x
✅ geopandas: 0.14.x
✅ scipy: 1.11.x
✅ scikit-learn: 1.3.x
✅ shapely: 2.0.x
✅ openpyxl: 3.1.x
✅ click: 8.0.x
✅ pyyaml: 6.0.x
✅ tqdm: 4.65.x
✅ jinja2: 3.1.x

✅ 所有依赖已安装，可以正常使用 OneDZ Handler！
```

### 测试导入

```python
# test_import.py
from scripts.onedz_handler import OneDZHandler
handler = OneDZHandler()
print("✅ OneDZ Handler 导入成功")
```

---

## 常见问题

### Q: polars 安装失败怎么办？

**A**: polars 需要编译，可能需要 Rust 工具链。

**解决方案**:
```bash
# 方法 1: 使用预编译的 wheel
pip install --upgrade pip
pip install polars --no-cache-dir

# 方法 2: 使用 conda
conda install -c conda-forge polars
```

### Q: geopandas 安装失败？

**A**: geopandas 依赖 GEOS、GDAL 等库。

**解决方案**:
```bash
# 使用 conda（推荐）
conda install -c conda-forge geopandas

# 或安装系统依赖后使用 pip
# Ubuntu/Debian
sudo apt-get install libgeos-dev gdal-bin

# Mac
brew install geos gdal
```

### Q: matplotlib 中文显示为方块？

**A**: 需要配置中文字体。

**解决方案**:
```python
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
```

或使用英文标签避免字体问题。

### Q: ImportError: No module named 'onedz_handler'？

**A**: 需要安装项目本身。

**解决方案**:
```bash
cd /path/to/my-OneDZ-skill
pip install -e .
```

---

## 依赖版本兼容性

### 测试过的环境

| Python | polars | pandas | matplotlib | 状态 |
|--------|--------|--------|------------|------|
| 3.11   | 0.20.0 | 2.0.0  | 3.7.0      | ✅   |
| 3.12   | 0.20.0 | 2.0.0  | 3.7.0      | ✅   |

### 已知问题

- Python 3.10: 部分功能可能不兼容
- polars < 0.20.0: API 不兼容
- pandas < 2.0.0: 类型注解不支持

---

## 更新日志

- **2026-04-20**: 创建文档，整理依赖清单
- **待更新**: 根据实际使用反馈补充

---

**维护者**: OneDZ Handler Team
**反馈**: 如遇安装问题，请提交 Issue
