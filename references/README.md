# OneDZ 参考文档导航

> **最后更新**: 2026-04-20
> **位置**: `onedz-skill/references/`

---

## 📚 文档目录

### 核心文档

| 文档 | 内容 | 难度 | 推荐人群 |
|------|------|------|----------|
| **[environment.md](environment.md)** | 环境依赖和安装 | ⭐ | 所有用户 |
| **[dataset.md](dataset.md)** | 数据集说明 | ⭐⭐ | 所有用户 |
| **[api_reference.md](api_reference.md)** | API 完整参考 | ⭐⭐⭐ | 开发者 |
| **[workflows.md](workflows.md)** | 工作流示例 | ⭐⭐ | 所有用户 |
| **[cli_guide.md](cli_guide.md)** | CLI 工具指南 | ⭐⭐ | 高级用户 |

---

## 🎯 按需求查找文档

### 我想...

#### 🚀 快速上手
→ 阅读 [SKILL.md](../SKILL.md) 核心说明
→ 运行 [environment_check.py](../scripts/environment_check.py)
→ 尝试 [basic_query.py](../assets/examples/basic_query.py)

#### 🔧 安装和配置
→ 查看 [environment.md](environment.md)
→ 了解 [dataset.md](dataset.md) 中的数据路径设置
→ 参考 [config_template.yaml](../assets/templates/config_template.yaml)

#### 📊 查询数据
→ [api_reference.md](api_reference.md) 的 `query()` 方法
→ [workflows.md](workflows.md) 的工作流 1
→ [dataset.md](dataset.md) 的数据结构

#### 🎨 生成图表
→ [api_reference.md](api_reference.md) 的可视化方法
→ [workflows.md](workflows.md) 的工作流 1 和 4
→ [cli_guide.md](cli_guide.md) 的 `plot` 命令

#### 🔬 Lu-Hf 分析
→ [api_reference.md](api_reference.md) 的 Lu-Hf 部分
→ [workflows.md](workflows.md) 的工作流 2
→ [luhf_analysis.py](../assets/examples/luhf_analysis.py) 示例

#### 📈 统计分析
→ [api_reference.md](api_reference.md) 的统计分析方法
→ [workflows.md](workflows.md) 的工作流 3
→ [regional_comparison.py](../assets/examples/regional_comparison.py) 示例

#### 💾 导出数据
→ [api_reference.md](api_reference.md) 的 `export()` 方法
→ [cli_guide.md](cli_guide.md) 的 `export` 命令
→ [dataset.md](dataset.md) 的导出格式说明

#### 🖥️ 使用命令行
→ [cli_guide.md](cli_guide.md) 完整指南
→ [workflows.md](workflows.md) 的工作流 5

---

## 📖 文档详细说明

### environment.md - 环境依赖说明

**内容**:
- Python 版本要求
- 核心依赖包列表（15个）
- 安装方法（pip、conda、源码）
- 环境验证
- 常见问题解决

**适合人群**: 所有用户

**何时查看**:
- 首次安装
- 依赖更新
- 遇到安装问题

---

### dataset.md - 数据集说明

**内容**:
- 数据集概述和来源
- 数据文件说明（zircon_upb.csv、zircon_luhf.csv）
- 数据结构详解（列名、含义）
- 自定义数据路径
- 数据下载和更新

**适合人群**: 所有用户

**何时查看**:
- 需要了解数据结构
- 自定义数据路径
- 数据更新

---

### api_reference.md - API 完整参考

**内容**:
- 所有方法的详细说明
- 参数列表和返回值
- 使用示例
- 方法分类（初始化、加载、查询、清洗、分析、可视化、导出）

**适合人群**: 开发者、高级用户

**何时查看**:
- 需要了解具体方法
- 编写自定义脚本
- 查询参数选项

---

### workflows.md - 工作流示例

**内容**:
- 6 个完整工作流
- 从基础到高级
- 每个工作流包含完整代码
- 输出说明
- 变体和扩展

**适合人群**: 所有用户

**何时查看**:
- 学习分析流程
- 寻找类似案例
- 复制代码修改

**工作流列表**:
1. 区域年龄谱（基础）
2. Lu-Hf 同位素演化（中级）
3. 区域对比分析（中级）
4. 统计探索（中级）
5. CLI 管道（高级）
6. 论文图表复现（高级）

---

### cli_guide.md - CLI 工具指南

**内容**:
- CLI 安装
- 所有命令详解（query、clean、analyze、plot、export、luhf、info）
- 管道操作
- 批量处理
- 高级用法

**适合人群**: 高级用户、系统管理员

**何时查看**:
- 使用命令行工具
- 批量处理
- 自动化工作流

---

## 🔍 快速查找

### 按关键词

**关键词**: 谐和度
→ [environment.md](environment.md) - 安装
→ [api_reference.md](api_reference.md) - `clean()` 方法
→ [workflows.md](workflows.md) - 所有工作流

**关键词**: KDE 图
→ [api_reference.md](api_reference.md) - `plot_age()` 方法
→ [workflows.md](workflows.md) - 工作流 1
→ [cli_guide.md](cli_guide.md) - `plot` 命令

**关键词**: εHf
→ [api_reference.md](api_reference.md) - Lu-Hf 部分
→ [workflows.md](workflows.md) - 工作流 2
→ [dataset.md](dataset.md) - 数据结构

**关键词**: 导出
→ [api_reference.md](api_reference.md) - `export()` 方法
→ [cli_guide.md](cli_guide.md) - `export` 命令
→ [dataset.md](dataset.md) - 格式说明

### 按任务

**任务**: 查询特定国家
→ [api_reference.md](api_reference.md) - `query()` 参数
→ [workflows.md](workflows.md) - 工作流 1 变体

**任务**: 生成出版级图表
→ [api_reference.md](api_reference.md) - 可视化参数
→ [workflows.md](workflows.md) - 工作流 6

**任务**: 批量处理
→ [cli_guide.md](cli_guide.md) - 管道操作
→ [workflows.md](workflows.md) - 工作流 5

**任务**: 统计检验
→ [api_reference.md](api_reference.md) - `ks_test()` 方法
→ [workflows.md](workflows.md) - 工作流 3

---

## 💡 使用建议

### 新手用户

1. **第一步**: 阅读 [SKILL.md](../SKILL.md) 前 3 节
2. **第二步**: 运行 [environment_check.py](../scripts/environment_check.py)
3. **第三步**: 查看 [workflows.md](workflows.md) 的工作流 1
4. **第四步**: 尝试 [basic_query.py](../assets/examples/basic_query.py)

### 有经验用户

1. **直接**: 查看 [api_reference.md](api_reference.md)
2. **参考**: [workflows.md](workflows.md) 找类似案例
3. **修改**: 复制示例代码适应需求

### 开发者

1. **详细**: [api_reference.md](api_reference.md) 完整 API
2. **工具**: [cli_guide.md](cli_guide.md) 命令行
3. **数据**: [dataset.md](dataset.md) 数据结构
4. **环境**: [environment.md](environment.md) 依赖管理

---

## 📊 文档关系图

```
SKILL.md (核心说明)
    ↓
    ├── references/environment.md (环境)
    ├── references/dataset.md (数据)
    ├── references/api_reference.md (API)
    ├── references/workflows.md (工作流)
    └── references/cli_guide.md (CLI)
         ↓
    assets/examples/ (示例)
        ├── basic_query.py
        ├── age_distribution.py
        ├── luhf_analysis.py
        └── regional_comparison.py
```

---

## 🔄 文档更新

### 更新日志

- **2026-04-20**: 创建参考文档结构
  - environment.md
  - dataset.md
  - api_reference.md
  - workflows.md
  - cli_guide.md

### 维护计划

- 每次功能更新时更新 API 文档
- 每次依赖变更时更新环境文档
- 收集用户反馈改进文档

---

**维护者**: OneDZ Handler Team
**反馈**: 文档有问题请提交 Issue
