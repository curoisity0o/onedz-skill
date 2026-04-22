#!/usr/bin/env python3
"""
================================================================================
AI-Friendly Example - Grouped Comparison Analysis
================================================================================

Compares detrital zircon age distributions across groups defined by any
categorical column (period, rock type, continent, country, etc.).

【AI Usage Guide】
1. This is a complete, runnable example
2. Copy and modify the CONFIG section below to adapt to user needs
3. Only modify items between "START CONFIG" and "END CONFIG"

【Key APIs】
- handler.query(country_state=...) / handler.query(continent=...)
- handler.clean(df, concordance_min=0.90)
- handler.analyze(df_clean)  → summary, peaks
- handler.ks_test(ages_a, ages_b)
- handler.plot_multi_kde({"Label": ages_array, ...})
- handler.viz.plot_geographic_distribution(df, geo_level=..., save=abs_path)

【Modification Template】
To adapt for different tasks, only change the CONFIG section:
- QUERY_PARAMS: change country/continent/period/rock_class1
- GROUP_COLUMN: change the column used to split data into groups
- GROUP_VALUES: change the list of group values to compare
- GROUP_LABELS: optional display labels (defaults to GROUP_VALUES)

================================================================================

Grouped Zircon Comparison Analysis
====================================

Compare zircon age distributions across groups within a dataset.

Data source: Li et al. (2025) OneDZ Database
"""

import sys
from pathlib import Path
from itertools import combinations

SKILL_DIR = Path.home() / ".claude" / "skills" / "onedz"
sys.path.insert(0, str(SKILL_DIR))

from scripts.onedz_handler import OneDZHandler, OneDZConfig

# ╔════════════════════════════════════════════════════════════════════╗
# ║  START CONFIG — Modify this section to adapt to user needs        ║
# ╚════════════════════════════════════════════════════════════════════╝

# Task identification
TASK_NAME = "grouped_comparison"  # Used for output folder name

# Query: filter data to a region/country before grouping
# Set to None to skip a filter. Common combinations:
#   country_state="China"
#   continent="Asia"
#   periods=["Cretaceous"]
#   rock_class1=["detrital"]
QUERY_PARAMS = {
    "country_state": "China",
}

# Grouping: which column to split data by
# Common choices:
#   "Depos.Age (Period)"  — by geological period
#   "Class-1 Rock Type"   — by major rock type
#   "Continent"           — by continent (if QUERY_PARAMS is empty)
#   "Country_State"       — by country (if querying a continent)
GROUP_COLUMN = "Depos.Age (Period)"

# Which group values to include (None = auto-detect top groups)
# Set to a list to specify exact groups, e.g.:
#   GROUP_VALUES = ["Cretaceous", "Jurassic", "Triassic"]
#   GROUP_VALUES = None  # auto-detect from data
GROUP_VALUES = [
    "Quaternary",
    "Neogene",
    "Paleogene",
    "Cretaceous",
    "Jurassic",
    "Triassic",
    "Permian",
    "Carboniferous",
    "Devonian",
    "Silurian",
    "Ordovician",
    "Cambrian",
    "Neoproterozoic",
    "Mesoproterozoic",
]

# Optional: custom labels for plots (defaults to GROUP_VALUES)
# e.g. {"Neoproterozoic": "Np", "Mesoproterozoic": "Mp"}
GROUP_LABELS = None

# Optional: merge small groups into larger categories
# e.g. {"Cenozoic": ["Quaternary", "Neogene", "Paleogene"], ...}
MERGE_GROUPS = None

# Minimum records per group (skip groups with fewer)
MIN_RECORDS_PER_GROUP = 50

# Output directory (will be created if not exists)
OUTPUT_DIR = None  # None = use TASK_DIR from step 0

# ╔════════════════════════════════════════════════════════════════════╗
# ║  END CONFIG — Do not modify below unless you know what you're doing║
# ╚════════════════════════════════════════════════════════════════════╝


def main():
    print("=" * 70)
    print("Grouped Zircon Comparison Analysis")
    print(f"   Query: {QUERY_PARAMS}")
    print(f"   Group by: {GROUP_COLUMN}")
    print(f"   OneDZ Skill | Li et al. (2025)")
    print("=" * 70)

    # ── Step 1: Initialize ──────────────────────────────────────────
    print("\n[1/5] Initializing OneDZ Handler...")

    output_dir = OUTPUT_DIR
    if output_dir is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path.cwd() / f"{TASK_NAME}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

    def out(filename):
        """Return absolute path for viz methods that don't use output_dir."""
        return str(Path(output_dir) / filename)

    print(f"  Output: {output_dir}")
    config = OneDZConfig(output_dir=output_dir, use_timestamp_output=False)
    handler = OneDZHandler(config=config)
    handler.load(source="csv", table="global_u-pb")
    print(f"  Global data loaded: {handler.data.height:,} records")

    # ── Step 2: Query data ──────────────────────────────────────────
    print(f"\n[2/5] Querying data ({QUERY_PARAMS})...")

    query_params = {k: v for k, v in QUERY_PARAMS.items() if v is not None}
    if query_params:
        df_raw = handler.query(**query_params)
    else:
        df_raw = handler.data

    print(f"  Raw records: {df_raw.height:,}")

    if df_raw.height == 0:
        print("  No data found. Exiting.")
        return

    # ── Step 3: Split by group & clean ──────────────────────────────
    print(f"\n[3/5] Splitting by '{GROUP_COLUMN}' and cleaning...")

    if GROUP_COLUMN not in df_raw.columns:
        print(f"  ERROR: Column '{GROUP_COLUMN}' not found.")
        print(f"  Available columns: {list(df_raw.columns)[:20]}...")
        return

    group_data = {}  # group_name -> (df_clean, ages, summary, peaks)

    if GROUP_VALUES is not None:
        groups_to_check = GROUP_VALUES
    else:
        # Auto-detect: get top 10 groups by record count
        counts = df_raw.group_by(GROUP_COLUMN).agg(
            pl_count=pl.len()
        ).sort("pl_count", descending=True)
        groups_to_check = counts[GROUP_COLUMN].drop_nulls().to_list()[:10]

    for group_val in groups_to_check:
        df_g = df_raw.filter(df_raw[GROUP_COLUMN] == group_val)

        if df_g.height < MIN_RECORDS_PER_GROUP:
            continue

        df_clean = handler.clean(
            df_g,
            compute_best_age=True,
            filter_concordance=True,
            concordance_min=0.90,
            concordance_max=1.10,
            standardize_errors=True,
            target_sigma=1,
            remove_null_ages=True,
            age_range=(0, 4500),
        )

        if df_clean.height < MIN_RECORDS_PER_GROUP:
            print(f"  {group_val:<30s}  skip ({df_clean.height} clean < {MIN_RECORDS_PER_GROUP})")
            continue

        ages = df_clean["Best Age"].drop_nulls().to_numpy()
        if len(ages) == 0:
            continue

        result = handler.analyze(df_clean)
        label = (GROUP_LABELS or {}).get(group_val, group_val)
        group_data[label] = (df_clean, ages, result["summary"], result["peaks"], group_val)

        print(f"  {label:<30s}  {df_g.height:>8,} raw  ->  {df_clean.height:>8,} clean  "
              f"(median {result['summary']['median']:.0f} Ma)")

    if len(group_data) < 2:
        print("  Not enough groups with data for comparison.")
        return

    # ── Step 4: K-S tests ──────────────────────────────────────────
    group_names = sorted(group_data.keys(), key=lambda g: group_data[g][2]["median"])
    ks_results = []

    print(f"\n[4/5] Pairwise K-S tests ({len(group_names)} groups)...")

    print(f"\n  {'Group A':<30s} {'Group B':<30s} {'D-stat':>8s} {'p-value':>12s} {'Sig':>5s}")
    print(f"  {'-'*88}")

    import polars as pl

    for ga, gb in combinations(group_names, 2):
        ages_a = group_data[ga][1]
        ages_b = group_data[gb][1]
        ks = handler.ks_test(ages_a, ages_b, alpha=0.05)
        ks_results.append((ga, gb, ks))
        sig = "***" if ks["p_value"] < 0.001 else "**" if ks["p_value"] < 0.01 else "*" if ks["significant"] else "ns"
        print(f"  {ga:<30s} {gb:<30s} {ks['statistic']:>8.4f} {ks['p_value']:>12.3e} {sig:>5s}")

    # ── Step 5: Visualizations ──────────────────────────────────────
    print("\n[5/5] Generating visualizations...")

    # 5.1 All-groups KDE
    all_ages = {g: group_data[g][1] for g in group_names}
    handler.plot_multi_kde(all_ages, age_range=(0, 4000), save="all_groups_kde.png")
    print("  [1] All-groups KDE: all_groups_kde.png")

    # 5.2 Merged groups KDE (if MERGE_GROUPS defined)
    if MERGE_GROUPS:
        import numpy as np
        merged_ages = {}
        for merge_name, sub_list in MERGE_GROUPS.items():
            parts = []
            for sub in sub_list:
                label = (GROUP_LABELS or {}).get(sub, sub)
                if label in group_data:
                    parts.append(group_data[label][1])
            if parts:
                merged_ages[merge_name] = np.concatenate(parts)

        if len(merged_ages) >= 2:
            handler.plot_multi_kde(merged_ages, age_range=(0, 4000), save="merged_groups_kde.png")
            print("  [2] Merged KDE:   merged_groups_kde.png")

    # 5.3 Individual group KDE plots
    for gname in group_names:
        fname = f"{gname.lower().replace(' ', '_')}_kde.png"
        handler.plot_age(
            group_data[gname][0],
            mode="kde",
            age_range=(0, 4000),
            show_peaks=True,
            save=fname,
        )
        print(f"  [3] {gname:<30s} -> {fname}")

    # ── Summary Table ───────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"SUMMARY: Grouped by {GROUP_COLUMN}")
    print(f"{'='*70}")

    print(f"  {'Group':<30s} {'N':>8s} {'Min':>8s} {'Max':>8s} {'Mean':>8s} {'Median':>8s} {'Std':>8s}")
    print(f"  {'-'*102}")

    for gname in group_names:
        s = group_data[gname][2]
        print(f"  {gname:<30s} {s['n']:>8,} {s['min']:>7.0f}Ma {s['max']:>7.0f}Ma "
              f"{s['mean']:>7.1f}Ma {s['median']:>7.0f}Ma {s['std']:>7.1f}Ma")

    # ── Export ──────────────────────────────────────────────────────
    print(f"\nExporting data...")
    dfs = [group_data[g][0] for g in group_names]
    df_all = pl.concat(dfs, how="vertical")
    handler.export(df_all, "all_groups_data.csv")
    print(f"  Exported: all_groups_data.csv ({df_all.height:,} records)")

    # ── Done ────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("Analysis Complete!")
    print(f"{'='*70}")

    n_sig = sum(1 for _, _, ks in ks_results if ks["significant"])
    print(f"\n  Groups compared: {len(group_names)}")
    print(f"  Significant K-S: {n_sig}/{len(ks_results)} ({n_sig/len(ks_results)*100:.0f}%)")


if __name__ == "__main__":
    main()
