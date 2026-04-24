"""
OneDZ Handler — 统计与重采样 (Analytics Module)

提供 KDE 分析、多峰识别、Bootstrap / Monte Carlo 重采样、K-S 检验。
"""

from typing import Dict, List, Optional, Tuple

import numpy as np
import polars as pl
from scipy import stats
from scipy.signal import find_peaks

from .config import Cols, OneDZConfig


class Analytics:
    """统计分析和重采样工具。"""

    def __init__(self, config: OneDZConfig) -> None:
        self.config = config

    # ──────────────────── 核密度估计 (KDE) ───────────────────────
    def kde(
        self,
        ages: np.ndarray,
        bandwidth: Optional[float] = None,
        x_range: Optional[Tuple[float, float]] = None,
        n_points: int = 1000,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        自适应带宽 KDE 分析。

        Parameters
        ----------
        ages : np.ndarray
            年龄数组（已清洗的 Best Age）
        bandwidth : float, optional
            带宽，None 表示自适应 (Silverman's rule)
        x_range : tuple, optional
            (x_min, x_max)，默认为数据范围 ±5%
        n_points : int
            评估点数

        Returns
        -------
        x : np.ndarray — 评估点
        y : np.ndarray — 概率密度
        """
        ages = np.asarray(ages, dtype=float)
        ages = ages[~np.isnan(ages)]
        if len(ages) < 2:
            raise ValueError("至少需要 2 个有效年龄数据点")

        if x_range is None:
            margin = (ages.max() - ages.min()) * 0.05
            x_range = (max(0, ages.min() - margin), ages.max() + margin)

        x = np.linspace(x_range[0], x_range[1], n_points)

        if bandwidth is None:
            # Silverman's rule of thumb
            bandwidth = 1.06 * np.std(ages) * len(ages) ** (-1 / 5)
            bandwidth = np.clip(
                bandwidth,
                self.config.kde_min_bandwidth,
                self.config.kde_max_bandwidth,
            )

        kde_obj = stats.gaussian_kde(ages, bw_method=bandwidth / np.std(ages) if np.std(ages) > 0 else 0.1)
        y = kde_obj(x)

        return x, y

    def adaptive_kde(
        self,
        ages: np.ndarray,
        n_points: int = 1000,
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        自适应带宽 KDE（基于 Silverman 准则自动选择最优带宽）。

        Returns
        -------
        x, y, bandwidth
        """
        ages = np.asarray(ages, dtype=float)
        ages = ages[~np.isnan(ages)]

        # Silverman's rule
        bw = 1.06 * np.std(ages) * len(ages) ** (-1 / 5)
        bw = np.clip(bw, self.config.kde_min_bandwidth, self.config.kde_max_bandwidth)

        x, y = self.kde(ages, bandwidth=bw, n_points=n_points)
        return x, y, bw

    # ──────────────────── 多峰自动识别 ───────────────────────────
    @staticmethod
    def find_peaks(
        x: np.ndarray,
        y: np.ndarray,
        prominence: float = 0.01,
        distance: int = 10,
        height: Optional[float] = None,
    ) -> List[Dict]:
        """
        从 KDE 曲线中自动识别峰值。

        Parameters
        ----------
        x, y : np.ndarray
            KDE 曲线
        prominence : float
            峰值突出度阈值
        distance : int
            峰间最小距离（点数）
        height : float, optional
            最小峰高

        Returns
        -------
        list[dict] — 每个 dict 含 peak_age, peak_height, peak_index
        """
        peak_indices, properties = find_peaks(
            y,
            prominence=prominence,
            distance=distance,
            height=height or 0,
        )

        # 无峰时输出诊断信息，帮助使用者判断
        if len(peak_indices) == 0 and len(y) > 0:
            y_max = float(np.max(y))
            print(f"[Analytics] 未检测到峰值 — prominence={prominence}, max(density)={y_max:.6f}")
            print(f"  提示: 当前 prominence 阈值高于 KDE 密度最大值，可能需要调低 prominence 参数")

        peaks = []
        for idx in peak_indices:
            peaks.append({
                "peak_age": float(x[idx]),
                "peak_height": float(y[idx]),
                "peak_index": int(idx),
            })

        # 按峰高降序排列
        peaks.sort(key=lambda p: p["peak_height"], reverse=True)
        return peaks

    # ──────────────────── Bootstrap 重采样 ───────────────────────
    def bootstrap(
        self,
        ages: np.ndarray,
        statistic: str = "kde",
        n_iterations: Optional[int] = None,
        sample_size: Optional[int] = None,
        bandwidth: Optional[float] = None,
        n_points: int = 500,
        confidence: float = 0.95,
    ) -> Dict:
        """
        Bootstrap 重采样估计年龄分布不确定性。

        Parameters
        ----------
        ages : np.ndarray
            原始年龄数据
        statistic : str
            "kde" | "mean" | "median" | "std"
        n_iterations : int
            Bootstrap 次数，默认取 config
        sample_size : int
            每次采样的样本量，默认与原始数据相同
        bandwidth : float
            KDE 带宽
        n_points : int
            KDE 评估点数
        confidence : float
            置信区间水平

        Returns
        -------
        dict — 含 stat_name, observed, ci_lower, ci_upper, n_iter
        """
        ages = np.asarray(ages, dtype=float)
        ages = ages[~np.isnan(ages)]
        n_iter = n_iterations or self.config.n_bootstrap
        n = sample_size or len(ages)

        if statistic == "kde":
            return self._bootstrap_kde(ages, n_iter, n, bandwidth, n_points, confidence)

        # 标量统计量
        stat_funcs = {
            "mean": np.mean,
            "median": np.median,
            "std": np.std,
        }
        func = stat_funcs.get(statistic)
        if func is None:
            raise ValueError(f"不支持的统计量: {statistic}")

        observed = func(ages)
        boot_stats = np.empty(n_iter)
        for i in range(n_iter):
            sample = np.random.choice(ages, size=n, replace=True)
            boot_stats[i] = func(sample)

        alpha = 1 - confidence
        ci_lo = np.percentile(boot_stats, 100 * alpha / 2)
        ci_hi = np.percentile(boot_stats, 100 * (1 - alpha / 2))

        return {
            "stat_name": statistic,
            "observed": float(observed),
            "ci_lower": float(ci_lo),
            "ci_upper": float(ci_hi),
            "n_iter": n_iter,
        }

    def _bootstrap_kde(
        self,
        ages: np.ndarray,
        n_iter: int,
        n: int,
        bandwidth: Optional[float],
        n_points: int,
        confidence: float,
    ) -> Dict:
        """Bootstrap KDE — 返回置信带。"""
        x_range = (max(0, ages.min() * 0.9), ages.max() * 1.1)
        x = np.linspace(x_range[0], x_range[1], n_points)
        all_kdes = np.empty((n_iter, n_points))

        for i in range(n_iter):
            sample = np.random.choice(ages, size=n, replace=True)
            try:
                _, y = self.kde(sample, bandwidth=bandwidth, x_range=x_range, n_points=n_points)
                all_kdes[i] = y
            except (ValueError, np.linalg.LinAlgError):
                all_kdes[i] = 0

        alpha = 1 - confidence
        ci_lo = np.percentile(all_kdes, 100 * alpha / 2, axis=0)
        ci_hi = np.percentile(all_kdes, 100 * (1 - alpha / 2), axis=0)
        _, y_observed = self.kde(ages, bandwidth=bandwidth, x_range=x_range, n_points=n_points)

        return {
            "stat_name": "kde",
            "x": x,
            "y_observed": y_observed,
            "ci_lower": ci_lo,
            "ci_upper": ci_hi,
            "n_iter": n_iter,
        }

    # ──────────────────── Monte Carlo 重采样 ─────────────────────
    def monte_carlo(
        self,
        ages: np.ndarray,
        errors: Optional[np.ndarray] = None,
        n_simulations: Optional[int] = None,
        bandwidth: Optional[float] = None,
        n_points: int = 500,
    ) -> Dict:
        """
        Monte Carlo 重采样：考虑测量误差的年龄分布不确定性。

        每次模拟中，对每个年龄值在其误差范围内随机扰动，然后计算 KDE。

        Parameters
        ----------
        ages : np.ndarray
            年龄数据
        errors : np.ndarray, optional
            1σ 误差，默认取 ages 的标准差的 5%
        n_simulations : int
            模拟次数
        bandwidth : float
            KDE 带宽
        n_points : int

        Returns
        -------
        dict — 含 x, y_mean, y_std, y_lower, y_upper
        """
        ages = np.asarray(ages, dtype=float)
        ages = ages[~np.isnan(ages)]
        n_sim = n_simulations or self.config.n_monte_carlo

        if errors is None:
            errors = np.full_like(ages, np.std(ages) * 0.05)
        else:
            errors = np.asarray(errors, dtype=float)

        x_range = (max(0, ages.min() * 0.9), ages.max() * 1.1)
        x = np.linspace(x_range[0], x_range[1], n_points)
        all_kdes = np.empty((n_sim, n_points))

        for i in range(n_sim):
            perturbed = ages + np.random.normal(0, errors)
            perturbed = perturbed[perturbed > 0]
            if len(perturbed) < 2:
                all_kdes[i] = 0
                continue
            try:
                _, y = self.kde(perturbed, bandwidth=bandwidth, x_range=x_range, n_points=n_points)
                all_kdes[i] = y
            except (ValueError, np.linalg.LinAlgError):
                all_kdes[i] = 0

        y_mean = np.mean(all_kdes, axis=0)
        y_std = np.std(all_kdes, axis=0)

        return {
            "x": x,
            "y_mean": y_mean,
            "y_std": y_std,
            "y_lower": y_mean - 2 * y_std,
            "y_upper": y_mean + 2 * y_std,
            "n_simulations": n_sim,
        }

    # ──────────────────── K-S 检验 ───────────────────────────────
    @staticmethod
    def ks_test(
        ages_a: np.ndarray,
        ages_b: np.ndarray,
        alpha: float = 0.05,
    ) -> Dict:
        """
        两样本 Kolmogorov-Smirnov 检验。

        用于对比不同盆地 / 样品的年龄分布相似度。

        Parameters
        ----------
        ages_a, ages_b : np.ndarray
            两组年龄数据
        alpha : float
            显著性水平

        Returns
        -------
        dict — statistic, p_value, significant, conclusion
        """
        ages_a = np.asarray(ages_a, dtype=float)
        ages_b = np.asarray(ages_b, dtype=float)
        ages_a = ages_a[~np.isnan(ages_a)]
        ages_b = ages_b[~np.isnan(ages_b)]

        statistic, p_value = stats.ks_2samp(ages_a, ages_b)

        return {
            "statistic": float(statistic),
            "p_value": float(p_value),
            "alpha": alpha,
            "significant": p_value < alpha,
            "conclusion": (
                f"K-S 检验: D={statistic:.4f}, p={p_value:.4e}. "
                f"{'拒绝 H0（分布显著不同）' if p_value < alpha else '不能拒绝 H0（分布无显著差异）'}"
            ),
        }

    # ──────────────────── 综合年龄分布分析 ────────────────────────
    def analyze_distribution(
        self,
        df: pl.DataFrame,
        age_col: str = Cols.BEST_AGE,
    ) -> Dict:
        """
        对 DataFrame 中的年龄列执行完整分布分析。

        Returns
        -------
        dict — 统计摘要、KDE、峰值、Bootstrap CI
        """
        if age_col not in df.columns:
            raise ValueError(f"列 '{age_col}' 不存在")

        ages = df[age_col].drop_nulls().to_numpy()

        # 基础统计
        summary = {
            "n": len(ages),
            "mean": float(np.mean(ages)),
            "median": float(np.median(ages)),
            "std": float(np.std(ages)),
            "min": float(np.min(ages)),
            "max": float(np.max(ages)),
            "q25": float(np.percentile(ages, 25)),
            "q75": float(np.percentile(ages, 75)),
        }

        # KDE
        x, y, bw = self.adaptive_kde(ages)

        # 多峰识别
        peaks = self.find_peaks(x, y)

        # Bootstrap mean CI
        boot_mean = self.bootstrap(ages, statistic="mean", n_iterations=500)

        return {
            "summary": summary,
            "kde": {"x": x, "y": y, "bandwidth": bw},
            "peaks": peaks,
            "bootstrap_mean": boot_mean,
        }
