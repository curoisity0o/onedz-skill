"""OneDZ Analytics 模块测试 — KDE、峰值检测、K-S 检验。"""

import numpy as np
import pytest

from scripts.onedz_handler.analytics import Analytics


class TestKDE:
    """核密度估计测试。"""

    def test_kde_basic(self, cfg_tmp_output):
        """KDE 应返回 (x, y) 数组，长度等于 n_points。"""
        ages = np.random.exponential(500, 200)
        analytics = Analytics(cfg_tmp_output)
        x, y = analytics.kde(ages, n_points=100)
        assert len(x) == 100
        assert len(y) == 100

    def test_kde_bandwidth_silverman(self, cfg_tmp_output):
        """Silverman 自适应带宽应在 [1, 50] 范围内。"""
        np.random.seed(42)
        ages = np.random.exponential(500, 1000)
        analytics = Analytics(cfg_tmp_output)
        _, y, bw = analytics.adaptive_kde(ages)
        assert 1.0 <= bw <= 50.0
        assert len(y) > 0

    def test_kde_too_few_points_raises(self, cfg_tmp_output):
        """少于 2 个有效数据点时应抛出 ValueError。"""
        analytics = Analytics(cfg_tmp_output)
        with pytest.raises(ValueError, match="至少需要 2 个"):
            analytics.kde(np.array([500.0]))

    def test_kde_nan_filtered(self, cfg_tmp_output):
        """NaN 值应被自动过滤。"""
        analytics = Analytics(cfg_tmp_output)
        ages = np.array([100.0, np.nan, 200.0, np.nan, 300.0])
        x, y = analytics.kde(ages)
        assert len(x) > 0
        assert len(y) > 0


class TestFindPeaks:
    """峰值检测测试。"""

    def test_find_peaks_returns_ordered(self, cfg_tmp_output):
        """峰值应按高度降序排列。"""
        analytics = Analytics(cfg_tmp_output)
        x = np.linspace(0, 1000, 1000)
        y = (
            np.exp(-((x - 200) ** 2) / (2 * 30 ** 2))
            + 0.5 * np.exp(-((x - 700) ** 2) / (2 * 20 ** 2))
        )
        peaks = analytics.find_peaks(x, y, prominence=0.01)
        assert len(peaks) >= 2
        assert peaks[0]["peak_height"] >= peaks[1]["peak_height"]


class TestKSTest:
    """Kolmogorov-Smirnov 检验测试。"""

    def test_significant_difference(self, random_ages_a, random_ages_b):
        """不同分布（~500 vs ~1500）应检出显著差异。"""
        result = Analytics.ks_test(random_ages_a, random_ages_b)
        assert result["significant"] is True
        assert result["p_value"] < 0.05

    def test_no_significant_difference(self, random_ages_a, random_ages_same):
        """相同分布应不显著。"""
        result = Analytics.ks_test(random_ages_a, random_ages_same)
        assert result["significant"] is False
        assert result["p_value"] > 0.05

    def test_ks_result_structure(self, random_ages_a, random_ages_b):
        """返回字典应包含所有必需字段。"""
        result = Analytics.ks_test(random_ages_a, random_ages_b)
        assert "statistic" in result
        assert "p_value" in result
        assert "significant" in result
        assert "conclusion" in result
        assert 0 <= result["statistic"] <= 1

    def test_empty_array_handling(self):
        """空数组应抛出异常。"""
        with pytest.raises(ValueError):
            Analytics.ks_test(np.array([]), np.array([1.0, 2.0]))
