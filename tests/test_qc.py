"""OneDZ QC 模块测试 — 重点是 Best Age 选择逻辑（科学正确性的核心）。"""

import polars as pl
import pytest

from scripts.onedz_handler.qc import QCMODULE
from scripts.onedz_handler.config import Cols


class TestComputeBestAge:
    """自适应年龄选择逻辑的单元测试。"""

    def test_young_uses_206pb_238u(self, upb_young_df):
        """<1000 Ma 的记录应使用 206Pb/238U age。"""
        result = QCMODULE.compute_best_age(upb_young_df)
        best_ages = result[Cols.BEST_AGE]
        expected = upb_young_df[Cols.AGE_206PB_238U]
        assert best_ages.equals(expected)

    def test_old_uses_207pb_206pb(self, upb_mixed_df):
        """>=1000 Ma 且有 207Pb/206Pb 时应使用后者。"""
        result = QCMODULE.compute_best_age(upb_mixed_df)
        best_ages = result[Cols.BEST_AGE]
        old_best = best_ages[5:]
        old_207_206 = upb_mixed_df[Cols.AGE_207PB_206PB][5:]
        assert old_best.equals(old_207_206)

    def test_nulls_and_coalesce_fallback(self, upb_with_nulls_df):
        """
        空值的兜底逻辑：
        - 第 1 行：全部为空 → Best Age 应为 None
        - 第 2 行：238=500（<1000）→ 用 238 age
        - 第 3 行：238=None, 207/206=1800（>=1000）→ 用 207/206 age
        """
        result = QCMODULE.compute_best_age(upb_with_nulls_df)
        best = result[Cols.BEST_AGE]
        assert best[0] is None, "Row 1 (all nulls) should have None Best Age"
        assert best[1] == 500.0
        assert best[2] == 1800.0

    def test_best_age_column_added(self, upb_young_df):
        """compute_best_age 后应存在 Best Age 和误差列。"""
        result = QCMODULE.compute_best_age(upb_young_df)
        assert Cols.BEST_AGE in result.columns
        assert Cols.BEST_AGE_1S in result.columns

    def test_missing_age_columns_returns_unchanged(self):
        """完全不包含年龄列时，应原样返回。"""
        df = pl.DataFrame({"Other": [1, 2, 3]})
        result = QCMODULE.compute_best_age(df)
        assert result.height == 3
        assert Cols.BEST_AGE not in result.columns


class TestCleanPipeline:
    """完整 QC 清洗管线的集成测试。"""

    def test_clean_removes_null_best_age(self, cfg_tmp_output, upb_mixed_df):
        """remove_null_ages=True 应移除 Best Age 为空的行。"""
        qc = QCMODULE(cfg_tmp_output)
        result = qc.clean(upb_mixed_df, remove_null_ages=True)
        assert Cols.BEST_AGE in result.columns
        assert result[Cols.BEST_AGE].is_null().sum() == 0

    def test_clean_filter_concordance(self, cfg_tmp_output, upb_mixed_df):
        """谐和度过滤不应抛出异常。"""
        qc = QCMODULE(cfg_tmp_output)
        result = qc.clean(upb_mixed_df, filter_concordance=True)
        assert result.height <= upb_mixed_df.height

    def test_clean_without_best_age_no_error(self, cfg_tmp_output):
        """关闭 Best Age 计算时也能正常跑。"""
        df = pl.DataFrame({"col": [1.0]})
        qc = QCMODULE(cfg_tmp_output)
        result = qc.clean(df, compute_best_age=False, filter_concordance=False)
        assert result.height == 1
