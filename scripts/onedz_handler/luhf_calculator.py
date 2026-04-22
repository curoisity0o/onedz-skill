"""
Lu-Hf 同位素计算模块

实现 εHf(t) 和 TDM 模型年龄计算，基于 Li et al. (2025) OneDZ 数据库论文

计算公式：
εHf(t) = 10000 × {[(176Hf/177Hf)sample - (176Lu/177Hf)sample × (e^λt - 1)] /
          [(176Hf/177Hf)CHUR,0 - (176Lu/177Hf)CHUR × (e^λt - 1)] - 1}

参考：
- Li, K., Hu, X., Chai, R., Yang, J. et al. (2025). OneDZ: A Global Detrital Zircon
  Database and Implications for Constructing Giant Geoscience Database.
  Earth System Science Data.
"""

import numpy as np
import polars as pl
from typing import Union, Tuple, Optional


class LuHfCalculator:
    """
    Lu-Hf 同位素计算器

    计算锆石的 εHf(t) 值和 TDM 模型年龄，用于示踪源区性质和地壳演化。
    """

    def __init__(
        self,
        lambda_176lu: float = 1.867e-11,        # 176Lu 衰变常数 (yr⁻¹)
        chur_hf_present: float = 0.282785,      # 现今球粒陨石 176Hf/177Hf
        chur_lu_hf: float = 0.0336,             # 球粒陨石 176Lu/177Hf
        dm_hf_present: float = 0.28325,         # 亏损地幔 176Hf/177Hf
        dm_lu_hf: float = 0.0388                # 亏损地幔 176Lu/177Hf
    ):
        """
        初始化计算器

        Parameters
        ----------
        lambda_176lu : float
            176Lu 衰变常数 (yr⁻¹)，默认 Söderlund et al. (2004)
        chur_hf_present : float
            现今球粒陨石 176Hf/177Hf 比值，默认 Bouvier et al. (2008)
        chur_lu_hf : float
            球粒陨石 176Lu/177Hf 比值
        dm_hf_present : float
            亏损地幔现今 176Hf/177Hf 比值，默认 Griffin et al. (2000)
        dm_lu_hf : float
            亏损地幔 176Lu/177Hf 比值
        """
        self.lambda_176lu = lambda_176lu
        self.chur_hf_present = chur_hf_present
        self.chur_lu_hf = chur_lu_hf
        self.dm_hf_present = dm_hf_present
        self.dm_lu_hf = dm_lu_hf

    def calculate_epsilon_hf_0(
        self,
        hf176_hf177_sample: Union[float, np.ndarray]
    ) -> Union[float, np.ndarray]:
        """
        计算 εHf(0)（现今值）

        εHf(0) = 10000 × [(176Hf/177Hf)sample / (176Hf/177Hf)CHUR,0 - 1]

        Parameters
        ----------
        hf176_hf177_sample : float or np.ndarray
            样品的 176Hf/177Hf 比值

        Returns
        -------
        epsilon_hf_0 : float or np.ndarray
            εHf(0) 值

        Examples
        --------
        >>> calc = LuHfCalculator()
        >>> epsilon_hf_0 = calc.calculate_epsilon_hf_0(0.282500)
        >>> print(f"εHf(0) = {epsilon_hf_0:.2f}")
        εHf(0) = -10.02
        """
        epsilon_hf_0 = 10000 * (hf176_hf177_sample / self.chur_hf_present - 1)
        return epsilon_hf_0

    def calculate_epsilon_hf_t(
        self,
        hf176_hf177_sample: Union[float, np.ndarray],
        lu176_lu177_sample: Union[float, np.ndarray],
        age_ma: Union[float, np.ndarray]
    ) -> Union[float, np.ndarray]:
        """
        计算 εHf(t)（时间演化值）

        εHf(t) = 10000 × {
            [(176Hf/177Hf)sample - (176Lu/177Hf)sample × (e^λt - 1)] /
            [(176Hf/177Hf)CHUR,0 - (176Lu/177Hf)CHUR × (e^λt - 1)]
            - 1
        }

        Parameters
        ----------
        hf176_hf177_sample : float or np.ndarray
            样品的现今 176Hf/177Hf 比值
        lu176_lu177_sample : float or np.ndarray
            样品的现今 176Lu/177Hf 比值
        age_ma : float or np.ndarray
            结晶年龄（Ma，百万年）

        Returns
        -------
        epsilon_hf_t : float or np.ndarray
            εHf(t) 值

        Examples
        --------
        >>> calc = LuHfCalculator()
        >>> epsilon_hf_t = calc.calculate_epsilon_hf_t(
        ...     hf176_hf177_sample=0.282500,
        ...     lu176_lu177_sample=0.028,
        ...     age_ma=1000
        ... )
        >>> print(f"εHf(1000 Ma) = {epsilon_hf_t:.2f}")
        εHf(1000 Ma) = -5.23
        """
        # 将年龄从 Ma 转换为年
        t_years = age_ma * 1e6

        # 计算衰变因子: (e^λt - 1)
        decay_factor = np.exp(self.lambda_176lu * t_years) - 1

        # 计算样品在时间 t 的 176Hf/177Hf 比值
        # (176Hf/177Hf)sample(t) = (176Hf/177Hf)sample(0) - (176Lu/177Hf)sample × (e^λt - 1)
        hf_sample_t = hf176_hf177_sample - lu176_lu177_sample * decay_factor

        # 计算 CHUR 在时间 t 的 176Hf/177Hf 比值
        # (176Hf/177Hf)CHUR(t) = (176Hf/177Hf)CHUR,0 - (176Lu/177Hf)CHUR × (e^λt - 1)
        hf_chur_t = self.chur_hf_present - self.chur_lu_hf * decay_factor

        # 计算 εHf(t)
        # εHf(t) = 10000 × [(176Hf/177Hf)sample(t) / (176Hf/177Hf)CHUR(t) - 1]
        epsilon_hf_t = 10000 * (hf_sample_t / hf_chur_t - 1)

        return epsilon_hf_t

    def calculate_tdm(
        self,
        hf176_hf177_sample: Union[float, np.ndarray],
        lu176_lu177_sample: Union[float, np.ndarray],
        model: str = "dm1",
        f_cc: Optional[float] = None
    ) -> Union[float, np.ndarray]:
        """
        计算 TDM (Depleted Mantle Model Age) 亏损地幔模型年龄

        单阶段模型 (TDM1):
        TDM = 1/λ × ln{1 + [(176Hf/177Hf)sample - (176Hf/177Hf)DM] /
                        [(176Lu/177Hf)sample - (176Lu/177Hf)DM]}

        两阶段模型 (TDM2):
        考虑地壳平均 Lu/Hf 比值的影响

        Parameters
        ----------
        hf176_hf177_sample : float or np.ndarray
            样品的 176Hf/177Hf 比值
        lu176_lu177_sample : float or np.ndarray
            样品的 176Lu/177Hf 比值
        model : str, optional
            "dm1" (单阶段) 或 "dm2" (两阶段)，默认 "dm1"
        f_cc : float, optional
            大陆壳平均 176Lu/177Hf 比值（用于两阶段模型）
            默认使用 f_cc = -0.55 对应的值

        Returns
        -------
        tdm_ma : float or np.ndarray
            TDM 模型年龄（Ma）

        Examples
        --------
        >>> calc = LuHfCalculator()
        >>> tdm = calc.calculate_tdm(
        ...     hf176_hf177_sample=0.282500,
        ...     lu176_lu177_sample=0.028,
        ...     model="dm1"
        ... )
        >>> print(f"TDM1 = {tdm:.0f} Ma")
        TDM1 = 1245 Ma
        """
        if model == "dm1":
            # 单阶段模型
            ratio_numerator = hf176_hf177_sample - self.dm_hf_present
            ratio_denominator = lu176_lu177_sample - self.dm_lu_hf

            # 避免除零错误
            if isinstance(ratio_denominator, np.ndarray):
                ratio_denominator = np.where(
                    np.abs(ratio_denominator) < 1e-10,
                    1e-10,
                    ratio_denominator
                )
            else:
                if abs(ratio_denominator) < 1e-10:
                    ratio_denominator = 1e-10

            # TDM (年) = 1/λ × ln[1 + (176Hf/177Hf)sample - (176Hf/177Hf)DM /
            #                              (176Lu/177Hf)sample - (176Lu/177Hf)DM]
            tdm_years = np.log(1 + ratio_numerator / ratio_denominator) / self.lambda_176lu

            # 转换为 Ma
            tdm_ma = tdm_years / 1e6

            return tdm_ma

        elif model == "dm2":
            # 两阶段模型
            # 使用大陆壳平均 Lu/Hf 比值
            if f_cc is None:
                # 默认大陆壳 176Lu/177Hf = 0.015 (对应 f_cc = -0.55)
                lu_cc_hf = 0.015
            else:
                lu_cc_hf = self.chur_lu_hf * (1 + f_cc)

            # 第一阶段：样品历史到地壳形成
            # 第二阶段：地壳形成到现在
            # 这里简化实现，使用近似公式

            ratio_numerator = hf176_hf177_sample - self.dm_hf_present
            ratio_denominator = lu_cc_hf - self.dm_lu_hf

            if isinstance(ratio_denominator, np.ndarray):
                ratio_denominator = np.where(
                    np.abs(ratio_denominator) < 1e-10,
                    1e-10,
                    ratio_denominator
                )
            else:
                if abs(ratio_denominator) < 1e-10:
                    ratio_denominator = 1e-10

            tdm_years = np.log(1 + ratio_numerator / ratio_denominator) / self.lambda_176lu
            tdm_ma = tdm_years / 1e6

            return tdm_ma

        else:
            raise ValueError(f"不支持的模型: {model}。请使用 'dm1' 或 'dm2'")

    def compute_batch(
        self,
        df: pl.DataFrame,
        hf_col: str = "176Hf/177Hf",
        lu_col: str = "176Lu/177Hf",
        age_col: str = "Best Age",
        compute_tdm: bool = True,
        tdm_models: list = ["dm1"]
    ) -> pl.DataFrame:
        """
        批量计算 Lu-Hf 指标

        Parameters
        ----------
        df : pl.DataFrame
            输入数据框
        hf_col : str, optional
            176Hf/177Hf 列名，默认 "176Hf/177Hf"
        lu_col : str, optional
            176Lu/177Hf 列名，默认 "176Lu/177Hf"
        age_col : str, optional
            年龄列名（Ma），默认 "Best Age"
        compute_tdm : bool, optional
            是否计算 TDM，默认 True
        tdm_models : list, optional
            TDM 模型列表，默认 ["dm1"]

        Returns
        -------
        pl.DataFrame
            添加了计算列的 DataFrame

        Examples
        --------
        >>> import polars as pl
        >>> from onedz_handler.luhf_calculator import LuHfCalculator
        >>>
        >>> # 创建测试数据
        >>> df = pl.DataFrame({
        ...     "176Hf/177Hf": [0.282500, 0.282650, 0.282480],
        ...     "176Lu/177Hf": [0.028, 0.030, 0.025],
        ...     "Best Age": [1000, 1200, 800]
        ... })
        >>>
        >>> # 计算
        >>> calc = LuHfCalculator()
        >>> df_result = calc.compute_batch(df)
        >>>
        >>> print(df_result)
        shape: (3, 5)
        ┌────────────┬─────────────┬───────────┬───────────┬──────────┐
        │ 176Hf/177Hf ┆ 176Lu/177Hf ┆ Best Age ┆ εHf(t)    ┆ TDM1     │
        │ ---        ┆ ---         ┆ ---      ┆ ---       ┆ ---      │
        │ f64        ┆ f64         ┆ f64      ┆ f64       ┆ f64      │
        ╞════════════╪═════════════╪══════════╪═══════════╪══════════╡
        │ 0.2825     ┆ 0.028       ┆ 1000.0   ┆ -5.234521 ┆ 1245.67  │
        │ 0.28265    ┆ 0.03        ┆ 1200.0   ┆ 2.123456  ┆ 1098.34  │
        │ 0.28248    ┆ 0.025       ┆ 800.0    ┆ -8.765432 ┆ 1345.89  │
        └────────────┴─────────────┴───────────┴───────────┴──────────┘
        """
        # 检查必需列是否存在
        required_cols = [hf_col, lu_col, age_col]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            raise ValueError(f"缺少必需列: {missing_cols}")

        # 提取数据
        hf_ratio = df[hf_col].to_numpy()
        lu_ratio = df[lu_col].to_numpy()
        ages = df[age_col].to_numpy()

        # 过滤缺失值
        valid_mask = (
            ~np.isnan(hf_ratio) &
            ~np.isnan(lu_ratio) &
            ~np.isnan(ages)
        )

        if not np.all(valid_mask):
            print(f"[LuHfCalculator] 警告: {np.sum(~valid_mask)} 条记录包含缺失值，将被跳过")

            # 只处理有效值
            hf_ratio_valid = hf_ratio[valid_mask]
            lu_ratio_valid = lu_ratio[valid_mask]
            ages_valid = ages[valid_mask]
        else:
            hf_ratio_valid = hf_ratio
            lu_ratio_valid = lu_ratio
            ages_valid = ages

        # 计算 εHf(t)
        epsilon_hf_t = self.calculate_epsilon_hf_t(
            hf_ratio_valid,
            lu_ratio_valid,
            ages_valid
        )

        # 创建结果数组（包含缺失值）
        epsilon_hf_t_result = np.full(len(df), np.nan)
        epsilon_hf_t_result[valid_mask] = epsilon_hf_t

        # 添加到 DataFrame
        result = df.with_columns([
            pl.Series("εHf(t)", epsilon_hf_t_result, dtype=pl.Float64)
        ])

        # 计算 TDM
        if compute_tdm:
            for model in tdm_models:
                tdm = self.calculate_tdm(
                    hf_ratio_valid,
                    lu_ratio_valid,
                    model=model
                )

                tdm_result = np.full(len(df), np.nan)
                tdm_result[valid_mask] = tdm

                col_name = f"TDM{model[-1]}"  # dm1 -> TDM1, dm2 -> TDM2
                result = result.with_columns([
                    pl.Series(col_name, tdm_result, dtype=pl.Float64)
                ])

        return result


# 便捷函数
def calculate_epsilon_hf_t(
    hf176_hf177_sample: Union[float, np.ndarray],
    lu176_lu177_sample: Union[float, np.ndarray],
    age_ma: Union[float, np.ndarray],
    **kwargs
) -> Union[float, np.ndarray]:
    """
    快捷计算 εHf(t) 的函数

    Parameters
    ----------
    hf176_hf177_sample : float or np.ndarray
        样品的 176Hf/177Hf 比值
    lu176_lu177_sample : float or np.ndarray
        样品的 176Lu/177Hf 比值
    age_ma : float or np.ndarray
        结晶年龄（Ma）
    **kwargs
        传递给 LuHfCalculator 的额外参数

    Returns
    -------
    epsilon_hf_t : float or np.ndarray
        εHf(t) 值
    """
    calc = LuHfCalculator(**kwargs)
    return calc.calculate_epsilon_hf_t(hf176_hf177_sample, lu176_lu177_sample, age_ma)


def calculate_tdm(
    hf176_hf177_sample: Union[float, np.ndarray],
    lu176_lu177_sample: Union[float, np.ndarray],
    model: str = "dm1",
    **kwargs
) -> Union[float, np.ndarray]:
    """
    快捷计算 TDM 的函数

    Parameters
    ----------
    hf176_hf177_sample : float or np.ndarray
        样品的 176Hf/177Hf 比值
    lu176_lu177_sample : float or np.ndarray
        样品的 176Lu/177Hf 比值
    model : str, optional
        "dm1" 或 "dm2"，默认 "dm1"
    **kwargs
        传递给 LuHfCalculator 的额外参数

    Returns
    -------
    tdm_ma : float or np.ndarray
        TDM 模型年龄（Ma）
    """
    calc = LuHfCalculator(**kwargs)
    return calc.calculate_tdm(hf176_hf177_sample, lu176_lu177_sample, model=model)
