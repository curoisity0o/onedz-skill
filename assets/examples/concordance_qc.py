#!/usr/bin/env python3
"""
================================================================================
AI-Friendly Example - Concordance Quality Control Analysis
================================================================================

Compare data retention rates under different concordance thresholds and
evaluate optimal filtering strategy for detrital zircon U-Pb data.

【AI Usage Guide】
1. This is a complete, runnable example
2. When user asks about "data quality", "concordance", "QC", or "filtering
   threshold", reference this example
3. Modify query parameters and threshold ranges as needed

【Key APIs】
- handler.query_from_csv(continent=..., rock_class1=[...])  # Lazy query
- handler.qc.compute_concordance(df)  # Add concordance column
- handler.qc.filter_concordance(df, concordance_min, concordance_max)  # Filter
- handler.clean(df, concordance_min=..., concordance_max=...)  # Full clean
- handler.plot_multi_kde({...})  # Comparison visualization

【Modification Template】
To adapt for different regions:
- Change continent/country_state in query_from_csv()
- Change thresholds list
- Change output file names

================================================================================

Concordance Quality Control Analysis
=====================================

Compare data retention and statistics under different concordance thresholds.

Data source: Li et al. (2025) OneDZ Database
"""

import sys
from pathlib import Path

SKILL_DIR = Path.home() / ".claude" / "skills" / "onedz"
sys.path.insert(0, str(SKILL_DIR))

from scripts.onedz_handler import OneDZHandler, OneDZConfig


# ── CONFIG ──────────────────────────────────────────────────────────
QUERY_PARAMS = {
    "continent": "Asia",
    "rock_class1": ["detrital"],
}

THRESHOLDS = [
    (0.80, 1.20, "Relaxed (80-120%)"),
    (0.90, 1.10, "Standard (90-110%)"),
    (0.95, 1.05, "Strict (95-105%)"),
]


def main():
    print("=" * 70)
    print("Concordance Quality Control Analysis")
    print(f"   Query: {QUERY_PARAMS}")
    print(f"   OneDZ Skill | Li et al. (2025)")
    print("=" * 70)

    # Step 1: Initialize
    print("\n[1/3] Initializing OneDZ Handler...")
    config = OneDZConfig(output_dir=Path.cwd(), use_timestamp_output=False)
    handler = OneDZHandler(config=config)

    # Step 2: Query data (lazy loading)
    print("\n[2/3] Querying data...")
    df = handler.query_from_csv(**QUERY_PARAMS)
    print(f"  Raw records: {df.height:,}")

    if df.height == 0:
        print("No data found. Exiting.")
        return

    # Compute concordance column
    df_conc = handler.qc.compute_concordance(df)

    # Multi-threshold comparison
    print(f"\n[3/3] Multi-threshold comparison...")
    print(f"\n  {'Threshold':<25s} {'Retained':>10s} {'Rate':>8s} {'Median':>10s}")
    print(f"  {'-'*60}")

    age_data = {}
    for lo, hi, label in THRESHOLDS:
        df_filt = handler.qc.filter_concordance(df_conc, concordance_min=lo, concordance_max=hi)
        rate = df_filt.height / df.height * 100

        df_clean = handler.clean(
            df_filt, compute_best_age=True, filter_concordance=False,
            remove_null_ages=True, age_range=(0, 4500),
        )
        result = handler.analyze(df_clean)
        s = result["summary"]

        print(f"  {label:<25s} {df_filt.height:>10,} {rate:>7.1f}% {s['median']:>9.0f} Ma")
        age_data[label] = df_clean["Best Age"].drop_nulls().to_numpy()

    # Comparison KDE
    if len(age_data) >= 2:
        handler.plot_multi_kde(age_data, age_range=(0, 4000), save="concordance_comparison_kde.png")
        print(f"\n  Comparison KDE: concordance_comparison_kde.png")

    print(f"\n{'='*70}")
    print(f"QC Analysis Complete!")
    print(f"{'='*70}")
    print(f"  Recommendation: Standard threshold (90-110%) balances data retention and quality.")


if __name__ == "__main__":
    main()
