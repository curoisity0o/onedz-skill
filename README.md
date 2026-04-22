# OneDZ Skill for Claude Code

A Claude Code skill that enables AI-assisted analysis of the world's largest detrital zircon database.

> **Based on**: Li, K., Hu, X., Chai, R., Yang, J. et al. (2025): OneDZ: A Global Detrital Zircon Database and Implications for Constructing Giant Geoscience Database, *Earth Syst. Sci. Data Discuss.* [preprint], https://doi.org/10.5194/essd-2025-157, in review, 2025.
>
> - GitHub: https://github.com/KeranLi/Global-Detrital-Zircon
> - Zenodo: https://zenodo.org/records/17407937
> - Website: https://onedz.top

---

## What It Does

This skill wraps the **OneDZ database** (1.92M U-Pb records, 270K Lu-Hf records) into a Claude Code skill, allowing users to perform geological zircon analysis through natural language commands.

**Example commands:**
```
/onedz 对比中国和印度的锆石数据
/onedz Compare China and Australia zircon data
/onedz 全球各大洲锆石年龄分布对比
/onedz Analyze Cretaceous detrital zircons in Asia
```

**What happens:**
1. AI reads the skill guidelines (SKILL.md)
2. Finds the best matching code template from examples
3. Generates a complete Python analysis script
4. Runs it and returns results (KDE plots, K-S tests, statistics, CSV exports)

---

## Interactive Demo

**[Open HTML Demo](assets/examples/onedz_skill_demo.html)** - A visual walkthrough of the skill's workflow with two real examples.

---

## Dataset

**OneDZ** (Li et al., 2025) is the world's largest detrital zircon database:

| Table | Records | Columns | Size |
|-------|---------|---------|------|
| U-Pb | ~1.92M | 72 | ~1.2 GB (CSV) |
| Lu-Hf | ~270K | 86 | ~164 MB (CSV) |

**Download:**
- Official: https://onedz.top/DownloadPage.html
- Zenodo: https://zenodo.org/records/17407937

**Citation:**
> Li, K., Hu, X., Chai, R., Yang, J. et al. (2025): OneDZ: A Global Detrital Zircon Database and Implications for Constructing Giant Geoscience Database, Earth Syst. Sci. Data Discuss. [preprint], https://doi.org/10.5194/essd-2025-157, in review, 2025.

---

## Skill Architecture

```
onedz-skill/
├── SKILL.md              # English skill entry (AI reads this first)
├── SKILL_ZH.md           # Chinese skill entry
├── scripts/              # Core handler implementation
│   └── onedz_handler/    # OneDZHandler API
├── assets/
│   └── examples/
│       ├── examples_index.md              # AI quick-match table
│       ├── regional_comparison.py         # Two-region comparison template
│       ├── grouped_comparison.py          # Multi-group comparison template
│       ├── age_distribution.py            # Age distribution analysis
│       ├── basic_query.py                 # Simple queries
│       ├── luhf_analysis.py               # Lu-Hf isotope analysis
│       ├── onedz_dataset_structure.json   # Lightweight data index (~50KB)
│       └── onedz_skill_demo.html          # Interactive demo
└── references/
    ├── api_reference.md    # Complete API documentation
    ├── quick_reference.md  # Quick lookup
    ├── workflows.md        # Step-by-step workflows
    ├── dataset.md          # Data structure guide
    ├── environment.md      # Setup instructions
    └── cli_guide.md        # CLI tool guide
```

---

## How the AI Workflow Works

When a user triggers `/onedz`, the AI follows a 6-step guided process:

| Step | Action | Purpose |
|------|--------|---------|
| 0 | Create task directory | Isolate outputs per analysis |
| 1 | Match `examples_index.md` | Find best code template |
| 1.5 | Check `onedz_dataset_structure.json` | Validate parameters without loading 1.5GB |
| 2 | Read API docs (if needed) | Fill gaps not covered by template |
| 3 | Generate & run script | Based on template, modified for user needs |
| 4 | Return results | Plots, tables, exports |

**Key design principle**: Reuse > Modify > Rewrite. The AI always starts from existing templates.

---

## Core API

```python
from scripts.onedz_handler import OneDZHandler, OneDZConfig

# Initialize
handler = OneDZHandler(config=OneDZConfig(output_dir="./output"))
handler.load(source="csv", table="global_u-pb")

# Query → Clean → Analyze → Visualize → Export
df = handler.query(country_state="China", periods=["Cretaceous"])
df_clean = handler.clean(df, concordance_min=0.90)
result = handler.analyze(df_clean)  # summary, peaks
handler.plot_age(df_clean, mode="kde", save="kde.png")
handler.export(df_clean, "output.csv")

# Statistical comparison
ks = handler.ks_test(ages_a, ages_b)
handler.plot_multi_kde({"China": ages_cn, "India": ages_in}, save="compare.png")
```

---

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify
python scripts/environment_check.py

# Set data path (one of)
export ONEDZ_DATA_PATH="/path/to/onedz_csv/"
# Or specify in code: OneDZConfig(csv_dir=Path("/path/to/"))
```

---

## Example Results

### China vs India Zircon Comparison

| Metric | China | India |
|--------|-------|-------|
| Raw records | 829,781 | 16,186 |
| Clean records | 524,049 | 11,969 |
| Median age (Ma) | 1,098 | 1,759 |
| K-S test | D=0.2078, p≈0 | **Significant** |

### Global Continent Comparison

7 continents compared, **21/21 pairwise K-S tests significant** (all distributions differ).

| Continent | N (clean) | Median (Ma) |
|-----------|-----------|-------------|
| Asia | 697,877 | 991 |
| N_America | 318,061 | 1,427 |
| S_America | 133,112 | 1,157 |
| Europe | 102,462 | 978 |
| Africa | 97,906 | 1,184 |
| Australia_Papua | 38,880 | 1,638 |
| Antarctica | 19,823 | 975 |

---

## Version

- **v1.2.0** (2026-04-20): Restructured, added examples system, grouped_comparison template
- **v1.1.0** (2026-04-17): Phase 5 visualizations, CLI enhancements
- **v1.0.0** (2026-04-16): Initial release

---

## License

This skill tool is provided for research use. The OneDZ database is published under the terms described in the original paper (Li et al., 2025).
