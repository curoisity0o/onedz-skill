# OneDZ Skill — 标准化结构

> **版本**: 1.2.0
> **最后更新**: 2026-04-20
> **状态**: 🔄 重组中

---

## 📁 目录结构

```
onedz-skill/                      # 标准化 Skill 目录
├── SKILL.md                      # 英文核心说明（精简版，~200行）
├── SKILL_ZH.md                   # 中文核心说明
│
├── scripts/                      # 可执行脚本
│   ├── environment_check.py     # 环境检查
│   ├── data_explorer.py         # 数据集探索
│   └── README.md                # 脚本说明
│
├── references/                   # 参考文档和知识库
│   ├── environment.md           # 依赖环境说明
│   ├── dataset.md               # 数据集说明
│   ├── api_reference.md         # API 完整文档
│   ├── workflows.md             # 工作流示例
│   ├── cli_guide.md             # CLI 使用指南
│   └── README.md                # 文档导航
│
├── assets/                       # 附加资源
│   ├── examples/                # 示例脚本
│   │   ├── basic_query.py      # 基础查询
│   │   ├── age_distribution.py # 年龄分布
│   │   ├── luhf_analysis.py    # Lu-Hf 分析
│   │   ├── regional_comparison.py # 区域对比
│   │   └── README.md           # 示例说明
│   ├── templates/               # 配置模板
│   │   └── config_template.yaml
│   └── output/                  # 输出目录
│       └── .gitkeep
│
└── README.md                     # 本文件
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /path/to/my-OneDZ-skill
pip install -r requirements.txt
```

详细说明见 [references/environment.md](references/environment.md)

### 2. 验证环境

```bash
python onedz-skill/scripts/environment_check.py
```

### 3. 运行示例

```bash
# 基础查询
python onedz-skill/assets/examples/basic_query.py

# 年龄分布
python onedz-skill/assets/examples/age_distribution.py
```

---

## 📚 文档导航

### 核心文档

- **[SKILL.md](SKILL.md)** - 英文版核心说明
- **[SKILL_ZH.md](SKILL_ZH.md)** - 中文版核心说明

### 参考文档

- **[environment.md](references/environment.md)** - 环境依赖和安装
- **[dataset.md](references/dataset.md)** - 数据集说明
- **[api_reference.md](references/api_reference.md)** - API 完整参考
- **[workflows.md](references/workflows.md)** - 常见工作流
- **[cli_guide.md](references/cli_guide.md)** - CLI 工具指南

### 示例脚本

- **[basic_query.py](assets/examples/basic_query.py)** - 基础查询示例
- **[age_distribution.py](assets/examples/age_distribution.py)** - 年龄分布分析
- **[luhf_analysis.py](assets/examples/luhf_analysis.py)** - Lu-Hf 同位素分析
- **[regional_comparison.py](assets/examples/regional_comparison.py)** - 区域对比分析

---

## 🎯 主要改进

### 从旧结构迁移

| 旧结构 | 新结构 | 说明 |
|--------|--------|------|
| `skills/onedz.md` (690行) | `SKILL.md` (~200行) | 精简核心说明 |
| 文档分散在 `docs/skill/` | `references/` | 集中管理 |
| 脚本分散在多个目录 | `scripts/` | 标准化组织 |
| 无示例目录 | `assets/examples/` | 独立示例脚本 |
| 依赖在 SKILL.md 中 | `references/environment.md` | 独立管理 |

### 新结构优势

✅ **SKILL.md 精简** - 从 690 行减少到 ~200 行
✅ **文档集中** - 所有参考文档在 `references/`
✅ **脚本标准化** - 可执行脚本在 `scripts/`
✅ **示例独立** - 示例脚本可独立运行
✅ **配置模板化** - 配置文件在 `assets/templates/`

---

## 📖 使用指南

### 新用户

1. 阅读 [SKILL.md](SKILL.md) 或 [SKILL_ZH.md](SKILL_ZH.md)
2. 运行 [environment_check.py](scripts/environment_check.py) 验证安装
3. 尝试 [basic_query.py](assets/examples/basic_query.py) 示例
4. 查看 [workflows.md](references/workflows.md) 了解更多

### 开发者

1. 阅读 [api_reference.md](references/api_reference.md) 了解完整 API
2. 查看 [cli_guide.md](references/cli_guide.md) 使用命令行工具
3. 参考 [examples/](assets/examples/) 中的示例脚本
4. 修改 [config_template.yaml](assets/templates/config_template.yaml) 配置

### 高级用户

1. 使用 CLI 工具进行批量处理
2. 自定义配置文件
3. 创建自己的示例脚本
4. 参考完整文档进行高级分析

---

## 🔧 维护指南

### 添加新功能

1. **更新 SKILL.md** - 添加功能概述
2. **更新 api_reference.md** - 添加 API 文档
3. **创建示例** - 在 `assets/examples/` 中添加示例
4. **测试** - 确保所有功能正常

### 更新依赖

1. **修改 requirements.txt** - 更新依赖版本
2. **更新 environment.md** - 记录变更
3. **测试环境** - 运行 environment_check.py
4. **更新文档** - 记录兼容性变化

### 添加新脚本

1. **放置在正确位置**
   - 可执行脚本 → `scripts/`
   - 示例脚本 → `assets/examples/`

2. **添加文档** - 在 README.md 中说明

3. **测试** - 确保可独立运行

---

## 📊 与旧结构的映射

### 数据位置

旧结构默认数据路径：
```
/home/zry/my-OneDZ-skill/onedz_csv_20260328/
```

新结构支持：
```python
# 方法 1: 初始化时指定
handler = OneDZHandler(data_path="/your/path/")

# 方法 2: 环境变量
export ONEDZ_DATA_PATH="/your/path/"
```

### 导入路径

旧结构：
```python
from onedz_handler import OneDZHandler
```

新结构（相同）：
```python
from onedz_handler import OneDZHandler
```

### CLI 工具

旧结构和新结构都支持：
```bash
onedz query --period Cretaceous -o data.csv
```

---

## ⚠️ 注意事项

### 当前状态

- ✅ 新结构已创建
- ✅ 文档已迁移
- ✅ 脚本已组织
- ⏳ 旧结构保留（向后兼容）

### 迁移建议

1. **新用户**: 直接使用新结构
2. **现有用户**: 继续使用旧结构，逐步迁移
3. **开发者**: 开始使用新结构开发

### 兼容性

- ✅ 旧代码路径仍然有效
- ✅ 所有 API 保持不变
- ✅ 数据格式兼容
- ✅ CLI 命令兼容

---

## 🗺️ 下一步

### 短期计划

- [ ] 完善所有参考文档
- [ ] 添加更多示例脚本
- [ ] 创建交互式教程
- [ ] 添加单元测试

### 长期计划

- [ ] 创建 Web 界面
- [ ] 支持更多数据格式
- [ ] 优化大数据集性能
- [ ] 添加机器学习功能

---

## 📞 获取帮助

### 文档

- 查看 [SKILL.md](SKILL.md) 核心说明
- 阅读 [references/](references/) 详细文档
- 参考 [examples/](assets/examples/) 示例

### 问题反馈

- 提交 Issue 到 GitHub
- 查看 [FAQ](docs/skill/DOCS_INDEX.md)
- 联系维护团队

---

**维护者**: OneDZ Handler Team
**版本**: 1.2.0
**状态**: 🔄 重组中
**反馈**: 欢迎提出改进建议！
