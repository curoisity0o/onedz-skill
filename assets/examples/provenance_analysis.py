#!/usr/bin/env python3
"""
================================================================================
AI-Friendly Example - Provenance Analysis (U-Pb + Lu-Hf Integrated)
================================================================================

Integrated provenance discrimination combining U-Pb age peaks and Lu-Hf
εHf(t) isotope characteristics. Two-phase approach to avoid OOM on
memory-constrained systems.

【AI Usage Guide】
1. When user asks about "provenance", "source area", "crustal evolution",
   "U-Pb + Lu-Hf combined analysis", reference this example
2. Phase 1 uses lazy U-Pb query; Phase 2 loads only Lu-Hf table
3. Modify country_state to target different regions

【Key APIs】
- handler.query_from_csv(country_state=...)  # Phase 1: U-Pb (lazy)
- handler.load(source="csv", table="global_lu-hf")  # Phase 2: Lu-Hf
- handler.engine.luhf  # Access Lu-Hf table directly
- handler.analyze(df)  # Peak detection
- handler.clean()  # Data cleaning

【Important Notes】
- εHf(t) is PRE-COMPUTED in the Lu-Hf table (column name: "εHf(t)")
- DO NOT call compute_epsilon_hf() on Lu-Hf-only data (missing Best Age)
- Lu-Hf age column is "U-Pb Age (Ma)" (not "Best Age")
- Free U-Pb memory with gc.collect() before loading Lu-Hf on low-RAM systems

【Memory Strategy】
- Phase 1: query_from_csv() ~0.5 GB (lazy, auto-freed)
- Phase 2: load Lu-Hf only ~0.2 GB (164 MB on disk)
- Total peak: ~0.7 GB (fits in 8 GB machines)

================================================================================

Provenance Analysis: Integrated U-Pb + Lu-Hf
==============================================

Two-phase approach for memory-constrained environments.

Data source: Li et al. (2025) OneDZ Database
"""

import sys, gc
from pathlib import Path

SKILL_DIR = Path.home() / ".claude" / "skills" / "onedz"
sys.path.insert(0, str(SKILL_DIR))

from scripts.onedz_handler import OneDZHandler, OneDZConfig
import polars as pl
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── CONFIG ──────────────────────────────────────────────────────────
REGION = "China"  # country_state value; change to target other regions
ROCK_TYPE = ["detrital"]

# ── HELPERS ─────────────────────────────────────────────────────────
TASK_DIR = Path.cwd()  # Override with specific dir if needed

def out(filename):
    return str(TASK_DIR / filename)


def main():
    print("=" * 70)
    print(f"Provenance Analysis: {REGION} Detrital Zircons")
    print("   U-Pb ages + Lu-Hf εHf(t)")
    print("=" * 70)

    config = OneDZConfig(output_dir=TASK_DIR, use_timestamp_output=False)
    handler = OneDZHandler(config=config)

    # ── Phase 1: U-Pb Age Distribution (lazy, memory-safe) ──────────
    print("\n[Phase 1] U-Pb Age Distribution")
    df_upb = handler.query_from_csv(country_state=REGION, rock_class1=ROCK_TYPE)
    print(f"  Raw: {df_upb.height:,}")

    df_clean = handler.clean(
        df_upb, compute_best_age=True, filter_concordance=True,
        concordance_min=0.90, concordance_max=1.10,
        remove_null_ages=True, age_range=(0, 4500),
    )
    print(f"  Cleaned: {df_clean.height:,}")

    result = handler.analyze(df_clean)
    peaks = result["peaks"]
    summary = result["summary"]
    print(f"  Median: {summary['median']:.0f} Ma, Peaks: {len(peaks)}")

    handler.plot_age(df_clean, mode="kde", show_peaks=True, age_range=(0, 4000),
                     save="provenance_upb_kde.png")

    # Free U-Pb before loading Lu-Hf
    handler.engine._upb_df = None
    gc.collect()

    # ── Phase 2: Lu-Hf Isotope Analysis (direct table) ─────────────
    print(f"\n[Phase 2] Lu-Hf Isotope Analysis")
    handler.load(source="csv", table="global_lu-hf")
    luhf = handler.engine.luhf
    handler.engine._upb_df = None
    gc.collect()

    df_luhf = luhf.filter(pl.col("Country_State") == REGION)
    age_col = "U-Pb Age (Ma)"  # Lu-Hf table age column (NOT "Best Age")

    df_valid = df_luhf.drop_nulls(subset=["εHf(t)", age_col])
    print(f"  {REGION} Lu-Hf: {df_luhf.height:,}, Valid εHf+age: {df_valid.height:,}")

    if df_valid.height < 10:
        print("  Insufficient Lu-Hf data. Provenance from U-Pb only.")
        return

    eps = df_valid["εHf(t)"].cast(pl.Float64).to_numpy()
    ages = df_valid[age_col].cast(pl.Float64).to_numpy()
    mask = np.isfinite(eps) & np.isfinite(ages) & (ages > 0) & (ages < 4500)
    eps, ages = eps[mask], ages[mask]

    n_neg = int(np.sum(eps < 0))
    n_pos = int(np.sum(eps >= 0))
    print(f"  εHf(t): N={len(eps):,}, mean={eps.mean():.1f}")
    print(f"    Ancient (εHf<0): {n_neg/len(eps)*100:.0f}%")
    print(f"    Juvenile (εHf≥0): {n_pos/len(eps)*100:.0f}%")

    # ── Phase 3: Integrated Visualization ───────────────────────────
    print(f"\n[Phase 3] Visualization")

    # εHf vs Age scatter
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.scatter(ages, eps, s=2, alpha=0.25, c=ages, cmap='RdYlBu_r', edgecolors='none')
    ax.axhline(y=0, color='black', linewidth=0.8, label='CHUR')
    ax.fill_between([0, 4500], -40, 0, alpha=0.05, color='blue', label='Ancient crust')
    ax.fill_between([0, 4500], 0, 25, alpha=0.05, color='red', label='Juvenile')
    ax.set_xlabel("U-Pb Age (Ma)", fontsize=12)
    ax.set_ylabel("εHf(t)", fontsize=12)
    ax.set_title(f"Provenance: {REGION} (N={len(eps):,})", fontsize=13)
    ax.set_xlim(0, 4000); ax.set_ylim(-40, 25)
    ax.legend(loc='upper right')
    fig.savefig(out("provenance_eps_vs_age.png"), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  provenance_eps_vs_age.png")

    # εHf distribution
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(eps, bins=60, color='steelblue', edgecolor='white', alpha=0.85)
    ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='CHUR')
    ax.set_xlabel("εHf(t)", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.set_title(f"εHf(t) Distribution — {REGION}", fontsize=13)
    ax.legend()
    fig.savefig(out("provenance_eps_distribution.png"), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  provenance_eps_distribution.png")

    # ── Conclusion ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    if n_neg > n_pos * 1.5:
        print(f"CONCLUSION: Dominant provenance = ANCIENT CRUSTAL RECYCLING ({n_neg/len(eps)*100:.0f}%)")
    elif n_pos > n_neg * 1.5:
        print(f"CONCLUSION: Dominant provenance = JUVENILE MANTLE INPUT ({n_pos/len(eps)*100:.0f}%)")
    else:
        print(f"CONCLUSION: Mixed provenance (Ancient {n_neg/len(eps)*100:.0f}% + Juvenile {n_pos/len(eps)*100:.0f}%)")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
