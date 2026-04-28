# Changelog

## v1.4.0 (2026-04-28)

### 新增
- **ReportGenerator**: 通用报告生成框架，将分析图表、表格、代码输出打包为出版级 Jupyter Notebook + HTML
  - `AnalysisContext` — 灵活的内容容器，支持 markdown、code cell、图片（base64 内嵌）、表格、核心发现
  - `ReportGenerator` — 格式层，将 `AnalysisContext` 渲染为 `.ipynb` 并支持 nbconvert 转 `.html`
  - CSS 专业排版：系统字体、条目化表格、图片阴影、代码样式、发现卡片、响应式/打印适配
  - HTML CSS 注入：自动处理 nbconvert 对 `<style>` 标签的转义问题
  - 图片 base64 内嵌：HTML 自包含，无需外部文件
- **综合报告示例** (`assets/examples/report_generation.py`): 展示 8 种图表类型（KDE、堆叠柱状图、饼图、εHf 散点、热力图、累积概率、谐和图、多面板组合）+ 交互式 Plotly
- **requirements.txt**: 项目依赖清单

### 修复
- 图标题居中被 Jupyter CSS (`.jp-RenderedHTMLCommon p text-align: left`) 覆盖问题
- nbconvert 将 `<style>` 转义为 `&lt;style&gt;` 导致的 CSS 失效问题

### 更新
- `examples_index.md`: 新增 `report_generation` 快速匹配条目和详细说明
- `references/environment.md`: 添加报告生成依赖项

---

## v1.3.0 (2026-04-24)

### 新增
- **新数据集适配 (Zenodo #19690702)**: 支持分片格式数据集 (`Total_UPb_split_parts/` + `Total_LuHf_split_parts/`)
  - adapter 配置: `adapters/v20260328_new.json` (31 个 U-Pb + 16 个 Lu-Hf 列名映射)
  - `query_from_csv()` 支持分片文件惰性扫描（22 个 U-Pb 分片 + 3 个 Lu-Hf 分片自动合并）
  - 新旧数据集通过 adapter 自动检测，无需修改代码
- **脏数据诊断**: 数据加载后自动报告数值列中的异常值（编码损坏、格式异常），按异常数量降序输出
- **峰值检测诊断**: `find_peaks()` 返回 0 个峰时输出 prominence 与密度值信息，帮助使用者判断参数是否合理
- **动态数值列检测**: `_post_process()` 自动识别未在硬编码列表中的数值列（如新数据集的 `epsilon_Hf_t`, `Upb_Age`, `TDM1_Ma`）

### 修复
- **分片数据集初始化验证**: `dataset_info.py` 现在正确识别分片格式目录，不再打印误导性"数据集未找到"提示
- **分片数据集信息展示**: `print_dataset_info()` 显示分片文件数和总大小

### 已知问题
- 新数据集 Lu-Hf 分片中存在编码损坏（约 200 个 εHf(t) 负值被乱码替代，源数据问题）
- `find_peaks()` 默认 `prominence=0.01` 对 OneDZ 典型 KDE 密度量级可能偏高，使用者可根据诊断输出调整

### 测试
- 5 个典型场景通过新旧数据集双重验证（KDE 分布、谐和度 QC、Lu-Hf 同位素、地层对比、物源综合分析）

---

## v1.2.0 (2026-04-20)

- 重组技能包结构
- 新增示例系统 (examples_index.md)
- 新增分组对比模板 (grouped_comparison.py)
- 新增 concordance_qc.py 和 provenance_analysis.py 示例

## v1.1.0 (2026-04-17)

- Phase 5 可视化增强
- CLI 命令完善

## v1.0.0 (2026-04-16)

- 初始发布
- 支持 U-Pb 数据查询、清洗、分析、可视化、导出
- 支持 K-S 检验
- 支持 Lu-Hf 同位素数据
