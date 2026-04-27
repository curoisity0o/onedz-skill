"""pytest 测试夹具 — 模拟数据集和 OneDZHandler 配置。"""

import sys
from pathlib import Path

import numpy as np
import polars as pl
import pytest

# 将项目根目录加入 sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.onedz_handler.config import OneDZConfig, Cols


@pytest.fixture
def cfg_tmp_output(tmp_path):
    """返回输出到临时目录的 OneDZConfig。"""
    return OneDZConfig(
        output_dir=tmp_path / "output",
        use_timestamp_output=False,
    )


@pytest.fixture
def upb_young_df():
    """
    <1000 Ma 的模拟 U-Pb 数据，用于测试年龄选择逻辑。
    10 行，所有记录 Best Age 应取 206Pb/238U age。
    """
    np.random.seed(42)
    n = 10
    ages_238 = np.random.uniform(100, 900, n)
    ages_207_206 = np.random.uniform(150, 950, n)
    return pl.DataFrame({
        Cols.AGE_206PB_238U: ages_238,
        Cols.AGE_207PB_206PB: ages_207_206,
        Cols.AGE_207PB_235U: ages_238 * np.random.uniform(0.95, 1.05, n),
    })


@pytest.fixture
def upb_mixed_df():
    """
    混合 <1000 Ma 和 >=1000 Ma 的模拟 U-Pb 数据。
    用于测试分段年龄选择逻辑。
    """
    np.random.seed(42)
    n_young, n_old = 5, 5
    young_238 = np.random.uniform(100, 900, n_young)
    old_238 = np.random.uniform(1000, 3500, n_old)
    old_207_206 = np.random.uniform(1050, 3600, n_old)
    return pl.DataFrame({
        Cols.AGE_206PB_238U: np.concatenate([young_238, old_238]),
        Cols.AGE_207PB_206PB: pl.Series(
            [None] * n_young + old_207_206.tolist(), dtype=pl.Float64
        ),
        Cols.AGE_207PB_235U: np.concatenate([young_238 * 1.02, old_238 * 0.98]),
    })


@pytest.fixture
def upb_with_nulls_df():
    """
    包含空年龄列的模拟数据，用于测试空值处理和 COALESCE 兜底。
    """
    np.random.seed(42)
    return pl.DataFrame({
        Cols.AGE_206PB_238U: [None, 500.0, None],
        Cols.AGE_207PB_206PB: [None, None, 1800.0],
        Cols.AGE_207PB_235U: [None, 520.0, 1750.0],
    })


@pytest.fixture
def random_ages_a():
    """Age group A for KS test — young cluster (~500 Ma)."""
    np.random.seed(42)
    return np.random.normal(500, 50, 200)


@pytest.fixture
def random_ages_b():
    """Age group B for KS test — old cluster (~1500 Ma), should be significantly different."""
    np.random.seed(42)
    return np.random.normal(1500, 50, 200)


@pytest.fixture
def random_ages_same():
    """Age group C for KS test — same distribution as A, should NOT be significantly different."""
    np.random.seed(42)
    return np.random.normal(500, 50, 200)


@pytest.fixture
def luhf_sample_df():
    """Lu-Hf 样本数据，用于 εHf(t) 和 TDM 计算测试。"""
    return pl.DataFrame({
        "176Hf/177Hf": [0.282500, 0.282650, 0.282480, None, 0.283000],
        "176Lu/177Hf": [0.028, 0.030, 0.025, 0.032, None],
        "Best Age": [1000.0, 1200.0, 800.0, 900.0, 1100.0],
    })
