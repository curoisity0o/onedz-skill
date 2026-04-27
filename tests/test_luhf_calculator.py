"""OneDZ Lu-Hf 计算器测试 — εHf(t)、TDM、批量计算。"""

import numpy as np
import polars as pl
import pytest

from scripts.onedz_handler.luhf_calculator import LuHfCalculator


class TestEpsilonHf:
    """εHf(0) 和 εHf(t) 计算测试。"""

    def test_epsilon_hf_0_chur_approx_zero(self):
        """样品值等于 CHUR 时 εHf(0) 应接近 0。"""
        calc = LuHfCalculator()
        result = calc.calculate_epsilon_hf_0(calc.chur_hf_present)
        assert abs(result) < 1e-10

    def test_epsilon_hf_0_negative_for_lower_ratio(self):
        """低于 CHUR 的 176Hf/177Hf 应产生负 εHf(0)。"""
        calc = LuHfCalculator()
        result = calc.calculate_epsilon_hf_0(0.282500)
        assert result < 0
        assert result == pytest.approx(-10.08, abs=0.5)

    def test_epsilon_hf_0_positive_for_higher_ratio(self):
        """高于 CHUR 的 176Hf/177Hf 应产生正 εHf(0)。"""
        calc = LuHfCalculator()
        result = calc.calculate_epsilon_hf_0(0.283500)
        assert result > 0

    def test_epsilon_hf_t_basic(self):
        """εHf(t) 应返回有限数值。"""
        calc = LuHfCalculator()
        result = calc.calculate_epsilon_hf_t(0.282500, 0.028, 1000.0)
        assert np.isfinite(result)

    def test_epsilon_hf_t_array_input(self):
        """数组输入应返回等长数组。"""
        calc = LuHfCalculator()
        n = 5
        hf = np.full(n, 0.282500)
        lu = np.full(n, 0.028)
        ages = np.full(n, 1000.0)
        result = calc.calculate_epsilon_hf_t(hf, lu, ages)
        assert len(result) == n
        assert np.all(np.isfinite(result))

    def test_epsilon_hf_known_values(self):
        """已知数据的 εHf(0) 计算应与公式一致。"""
        calc = LuHfCalculator()
        sample = 0.282500
        expected = 10000 * (sample / calc.chur_hf_present - 1)
        result = calc.calculate_epsilon_hf_0(sample)
        assert result == pytest.approx(expected, abs=1e-10)


class TestTDM:
    """TDM 模型年龄计算测试。"""

    def test_tdm1_positive(self):
        """TDM1 应为正数。"""
        calc = LuHfCalculator()
        result = calc.calculate_tdm(0.282500, 0.028, model="dm1")
        assert result > 0

    def test_tdm2_positive(self):
        """TDM2 应为正数。"""
        calc = LuHfCalculator()
        result = calc.calculate_tdm(0.282500, 0.028, model="dm2")
        assert result > 0

    def test_invalid_model_raises(self):
        """不支持的模型名称应抛出 ValueError。"""
        calc = LuHfCalculator()
        with pytest.raises(ValueError, match="不支持"):
            calc.calculate_tdm(0.282500, 0.028, model="dm3")

    def test_tdm_array_input(self):
        """数组输入应返回等长数组。"""
        calc = LuHfCalculator()
        n = 4
        hf = np.full(n, 0.282500)
        lu = np.full(n, 0.028)
        result = calc.calculate_tdm(hf, lu, model="dm1")
        assert len(result) == n
        assert np.all(result > 0)


class TestComputeBatch:
    """批量计算测试。"""

    def test_columns_added(self, luhf_sample_df):
        """compute_batch 后应存在 εHf(t) 和 TDM1 列。"""
        calc = LuHfCalculator()
        result = calc.compute_batch(luhf_sample_df)
        assert "εHf(t)" in result.columns
        assert "TDM1" in result.columns

    def test_epsilon_hf_column_not_null(self, luhf_sample_df):
        """有效行对应的 εHf(t) 不应为 None。"""
        calc = LuHfCalculator()
        result = calc.compute_batch(luhf_sample_df)
        valid = result["εHf(t)"].to_numpy()
        # 前 3 行数据完整，应为有效值
        assert np.all(np.isfinite(valid[:3]))

    def test_missing_columns_raises(self):
        """缺少必需列时应抛出 ValueError。"""
        calc = LuHfCalculator()
        df = pl.DataFrame({"SomeCol": [1.0, 2.0]})
        with pytest.raises(ValueError, match="缺少必需列"):
            calc.compute_batch(df)

    def test_without_tdm(self, luhf_sample_df):
        """compute_tdm=False 时不应添加 TDM 列。"""
        calc = LuHfCalculator()
        result = calc.compute_batch(luhf_sample_df, compute_tdm=False)
        assert "εHf(t)" in result.columns
        assert "TDM1" not in result.columns


class TestConvenienceFunctions:
    """模块级便捷函数测试。"""

    def test_calculate_epsilon_hf_t_function(self):
        """便捷函数应返回与类方法一致的结果。"""
        from scripts.onedz_handler.luhf_calculator import calculate_epsilon_hf_t as func
        calc = LuHfCalculator()
        result_func = func(0.282500, 0.028, 1000.0)
        result_class = calc.calculate_epsilon_hf_t(0.282500, 0.028, 1000.0)
        assert result_func == pytest.approx(result_class, abs=1e-10)

    def test_calculate_tdm_function(self):
        """便捷函数应返回与类方法一致的结果。"""
        from scripts.onedz_handler.luhf_calculator import calculate_tdm as func
        calc = LuHfCalculator()
        result_func = func(0.282500, 0.028, model="dm1")
        result_class = calc.calculate_tdm(0.282500, 0.028, model="dm1")
        assert result_func == pytest.approx(result_class, abs=1e-10)
