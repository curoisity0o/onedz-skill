"""
OneDZ Handler — 科学级数据清洗 (QC Module)

实现自适应年龄选择、谐和度过滤、误差标准化，符合 Li et al. (2025) 规范。
"""

from typing import Optional, Tuple

import polars as pl
import numpy as np

from .config import Cols, OneDZConfig, AGE_CUTOFF_MA


class QCMODULE:
    """数据质量控制与清洗。"""

    def __init__(self, config: OneDZConfig) -> None:
        self.config = config

    # ──────────────────── 自适应年龄选择 ─────────────────────────
    @staticmethod
    def compute_best_age(df: pl.DataFrame) -> pl.DataFrame:
        """
        计算自适应 Best Age。

        规则 (Li et al., 2025; Best_Age_Add.sql):
        - 206Pb/238U age < 1000 Ma → 使用 206Pb/238U age
        - 206Pb/238U age >= 1000 Ma 且有 207Pb/206Pb age → 使用 207Pb/206Pb age
        - 206Pb/238U age >= 1000 Ma (或NULL) 且有 207Pb/235U age → 使用 207Pb/235U age
        - 兜底: 从 206Pb/238U 同位素比值计算 LOG(1+ratio)/1.55125e-10
        - 最终兜底: COALESCE 三个年龄

        Parameters
        ----------
        df : pl.DataFrame
            原始数据，须含年龄列

        Returns
        -------
        pl.DataFrame — 添加 Best Age 和对应误差列
        """
        age_238 = Cols.AGE_206PB_238U
        age_207_206 = Cols.AGE_207PB_206PB
        age_207_235 = Cols.AGE_207PB_235U
        ratio_238 = Cols.RATIO_206PB_238U

        # 确保列存在
        has_238 = age_238 in df.columns
        has_207_206 = age_207_206 in df.columns
        has_207_235 = age_207_235 in df.columns
        has_ratio = ratio_238 in df.columns

        if not has_238:
            # 如果完全没有年龄列，直接返回
            return df

        # 使用 COALESCE 策略实现分段选择
        # Step 1: 条件 — 238U age < 1000 Ma → 用 238U age
        # Step 2: 条件 — 238U age >= 1000 Ma 且有 207Pb/206Pb → 用 207Pb/206Pb
        # Step 3: 条件 — 238U age >= 1000 Ma 且有 207Pb/235U → 用 207Pb/235U
        # Step 4: fallback

        young_mask = pl.col(age_238) < AGE_CUTOFF_MA

        # 优先级 1: < 1000 Ma 用 206Pb/238U
        best_age = pl.when(young_mask).then(pl.col(age_238))

        # 优先级 2: >= 1000 Ma 用 207Pb/206Pb
        if has_207_206:
            best_age = best_age.when(
                ~young_mask & pl.col(age_207_206).is_not_null()
            ).then(pl.col(age_207_206))

        # 优先级 3: >= 1000 Ma 用 207Pb/235U
        if has_207_235:
            remaining_mask = ~young_mask
            if has_207_206:
                remaining_mask = remaining_mask & pl.col(age_207_206).is_null()
            best_age = best_age.when(
                remaining_mask & pl.col(age_207_235).is_not_null()
            ).then(pl.col(age_207_235))

        # 优先级 4: 从同位素比值计算
        if has_ratio:
            calc_from_ratio = np.log(1 + pl.col(ratio_238)) / 1.55125e-10
            best_age = best_age.when(
                pl.col(age_238).is_null() & pl.col(ratio_238).is_not_null()
            ).then(calc_from_ratio)

        # 最终 fallback: COALESCE
        coalesce_cols = []
        if has_238:
            coalesce_cols.append(pl.col(age_238))
        if has_207_206:
            coalesce_cols.append(pl.col(age_207_206))
        if has_207_235:
            coalesce_cols.append(pl.col(age_207_235))

        if coalesce_cols:
            coalesce_expr = pl.coalesce(coalesce_cols)
            best_age = best_age.otherwise(coalesce_expr)
        else:
            best_age = best_age.otherwise(pl.lit(None))

        # 对应的误差选择
        err_238_1s = Cols.AGE_206PB_238U_1S
        err_207_206_1s = Cols.AGE_207PB_206PB_1S

        if err_238_1s in df.columns:
            best_err = pl.when(young_mask).then(pl.col(err_238_1s))
            if err_207_206_1s in df.columns:
                best_err = best_err.otherwise(pl.col(err_207_206_1s))
            else:
                best_err = best_err.otherwise(pl.lit(None))
        else:
            best_err = pl.lit(None)

        df = df.with_columns([
            best_age.alias(Cols.BEST_AGE),
            best_err.alias(Cols.BEST_AGE_1S),
        ])
        return df

    # ──────────────────── 谐和度计算与过滤 ───────────────────────
    @staticmethod
    def compute_concordance(df: pl.DataFrame) -> pl.DataFrame:
        """
        计算 Discordance (谐和度偏差)。

        Discordance = 1 - (206Pb/238U age / 207Pb/206Pb age)
        或 Discordance = (207Pb/206Pb age - 206Pb/238U age) / 207Pb/206Pb age

        Parameters
        ----------
        df : pl.DataFrame

        Returns
        -------
        pl.DataFrame — 添加 Discord ratio 列
        """
        age_238 = Cols.AGE_206PB_238U
        age_207_206 = Cols.AGE_207PB_206PB

        if age_238 not in df.columns or age_207_206 not in df.columns:
            return df

        discord = 1.0 - (pl.col(age_238) / pl.col(age_207_206))

        df = df.with_columns(discord.alias(Cols.DISCORD_RATIO))
        return df

    def filter_concordance(
        self,
        df: pl.DataFrame,
        concordance_min: Optional[float] = None,
        concordance_max: Optional[float] = None,
    ) -> pl.DataFrame:
        """
        按谐和度范围过滤。

        Concordance = 206Pb/238U age / 207Pb/206Pb age
        典型阈值: 0.90 ~ 1.10 (90% ~ 110%)

        Parameters
        ----------
        df : pl.DataFrame
        concordance_min : float
            下限，默认 0.90
        concordance_max : float
            上限，默认 1.10

        Returns
        -------
        pl.DataFrame
        """
        lo = concordance_min or self.config.concordance_min
        hi = concordance_max or self.config.concordance_max

        age_238 = Cols.AGE_206PB_238U
        age_207_206 = Cols.AGE_207PB_206PB

        if age_238 not in df.columns or age_207_206 not in df.columns:
            print("[QC] 缺少年龄列，无法进行谐和度过滤，跳过")
            return df

        concordance = pl.col(age_238) / pl.col(age_207_206)
        mask = (concordance >= lo) & (concordance <= hi)

        before = df.height
        df = df.filter(mask)
        after = df.height
        print(f"[QC] 谐和度过滤 [{lo:.0%} ~ {hi:.0%}]: {before} → {after} 行 (去除 {before - after})")
        return df

    # ──────────────────── 误差标准化 ─────────────────────────────
    @staticmethod
    def standardize_errors(
        df: pl.DataFrame,
        target_sigma: int = 1,
    ) -> pl.DataFrame:
        """
        将所有误差统一为指定 σ 级别。

        - 若原始为 1σ 且 target=2，乘以 2
        - 若原始为 2σ 且 target=1，除以 2
        - 自动识别列名中包含 "1σ" 或 "2σ" 的误差列

        Parameters
        ----------
        df : pl.DataFrame
        target_sigma : int
            目标 σ 级别 (1 或 2)

        Returns
        -------
        pl.DataFrame
        """
        if target_sigma not in (1, 2):
            raise ValueError("target_sigma 只能是 1 或 2")

        rename_map = {}
        exprs = []

        for col in df.columns:
            if "2σ uncert" in col:
                # 这是一个 2σ 列
                std_col = col.replace("2σ uncert", "1σ uncert")
                if target_sigma == 1:
                    exprs.append((pl.col(col) / 2.0).alias(std_col))
                    rename_map[col] = std_col
            elif "1σ uncert" in col:
                # 这是一个 1σ 列
                std_col = col.replace("1σ uncert", "2σ uncert")
                if target_sigma == 2:
                    exprs.append((pl.col(col) * 2.0).alias(std_col))

        if exprs:
            df = df.with_columns(exprs)
        return df

    # ──────────────────── 综合清洗流水线 ─────────────────────────
    def clean(
        self,
        df: pl.DataFrame,
        *,
        compute_best_age: bool = True,
        filter_concordance: bool = True,
        concordance_min: Optional[float] = None,
        concordance_max: Optional[float] = None,
        standardize_errors: bool = True,
        target_sigma: int = 1,
        remove_null_ages: bool = True,
        age_range: Optional[Tuple[float, float]] = None,
    ) -> pl.DataFrame:
        """
        执行完整数据清洗流水线。

        Parameters
        ----------
        df : pl.DataFrame
            原始数据
        compute_best_age : bool
            是否计算自适应 Best Age
        filter_concordance : bool
            是否进行谐和度过滤
        standardize_errors : bool
            是否标准化误差
        target_sigma : int
            误差标准化目标 (1 或 2)
        remove_null_ages : bool
            是否移除无年龄记录
        age_range : tuple, optional
            限定 Best Age 范围 (min_ma, max_ma)

        Returns
        -------
        pl.DataFrame — 清洗后数据
        """
        n_original = df.height
        print(f"[QC] 开始清洗: {n_original} 条记录")

        # 1. 自适应年龄
        if compute_best_age:
            df = self.compute_best_age(df)

        # 2. 移除无效年龄
        if remove_null_ages and Cols.BEST_AGE in df.columns:
            before = df.height
            df = df.filter(pl.col(Cols.BEST_AGE).is_not_null())
            print(f"[QC] 移除空年龄: {before} → {df.height}")

        # 3. 谐和度过滤
        if filter_concordance:
            df = self.compute_concordance(df)
            df = self.filter_concordance(df, concordance_min, concordance_max)

        # 4. 误差标准化
        if standardize_errors:
            df = self.standardize_errors(df, target_sigma)

        # 5. 年龄范围过滤
        if age_range and Cols.BEST_AGE in df.columns:
            df = df.filter(
                (pl.col(Cols.BEST_AGE) >= age_range[0])
                & (pl.col(Cols.BEST_AGE) <= age_range[1])
            )

        print(f"[QC] 清洗完成: {n_original} → {df.height} 条记录")
        return df
