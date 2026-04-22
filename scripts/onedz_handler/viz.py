"""
OneDZ Handler — 演化建模与可视化 (Viz Module)

绘制锆石年龄频率分布图 (PDP/KDE)、εHf(t) 演化散图、TDM 模型年龄分布。
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path

import numpy as np
import polars as pl
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.integrate import trapezoid

# 配置中文字体支持
def _setup_chinese_font():
    """配置matplotlib以支持中文显示"""
    try:
        # 尝试使用系统常见的中文字体
        chinese_fonts = [
            'WenQuanYi Micro Hei',     # 文泉驿微米黑
            'WenQuanYi Zen Hei',        # 文泉驿正黑
            'SimHei',                   # 黑体
            'Microsoft YaHei',          # 微软雅黑
            'PingFang SC',              # 苹方
            'STHeiti',                  # 华文黑体
        ]

        for font in chinese_fonts:
            try:
                matplotlib.rcParams['font.sans-serif'] = [font] + matplotlib.rcParams['font.sans-serif']
                # 测试字体是否可用
                plt.figure()
                plt.text(0.5, 0.5, '测试', fontsize=12)
                plt.close()
                print(f"[Viz] 已配置中文字体: {font}")
                return
            except:
                continue

        # 如果所有字体都失败，使用兜底方案
        matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans'] + matplotlib.rcParams['font.sans-serif']
        print("[Viz] 警告: 未找到可用的中文字体，将使用默认字体")

        # 解决负号显示问题
        matplotlib.rcParams['axes.unicode_minus'] = False
    except Exception as e:
        print(f"[Viz] 字体配置警告: {e}")

# 在导入时立即配置
_setup_chinese_font()

from .config import (
    Cols,
    OneDZConfig,
    LAMBDA_176LU,
    CHUR_176HF_177HF_PRESENT,
    CHUR_176LU_177HF_PRESENT,
    DM_176HF_177HF_PRESENT,
    DM_176LU_177HF_PRESENT,
    LUC_176HF_177HF,
)
from .analytics import Analytics


class Viz:
    """地质数据可视化。"""

    def __init__(self, config: OneDZConfig) -> None:
        self.config = config
        self.analytics = Analytics(config)

    def _setup_axes(self, ax: plt.Axes, title: str = "", xlabel: str = "", ylabel: str = "") -> None:
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)

    # ──────────────────── PDP / KDE 年龄分布图 ───────────────────
    def plot_age_distribution(
        self,
        df: pl.DataFrame,
        age_col: str = Cols.BEST_AGE,
        mode: str = "kde",
        bandwidth: Optional[float] = None,
        age_range: Tuple[float, float] = (0, 4000),
        normalize: bool = True,
        show_peaks: bool = True,
        n_peaks: int = 5,
        color: str = "#2196F3",
        alpha: float = 0.6,
        ax: Optional[plt.Axes] = None,
        figsize: Tuple[float, float] = (10, 5),
    ) -> plt.Figure:
        """
        绘制锆石年龄频率分布图 (KDE 或 PDP)。

        Parameters
        ----------
        df : pl.DataFrame
        age_col : str
            年龄列名
        mode : str
            "kde" | "pdp" (Probability Density Plot)
        bandwidth : float
            KDE 带宽
        age_range : tuple
            显示年龄范围
        normalize : bool
            是否归一化为相对频率
        show_peaks : bool
            是否标注峰值
        n_peaks : int
            显示前 N 个峰
        color : str
            填充色
        alpha : float
            透明度
        ax : plt.Axes, optional
            外部传入的 Axes
        figsize : tuple

        Returns
        -------
        plt.Figure
        """
        if age_col not in df.columns:
            raise ValueError(f"列 '{age_col}' 不在数据中")

        ages = df[age_col].drop_nulls().to_numpy()
        ages = ages[(ages >= age_range[0]) & (ages <= age_range[1])]

        if ax is None:
            fig, ax = plt.subplots(figsize=figsize, dpi=self.config.figure_dpi)
        else:
            fig = ax.get_figure()

        if mode == "kde":
            x, y = self.analytics.kde(ages, bandwidth=bandwidth, x_range=age_range, n_points=2000)
            if normalize:
                y = y / trapezoid(y, x) if trapezoid(y, x) > 0 else y
        elif mode == "pdp":
            # PDP: 每个数据点的高斯叠加
            bw = bandwidth or (1.06 * np.std(ages) * len(ages) ** (-1 / 5))
            x = np.linspace(age_range[0], age_range[1], 2000)
            y = np.zeros_like(x)
            for age in ages:
                y += stats_norm_pdf(x, age, bw)
            if normalize:
                y = y / trapezoid(y, x) if trapezoid(y, x) > 0 else y
        else:
            raise ValueError(f"不支持的模式: {mode}。请使用 'kde' 或 'pdp'")

        ax.fill_between(x, y, alpha=alpha, color=color, label=f"{mode.upper()} (n={len(ages)})")
        ax.plot(x, y, color=color, linewidth=1.0)

        # 标注峰值
        if show_peaks:
            peaks = self.analytics.find_peaks(x, y)
            for p in peaks[:n_peaks]:
                ax.annotate(
                    f"{p['peak_age']:.0f} Ma",
                    xy=(p["peak_age"], p["peak_height"]),
                    xytext=(0, 10),
                    textcoords="offset points",
                    fontsize=8,
                    ha="center",
                    color="red",
                    arrowprops=dict(arrowstyle="->", color="red", lw=0.8),
                )

        self._setup_axes(
            ax,
            title=f"Detrital Zircon Age Distribution ({mode.upper()})",
            xlabel="Age (Ma)",
            ylabel="Relative Probability" if normalize else "Density",
        )
        ax.set_xlim(age_range)
        ax.legend(fontsize=9)
        fig.tight_layout()
        return fig

    # ──────────────────── 多样品叠加对比图 ───────────────────────
    def plot_multi_kde(
        self,
        data_dict: Dict[str, np.ndarray],
        bandwidth: Optional[float] = None,
        age_range: Tuple[float, float] = (0, 4000),
        figsize: Tuple[float, float] = (12, 6),
    ) -> plt.Figure:
        """
        多样品 KDE 叠加对比图。

        Parameters
        ----------
        data_dict : dict
            {样品名: 年龄数组}
        bandwidth : float
        age_range : tuple
        figsize : tuple

        Returns
        -------
        plt.Figure
        """
        fig, ax = plt.subplots(figsize=figsize, dpi=self.config.figure_dpi)
        colors = plt.cm.Set2(np.linspace(0, 1, len(data_dict)))

        for (name, ages), color in zip(data_dict.items(), colors):
            ages = np.asarray(ages, dtype=float)
            ages = ages[~np.isnan(ages)]
            ages = ages[(ages >= age_range[0]) & (ages <= age_range[1])]
            if len(ages) < 2:
                continue

            x, y = self.analytics.kde(ages, bandwidth=bandwidth, x_range=age_range)
            y_norm = y / trapezoid(y, x) if trapezoid(y, x) > 0 else y
            ax.plot(x, y_norm, label=f"{name} (n={len(ages)})", color=color, linewidth=1.5)

        self._setup_axes(ax, "Multi-Sample KDE Comparison", "Age (Ma)", "Relative Probability")
        ax.set_xlim(age_range)
        ax.legend(fontsize=9)
        fig.tight_layout()
        return fig

    # ──────────────────── εHf(t) 演化散图 ───────────────────────
    def plot_epsilon_hf(
        self,
        df: pl.DataFrame,
        age_col: str = Cols.BEST_AGE,
        epsilon_hf_col: str = "εHf(t)",
        show_chur: bool = True,
        show_dm: bool = True,
        age_range: Tuple[float, float] = (0, 4000),
        hf_range: Tuple[float, float] = (-40, 20),
        color_by: Optional[str] = None,
        ax: Optional[plt.Axes] = None,
        figsize: Tuple[float, float] = (10, 8),
    ) -> plt.Figure:
        """
        绘制 εHf(t) 演化散图，叠加 CHUR 和 DM 参考线。

        Parameters
        ----------
        df : pl.DataFrame
            须含年龄列和 epsilon_Hf 列
        age_col, epsilon_hf_col : str
        show_chur, show_dm : bool
            是否绘制 CHUR / DM 参考线
        age_range, hf_range : tuple
        color_by : str, optional
            按某列着色（如 "Class-1 Rock Type"）
        ax : plt.Axes
        figsize : tuple

        Returns
        -------
        plt.Figure
        """
        if age_col not in df.columns or epsilon_hf_col not in df.columns:
            raise ValueError(f"数据中缺少 '{age_col}' 或 '{epsilon_hf_col}' 列")

        valid = df.filter(
            pl.col(age_col).is_not_null() & pl.col(epsilon_hf_col).is_not_null()
            & (pl.col(age_col) >= age_range[0]) & (pl.col(age_col) <= age_range[1])
        )
        ages = valid[age_col].to_numpy()
        ehf = valid[epsilon_hf_col].to_numpy()

        if ax is None:
            fig, ax = plt.subplots(figsize=figsize, dpi=self.config.figure_dpi)
        else:
            fig = ax.get_figure()

        # 散点
        if color_by and color_by in valid.columns:
            categories = valid[color_by].unique().to_list()
            cat_colors = plt.cm.tab10(np.linspace(0, 1, len(categories)))
            for cat, c in zip(categories, cat_colors):
                sub = valid.filter(pl.col(color_by) == cat)
                ax.scatter(
                    sub[age_col].to_numpy(),
                    sub[epsilon_hf_col].to_numpy(),
                    s=8, alpha=0.5, color=c, label=str(cat),
                )
        else:
            ax.scatter(ages, ehf, s=8, alpha=0.5, color="#1565C0", edgecolors="none")

        # CHUR 参考线 (εHf = 0 对所有年龄)
        t_line = np.linspace(age_range[0], age_range[1], 500)
        if show_chur:
            chur_ehf = self._reference_line(t_line, "chur")
            ax.plot(t_line, chur_ehf, "g--", linewidth=1.5, label="CHUR")

        # DM 参考线
        if show_dm:
            dm_ehf = self._reference_line(t_line, "dm")
            ax.plot(t_line, dm_ehf, "r--", linewidth=1.5, label="Depleted Mantle")

        self._setup_axes(ax, "εHf(t) vs. Age", "Age (Ma)", "εHf(t)")
        ax.set_xlim(age_range)
        ax.set_ylim(hf_range)
        ax.axhline(y=0, color="gray", linewidth=0.5, linestyle="-")
        ax.legend(fontsize=9)
        fig.tight_layout()
        return fig

    @staticmethod
    def _reference_line(ages_ma: np.ndarray, source: str) -> np.ndarray:
        """
        计算 CHUR 或 DM 的 εHf(t) 参考线。

        εHf(t) = [(176Hf/177Hf)_sample(t) / (176Hf/177Hf)_CHUR(t) - 1] * 10000
        """
        t_yr = ages_ma * 1e6  # Ma → yr

        if source == "chur":
            hf_present = CHUR_176HF_177HF_PRESENT
            lu_hf = CHUR_176LU_177HF_PRESENT
            ref_hf = CHUR_176HF_177HF_PRESENT
            ref_lu = CHUR_176LU_177HF_PRESENT
        elif source == "dm":
            hf_present = DM_176HF_177HF_PRESENT
            lu_hf = DM_176LU_177HF_PRESENT
            ref_hf = CHUR_176HF_177HF_PRESENT
            ref_lu = CHUR_176LU_177HF_PRESENT
        else:
            raise ValueError(f"Unknown source: {source}")

        # 过去时刻的比值
        hf_t = hf_present - lu_hf * LAMBDA_176LU * t_yr
        ref_hf_t = ref_hf - ref_lu * LAMBDA_176LU * t_yr

        epsilon_hf = ((hf_t / ref_hf_t) - 1) * 10000
        return epsilon_hf

    # ──────────────────── TDM 模型年龄计算与分布 ─────────────────
    @staticmethod
    def compute_tdm(
        epsilon_hf: np.ndarray,
        crystallization_age_ma: np.ndarray,
        model: str = "dm1",
        f_cc: float = -0.55,
    ) -> np.ndarray:
        """
        计算 TDM (Depleted Mantle Model Age)。

        Parameters
        ----------
        epsilon_hf : np.ndarray
            εHf(t) 值
        crystallization_age_ma : np.ndarray
            结晶年龄 (Ma)
        model : str
            "dm1" (单阶段) 或 "dm2" (两阶段)
        f_cc : float
            大陆地壳 f_Lu/Hf，默认 -0.55 (Griffin et al., 2002)

        Returns
        -------
        np.ndarray — TDM 年龄 (Ma)
        """
        t_cryst = crystallization_age_ma * 1e6  # yr

        # εHf(t) → 176Hf/177Hf(t)
        hf_chur_t = CHUR_176HF_177HF_PRESENT - CHUR_176LU_177HF_PRESENT * LAMBDA_176LU * t_cryst
        hf_sample_t = hf_chur_t * (1 + epsilon_hf / 10000)

        if model == "dm1":
            # 单阶段 TDM
            hf_dm_0 = DM_176HF_177HF_PRESENT
            lu_hf_dm = DM_176LU_177HF_PRESENT
            f_sample = (hf_sample_t / hf_chur_t - 1)
            tdm_yr = (
                (hf_dm_0 - hf_sample_t)
                / (LAMBDA_176LU * (lu_hf_dm - f_sample * CHUR_176LU_177HF_PRESENT))
            )
        elif model == "dm2":
            # 两阶段 TDM (假设从 DM 提取后进入大陆壳)
            hf_dm_0 = DM_176HF_177HF_PRESENT
            lu_hf_cc = LUC_176HF_177HF  # 大陆壳 176Lu/177Hf
            # TDM2 = TDM1 - f_cc adjustment
            f_sample = f_cc
            tdm1_yr = (
                (hf_dm_0 - hf_sample_t)
                / (LAMBDA_176LU * (DM_176LU_177HF_PRESENT - f_sample * CHUR_176LU_177HF_PRESENT))
            )
            # 两阶段校正
            tdm_yr = t_cryst + (tdm1_yr - t_cryst) * (
                (DM_176LU_177HF_PRESENT - CHUR_176LU_177HF_PRESENT)
                / (CHUR_176LU_177HF_PRESENT * f_cc - CHUR_176LU_177HF_PRESENT + DM_176LU_177HF_PRESENT)
            )
        else:
            raise ValueError(f"不支持的 model: {model}")

        tdm_ma = tdm_yr / 1e6
        tdm_ma = np.where(tdm_ma > 0, tdm_ma, np.nan)
        return tdm_ma

    def plot_tdm_distribution(
        self,
        df: pl.DataFrame,
        epsilon_hf_col: str = "εHf(t)",
        age_col: str = Cols.BEST_AGE,
        model: str = "dm2",
        age_range: Tuple[float, float] = (0, 4000),
        bandwidth: Optional[float] = None,
        figsize: Tuple[float, float] = (10, 5),
    ) -> plt.Figure:
        """
        绘制 TDM 模型年龄分布图。

        Parameters
        ----------
        df : pl.DataFrame
        epsilon_hf_col : str
        age_col : str
        model : str
            "dm1" 或 "dm2"
        age_range : tuple
        bandwidth : float
        figsize : tuple

        Returns
        -------
        plt.Figure
        """
        if epsilon_hf_col not in df.columns or age_col not in df.columns:
            raise ValueError(f"数据中缺少 '{epsilon_hf_col}' 或 '{age_col}' 列")

        valid = df.filter(
            pl.col(epsilon_hf_col).is_not_null() & pl.col(age_col).is_not_null()
        )
        ehf = valid[epsilon_hf_col].to_numpy()
        ages = valid[age_col].to_numpy()

        tdm = self.compute_tdm(ehf, ages, model=model)
        tdm = tdm[~np.isnan(tdm)]
        tdm = tdm[(tdm >= age_range[0]) & (tdm <= age_range[1])]

        fig, ax = plt.subplots(figsize=figsize, dpi=self.config.figure_dpi)

        if len(tdm) > 2:
            x, y = self.analytics.kde(tdm, bandwidth=bandwidth, x_range=age_range)
            ax.fill_between(x, y, alpha=0.6, color="#FF9800")
            ax.plot(x, y, color="#E65100", linewidth=1.0)

            peaks = self.analytics.find_peaks(x, y)
            for p in peaks[:3]:
                ax.annotate(
                    f"{p['peak_age']:.0f} Ma",
                    xy=(p["peak_age"], p["peak_height"]),
                    xytext=(0, 10),
                    textcoords="offset points",
                    fontsize=8, ha="center", color="red",
                )

        self._setup_axes(
            ax,
            title=f"TDM{model[-1]} Model Age Distribution (n={len(tdm)})",
            xlabel="TDM Age (Ma)",
            ylabel="Density",
        )
        ax.set_xlim(age_range)
        fig.tight_layout()
        return fig


    # ──────────────────── εHf(t) 可视化 ─────────────────────────────
    def plot_epsilon_hf_vs_age(
        self,
        df: pl.DataFrame,
        age_col: str = Cols.BEST_AGE,
        epsilon_col: str = "εHf(t)",
        age_range: Tuple[float, float] = (0, 4000),
        epsilon_range: Tuple[float, float] = (-30, 20),
        show_chur: bool = True,
        show_dm: bool = True,
        color_by: Optional[str] = None,
        figsize: Tuple[float, float] = (12, 8),
        save: Optional[str] = None
    ) -> plt.Figure:
        """
        绘制 εHf(t) vs Age 散点图

        展示锆石样品的 Hf 同位素演化特征，用于源区判别和地壳演化研究。

        Parameters
        ----------
        df : pl.DataFrame
            输入数据，必须包含年龄和 εHf(t) 列
        age_col : str, optional
            年龄列名，默认 "Best Age"
        epsilon_col : str, optional
            εHf(t) 列名，默认 "εHf(t)"
        age_range : tuple, optional
            年龄范围 (Ma)，默认 (0, 4000)
        epsilon_range : tuple, optional
            εHf(t) 范围，默认 (-30, 20)
        show_chur : bool, optional
            显示 CHUR 参考线，默认 True
        show_dm : bool, optional
            显示 DM 参考线，默认 True
        color_by : str, optional
            颜色分组的列名（如 "Continent", "Depos.Age (Period)"）
        figsize : tuple, optional
            图形大小，默认 (12, 8)
        save : str, optional
            保存路径

        Returns
        -------
        plt.Figure
            matplotlib Figure 对象

        Examples
        --------
        >>> handler.plot_epsilon_hf_vs_age(
        ...     df_joined,
        ...     color_by="Continent",
        ...     save="epsilon_hf_asia.png"
        ... )
        """
        # 检查必需列
        if age_col not in df.columns or epsilon_col not in df.columns:
            raise ValueError(f"数据缺少必需列: {age_col} 或 {epsilon_col}")

        # 过滤有效数据
        valid_data = df.filter(
            (pl.col(age_col).is_not_null()) &
            (pl.col(epsilon_col).is_not_null()) &
            (pl.col(age_col) >= age_range[0]) &
            (pl.col(age_col) <= age_range[1]) &
            (pl.col(epsilon_col) >= epsilon_range[0]) &
            (pl.col(epsilon_col) <= epsilon_range[1])
        )

        if valid_data.height == 0:
            raise ValueError("没有有效数据可用于绘图")

        ages = valid_data[age_col].to_numpy()
        epsilon_hf = valid_data[epsilon_col].to_numpy()

        # 创建图形
        fig, ax = plt.subplots(figsize=figsize, dpi=self.config.figure_dpi)

        # 确定颜色映射
        if color_by and color_by in valid_data.columns:
            # 按分类变量着色
            categories = valid_data[color_by].unique().to_list()
            colors = plt.cm.tab20(np.linspace(0, 1, len(categories)))

            for i, cat in enumerate(categories):
                mask = valid_data[color_by] == cat
                cat_ages = valid_data.filter(mask)[age_col].to_numpy()
                cat_epsilon = valid_data.filter(mask)[epsilon_col].to_numpy()

                ax.scatter(
                    cat_ages, cat_epsilon,
                    c=[colors[i]], label=str(cat),
                    alpha=0.6, s=30, edgecolors='black', linewidths=0.5
                )

            ax.legend(fontsize=9, loc='upper left', bbox_to_anchor=(1.02, 1))
        else:
            # 使用 εHf(t) 值着色
            scatter = ax.scatter(
                ages, epsilon_hf,
                c=epsilon_hf, cmap='RdYlBu_r',
                alpha=0.6, s=30, edgecolors='black', linewidths=0.5,
                vmin=epsilon_range[0], vmax=epsilon_range[1]
            )

            # 添加颜色条
            cbar = plt.colorbar(scatter, ax=ax, pad=0.02)
            cbar.set_label('εHf(t)', fontsize=11)

        # 添加参考线
        if show_chur:
            # CHUR 参考线（εHf = 0）
            ax.axhline(y=0, color='red', linestyle='--', linewidth=2,
                      label='CHUR', alpha=0.7, zorder=3)

        if show_dm:
            # DM 参考线（计算 DM 的 εHf 值）
            # εHf_DM = 10000 × [(176Hf/177Hf)DM / (176Hf/177Hf)CHUR - 1]
            dm_epsilon = 10000 * (
                (DM_176HF_177HF_PRESENT / CHUR_176HF_177HF_PRESENT) - 1
            )
            ax.axhline(y=dm_epsilon, color='blue', linestyle='--',
                      linewidth=2, label='DM', alpha=0.7, zorder=3)

        # 添加地壳演化趋势线（简化）
        if show_chur:
            # 绘制从古老地壳到年轻地壳的演化趋势
            trend_ages = np.linspace(age_range[0], age_range[1], 100)

            # 典型地壳演化路径（简化）
            # 假设平均地壳 176Lu/177Hf = 0.015
            crust_lu_hf = 0.015
            t_years = trend_ages * 1e6
            decay_factor = np.exp(LAMBDA_176LU * t_years) - 1

            # 计算地壳的 εHf(t) 演化
            for initial_hf in [-10, -5, 0]:  # 不同的初始 εHf 值
                initial_hf_ratio = CHUR_176HF_177HF_PRESENT * (1 + initial_hf / 10000)
                hf_crust_t = initial_hf_ratio - crust_lu_hf * decay_factor
                hf_chur_t = CHUR_176HF_177HF_PRESENT - CHUR_176LU_177HF_PRESENT * decay_factor
                epsilon_evolution = 10000 * (hf_crust_t / hf_chur_t - 1)

                ax.plot(trend_ages, epsilon_evolution, 'gray', linestyle='-',
                        linewidth=0.5, alpha=0.3)

        # 设置标签和样式
        ax.set_xlabel('Age (Ma)', fontsize=13, fontweight='bold')
        ax.set_ylabel('εHf(t)', fontsize=13, fontweight='bold')
        ax.set_title(
            f'εHf(t) Evolution vs. Crystallization Age (n={valid_data.height:,})',
            fontsize=14, fontweight='bold'
        )

        # 添加网格和范围
        ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)
        ax.set_xlim(age_range)
        ax.set_ylim(epsilon_range)

        # 添加源区性质标注
        self._add_source_zones(ax)

        fig.tight_layout()

        if save:
            fig.savefig(save, dpi=self.config.figure_dpi, bbox_inches='tight')
            print(f"[Viz] 已保存: {save}")

        return fig

    def _add_source_zones(self, ax: plt.Axes) -> None:
        """在图上添加源区性质分区标注"""
        ylim = ax.get_ylim()

        # 添加源区性质文字标注
        ax.text(0.02, 0.95, "DM Source", transform=ax.transAxes,
                fontsize=9, color='blue', alpha=0.7,
                verticalalignment='top', fontweight='bold')

        ax.text(0.02, 0.50, "Juvenile Crust", transform=ax.transAxes,
                fontsize=9, color='green', alpha=0.7,
                verticalalignment='center')

        ax.text(0.02, 0.05, "Ancient Crust", transform=ax.transAxes,
                fontsize=9, color='red', alpha=0.7,
                verticalalignment='bottom', fontweight='bold')

    def plot_epsilon_hf_distribution(
        self,
        df: pl.DataFrame,
        epsilon_col: str = "εHf(t)",
        bins: int = 50,
        figsize: Tuple[float, float] = (14, 5),
        save: Optional[str] = None
    ) -> plt.Figure:
        """
        绘制 εHf(t) 分布图（直方图 + KDE）

        Parameters
        ----------
        df : pl.DataFrame
            输入数据
        epsilon_col : str, optional
            εHf(t) 列名，默认 "εHf(t)"
        bins : int, optional
            直方图箱数，默认 50
        figsize : tuple, optional
            图形大小，默认 (14, 5)
        save : str, optional
            保存路径

        Returns
        -------
        plt.Figure
        """
        if epsilon_col not in df.columns:
            raise ValueError(f"数据缺少列: {epsilon_col}")

        # 提取有效数据
        epsilon_data = df[epsilon_col].drop_nulls().to_numpy()

        if len(epsilon_data) == 0:
            raise ValueError(f"没有有效数据: {epsilon_col}")

        # 创建子图
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize,
                                        dpi=self.config.figure_dpi)

        # 左图：直方图
        ax1.hist(epsilon_data, bins=bins, color='steelblue',
                alpha=0.7, edgecolor='black', linewidth=0.5)

        # 添加参考线
        ax1.axvline(x=0, color='red', linestyle='--', linewidth=2,
                   label='CHUR', alpha=0.7)

        # 计算并标注 DM 参考线
        dm_epsilon = 10000 * ((DM_176HF_177HF_PRESENT / CHUR_176HF_177HF_PRESENT) - 1)
        ax1.axvline(x=dm_epsilon, color='blue', linestyle='--',
                   linewidth=2, label='DM', alpha=0.7)

        # 添加均值线
        mean_epsilon = np.mean(epsilon_data)
        ax1.axvline(x=mean_epsilon, color='green', linestyle='-',
                   linewidth=2, label=f'Mean: {mean_epsilon:+.1f}', alpha=0.7)

        ax1.set_xlabel('εHf(t)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        ax1.set_title(f'εHf(t) Distribution (Histogram, n={len(epsilon_data):,})',
                     fontsize=13, fontweight='bold')
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)

        # 右图：KDE
        try:
            x, y = self.analytics.kde(epsilon_data, bandwidth=None, n_points=1000)
            ax2.plot(x, y, linewidth=2.5, color='darkblue')
            ax2.fill_between(x, y, alpha=0.4, color='steelblue')

            # 添加相同的参考线
            ax2.axvline(x=0, color='red', linestyle='--', linewidth=2,
                       label='CHUR', alpha=0.7)
            ax2.axvline(x=dm_epsilon, color='blue', linestyle='--',
                       linewidth=2, label='DM', alpha=0.7)
            ax2.axvline(x=mean_epsilon, color='green', linestyle='-',
                       linewidth=2, label=f'Mean: {mean_epsilon:+.1f}', alpha=0.7)

            # 标注峰值
            peaks = self.analytics.find_peaks(x, y)
            for i, peak in enumerate(peaks[:3]):
                ax2.annotate(
                    f"Peak {i+1}: {peak['peak_age']:+.1f}",
                    xy=(peak["peak_age"], peak["peak_height"]),
                    xytext=(10, 10), textcoords='offset points',
                    fontsize=8, ha='left', color='red',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.3)
                )

        except Exception as e:
            print(f"[Viz] KDE 计算失败: {e}")
            ax2.text(0.5, 0.5, f'KDE calculation failed: {e}',
                    transform=ax2.transAxes, ha='center', va='center')

        ax2.set_xlabel('εHf(t)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Probability Density', fontsize=12, fontweight='bold')
        ax2.set_title(f'εHf(t) Distribution (KDE, n={len(epsilon_data):,})',
                     fontsize=13, fontweight='bold')
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save:
            fig.savefig(save, dpi=self.config.figure_dpi, bbox_inches='tight')
            print(f"[Viz] 已保存: {save}")

        return fig

    def plot_multi_epsilon_hf(
        self,
        datasets: Dict[str, np.ndarray],
        age_range: Tuple[float, float] = (0, 4000),
        epsilon_range: Tuple[float, float] = (-30, 20),
        figsize: Tuple[float, float] = (12, 8),
        save: Optional[str] = None
    ) -> plt.Figure:
        """
        绘制多样品 εHf(t) 对比图

        Parameters
        ----------
        datasets : dict
            数据字典，格式为 {名称: (ages_array, epsilon_array)}
        age_range : tuple, optional
            年龄范围
        epsilon_range : tuple, optional
            εHf(t) 范围
        figsize : tuple, optional
            图形大小
        save : str, optional
            保存路径

        Returns
        -------
        plt.Figure
        """
        fig, ax = plt.subplots(figsize=figsize, dpi=self.config.figure_dpi)

        colors = plt.cm.tab10(np.linspace(0, 1, len(datasets)))

        for i, (name, (ages, epsilons)) in enumerate(datasets.items()):
            # 过滤范围外的数据
            mask = (
                (ages >= age_range[0]) & (ages <= age_range[1]) &
                (epsilons >= epsilon_range[0]) & (epsilons <= epsilon_range[1])
            )

            valid_ages = ages[mask]
            valid_epsilons = epsilons[mask]

            if len(valid_ages) > 0:
                ax.scatter(
                    valid_ages, valid_epsilons,
                    c=[colors[i]], label=name,
                    alpha=0.6, s=25, edgecolors='black', linewidths=0.5
                )

        # 添加参考线
        ax.axhline(y=0, color='red', linestyle='--', linewidth=2,
                  label='CHUR', alpha=0.7, zorder=3)

        dm_epsilon = 10000 * ((DM_176HF_177HF_PRESENT / CHUR_176HF_177HF_PRESENT) - 1)
        ax.axhline(y=dm_epsilon, color='blue', linestyle='--',
                  linewidth=2, label='DM', alpha=0.7, zorder=3)

        # 设置标签
        ax.set_xlabel('Age (Ma)', fontsize=13, fontweight='bold')
        ax.set_ylabel('εHf(t)', fontsize=13, fontweight='bold')
        ax.set_title('Multi-sample εHf(t) Comparison', fontsize=14, fontweight='bold')

        ax.legend(fontsize=10, loc='upper left', bbox_to_anchor=(1.02, 1))
        ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)
        ax.set_xlim(age_range)
        ax.set_ylim(epsilon_range)

        plt.tight_layout()

        if save:
            fig.savefig(save, dpi=self.config.figure_dpi, bbox_inches='tight')
            print(f"[Viz] 已保存: {save}")

        return fig

    # ──────────────────── 岩石类型统计图 ─────────────────────────
    def plot_rock_type_statistics(
        self,
        df: pl.DataFrame,
        class_level: str = "Class1",
        plot_type: str = "bar",
        top_n: int = 15,
        save: Optional[str] = None,
        figsize: Tuple[float, float] = (12, 8),
    ) -> pl.DataFrame:
        """
        绘制岩石类型统计图（横向条形图）

        Parameters
        ----------
        df : pl.DataFrame
            输入数据
        class_level : str
            岩石分类级别："Class1", "Class2", "Class3"
        plot_type : str
            图表类型："bar"（横向条形图）或 "pie"（饼图）
        top_n : int
            显示前N个类别
        save : str, optional
            保存路径
        figsize : tuple
            图表尺寸

        Returns
        -------
        pl.DataFrame
            统计结果，包含列：岩石类型、count、percentage、cumulative_pct

        Examples
        --------
        >>> handler = OneDZHandler()
        >>> handler.load(source="csv")
        >>> stats = handler.viz.plot_rock_type_statistics(
        ...     handler.data,
        ...     class_level="Class1",
        ...     save="rock_type_class1.png"
        ... )
        """
        # 确定列名
        col_map = {
            "Class1": "Class-1 Rock Type",
            "Class2": "Class-2 Rock Type",
            "Class3": "Class-3 Rock Type"
        }

        if class_level not in col_map:
            raise ValueError(f"class_level 必须是 {list(col_map.keys())} 之一")

        col = col_map[class_level]

        # 过滤有效数据
        df_valid = df.filter(pl.col(col).is_not_null())

        if len(df_valid) == 0:
            raise ValueError(f"列 '{col}' 中没有有效数据")

        # 统计
        stats = (
            df_valid
            .group_by(col)
            .agg(pl.count().alias("count"))
            .sort("count", descending=True)
            .head(top_n)
            .with_columns([
                (pl.col("count") / pl.col("count").sum() * 100).alias("percentage"),
                (pl.col("count").cum_sum() / pl.col("count").sum() * 100).alias("cumulative_pct")
            ])
            .sort("count", descending=True)
        )

        # 打印统计信息
        total_valid = len(df_valid)
        total_all = len(df)
        coverage = (total_valid / total_all * 100) if total_all > 0 else 0

        print(f"\n岩石类型统计 (Class-{class_level[-1]}):")
        print(f"  总记录: {total_all:,}")
        print(f"  有效记录: {total_valid:,} ({coverage:.1f}%)")
        print(f"  类别数: {len(stats):,}")

        # 绘图
        if plot_type == "pie":
            self._draw_pie_chart(stats, col, class_level, save, figsize)
        elif plot_type == "bar":
            self._draw_horizontal_bar(stats, col, "Rock Type", class_level, save, figsize)
        else:
            raise ValueError(f"plot_type 必须是 'bar' 或 'pie'")

        return stats

    # ──────────────────── 地理分布图 ─────────────────────────────
    def plot_geographic_distribution(
        self,
        df: pl.DataFrame,
        geo_level: str = "continent",
        top_n: int = 20,
        save: Optional[str] = None,
        figsize: Tuple[float, float] = (12, 10),
    ) -> pl.DataFrame:
        """
        绘制地理分布图（横向条形图）

        Parameters
        ----------
        df : pl.DataFrame
            输入数据
        geo_level : str
            地理级别："continent", "major", "minor", "country", "formation"
        top_n : int
            显示前N个类别
        save : str, optional
            保存路径
        figsize : tuple
            图表尺寸

        Returns
        -------
        pl.DataFrame
            统计结果

        Examples
        --------
        >>> handler = OneDZHandler()
        >>> handler.load(source="csv")
        >>> stats = handler.viz.plot_geographic_distribution(
        ...     handler.data,
        ...     geo_level="continent",
        ...     save="geo_distribution.png"
        ... )
        """
        # 确定列名
        col_map = {
            "continent": "Continent",
            "major": "Major_Geographic_Geologic_Description",
            "minor": "Minor_Geologic_Geographic_Unit",
            "country": "Country_State",
            "formation": "Formation"
        }

        if geo_level not in col_map:
            raise ValueError(f"geo_level 必须是 {list(col_map.keys())} 之一")

        col = col_map[geo_level]

        # 过滤有效数据
        df_valid = df.filter(pl.col(col).is_not_null())

        if len(df_valid) == 0:
            raise ValueError(f"列 '{col}' 中没有有效数据")

        # 统计
        stats = (
            df_valid
            .group_by(col)
            .agg(pl.count().alias("count"))
            .sort("count", descending=True)
            .head(top_n)
            .with_columns([
                (pl.col("count") / pl.col("count").sum() * 100).alias("percentage"),
                (pl.col("count").cum_sum() / pl.col("count").sum() * 100).alias("cumulative_pct")
            ])
            .sort("count", descending=True)
        )

        # 打印统计信息
        total_valid = len(df_valid)
        total_all = len(df)
        coverage = (total_valid / total_all * 100) if total_all > 0 else 0

        print(f"\n地理分布统计 ({geo_level}):")
        print(f"  总记录: {total_all:,}")
        print(f"  有效记录: {total_valid:,} ({coverage:.1f}%)")
        print(f"  累计覆盖: {stats['cumulative_pct'][-1]:.1f}%")

        # 绘图
        self._draw_horizontal_bar(stats, col, "Geographic", geo_level, save, figsize)

        return stats

    # ──────────────────── 时间分布图（推导法）────────────────────────
    def plot_temporal_distribution(
        self,
        df: pl.DataFrame,
        save: Optional[str] = None,
        figsize: Tuple[float, float] = (12, 6),
    ) -> pl.DataFrame:
        """
        绘制时间分布图（基于 Best Age 推导 Period）

        Parameters
        ----------
        df : pl.DataFrame
            输入数据
        save : str, optional
            保存路径
        figsize : tuple
            图表尺寸

        Returns
        -------
        pl.DataFrame
            统计结果

        Examples
        --------
        >>> handler = OneDZHandler()
        >>> handler.load(source="csv")
        >>> stats = handler.viz.plot_temporal_distribution(
        ...     handler.data,
        ...     save="temporal_distribution.png"
        ... )
        """
        # 过滤有 Best Age 的记录
        df_with_age = df.filter(pl.col("Best Age").is_not_null())

        if len(df_with_age) == 0:
            raise ValueError("没有有效的 Best Age 数据")

        # 推导 Period
        df_with_age = df_with_age.with_columns([
            pl.col("Best Age")
            .map_elements(self._infer_period_from_age, return_dtype=str)
            .alias("Inferred_Period")
        ])

        # 过滤推导成功的记录
        df_with_age = df_with_age.filter(
            pl.col("Inferred_Period").is_not_null()
        )

        # 统计
        stats = (
            df_with_age
            .group_by("Inferred_Period")
            .agg([
                pl.count().alias("count"),
                pl.col("Best Age").mean().alias("mean_age_ma"),
                pl.col("Best Age").min().alias("min_age_ma"),
                pl.col("Best Age").max().alias("max_age_ma")
            ])
            .sort("Inferred_Period")
        )

        # 计算百分比
        total = stats["count"].sum()
        stats = stats.with_columns([
            (pl.col("count") / total * 100).alias("percentage")
        ])

        # 打印统计信息
        print(f"\n时间分布统计（推导法）:")
        print(f"  总记录: {len(df):,}")
        print(f"  有 Best Age: {len(df_with_age):,} ({len(df_with_age)/len(df)*100:.1f}%)")
        print(f"  推导成功: {total:,} ({total/len(df)*100:.1f}%)")

        # 绘图
        self._draw_temporal_bar(stats, save, figsize)

        return stats

    @staticmethod
    def _infer_period_from_age(best_age_ma: float) -> Optional[str]:
        """
        根据 Best Age 推导地质年代（Period级别）

        基于 International Chronostratigraphic Chart (v2023)
        """
        if best_age_ma is None:
            return None

        try:
            age = float(best_age_ma)
        except (TypeError, ValueError):
            return None

        # Cenozoic (0-66 Ma)
        if age < 2.588:
            return "Quaternary"
        elif age < 23.03:
            return "Neogene"
        elif age < 66.0:
            return "Paleogene"

        # Mesozoic (66-252 Ma)
        elif age < 145.0:
            return "Cretaceous"
        elif age < 201.3:
            return "Jurassic"
        elif age < 252.2:
            return "Triassic"

        # Paleozoic (252-541 Ma)
        elif age < 298.9:
            return "Permian"
        elif age < 358.9:
            return "Carboniferous"
        elif age < 419.2:
            return "Devonian"
        elif age < 423.0:
            return "Silurian"
        elif age < 477.7:
            return "Ordovician"
        elif age < 541.0:
            return "Cambrian"

        # Precambrian
        else:
            return "Precambrian"

    # ──────────────────── 私有绘图方法 ─────────────────────────────
    def _draw_horizontal_bar(
        self,
        stats: pl.DataFrame,
        col_name: str,
        chart_type: str,
        subtitle_info: str,
        save_path: Optional[str],
        figsize: Tuple[float, float],
    ) -> None:
        """绘制横向条形图（通用方法）"""
        fig, ax = plt.subplots(figsize=figsize, dpi=self.config.figure_dpi)

        # 反转数据
        categories = stats[col_name].to_list()[::-1]
        counts = stats["count"].to_list()[::-1]
        percentages = stats["percentage"].to_list()[::-1]
        cumulative = stats["cumulative_pct"].to_list()[::-1]

        # 绘制横向条形图
        y_pos = range(len(categories))

        if chart_type == "Rock Type":
            cmap = plt.cm.Spectral
        elif chart_type == "Geographic":
            cmap = plt.cm.viridis
        else:
            cmap = plt.cm.tab20

        bars = ax.barh(y_pos, counts, color=cmap(np.linspace(0.2, 0.8, len(categories))))

        # 设置y轴标签
        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories, fontsize=9)

        # 添加数值标签
        for i, (count, pct, cum) in enumerate(zip(counts, percentages, cumulative)):
            ax.text(
                count,
                i,
                f" {count:,} ({pct:.1f}% | cum: {cum:.1f}%)",
                va='center',
                fontsize=8
            )

        # 设置标题和标签
        title = f"{chart_type} Distribution ({subtitle_info})"
        self._setup_axes(ax, title=title, xlabel="Sample Count")

        # 添加网格
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)

        plt.tight_layout()

        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(save_path, dpi=self.config.figure_dpi, bbox_inches='tight')
            print(f"✅ 已保存: {save_path}")

        plt.close()

    def _draw_pie_chart(
        self,
        stats: pl.DataFrame,
        col_name: str,
        class_level: str,
        save_path: Optional[str],
        figsize: Tuple[float, float],
    ) -> None:
        """绘制饼图"""
        fig, ax = plt.subplots(figsize=figsize, dpi=self.config.figure_dpi)

        categories = stats[col_name].to_list()
        counts = stats["count"].to_list()
        percentages = stats["percentage"].to_list()

        # 创建标签
        labels = [f"{cat}\n({pct:.1f}%)" for cat, pct in zip(categories, percentages)]

        # 绘制饼图
        colors = plt.cm.Set3(range(len(categories)))
        wedges, texts, autotexts = ax.pie(
            counts,
            labels=labels,
            autopct='',
            startangle=90,
            colors=colors,
            pctdistance=0.85
        )

        # 美化字体
        for text in texts:
            text.set_fontsize(10)
            text.set_fontweight('bold')

        title = f"Rock Type Distribution (Class-{class_level[-1]})"
        self._setup_axes(ax, title=title)

        plt.tight_layout()

        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(save_path, dpi=self.config.figure_dpi, bbox_inches='tight')
            print(f"✅ 已保存: {save_path}")

        plt.close()

    def _draw_temporal_bar(
        self,
        stats: pl.DataFrame,
        save_path: Optional[str],
        figsize: Tuple[float, float],
    ) -> None:
        """绘制时间分布柱状图"""
        fig, ax = plt.subplots(figsize=figsize, dpi=self.config.figure_dpi)

        periods = stats["Inferred_Period"].to_list()
        counts = stats["count"].to_list()
        percentages = stats["percentage"].to_list()

        # 绘制柱状图
        x_pos = range(len(periods))
        bars = ax.bar(
            x_pos,
            counts,
            color=plt.cm.tab20(range(len(periods))),
            edgecolor='black',
            linewidth=1.5
        )

        # 设置x轴标签
        ax.set_xticks(x_pos)
        ax.set_xticklabels(periods, rotation=45, ha='right', fontsize=10)

        # 添加数值标签
        for i, (count, pct) in enumerate(zip(counts, percentages)):
            ax.text(
                i,
                count,
                f"{count:,}\n({pct:.1f}%)",
                ha='center',
                va='bottom',
                fontsize=9
            )

        # 设置标题和标签
        title = "Temporal Distribution (Derived from Best Age)"
        self._setup_axes(ax, title=title, xlabel="Geological Period", ylabel="Sample Count")

        # 添加网格
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)

        plt.tight_layout()

        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(save_path, dpi=self.config.figure_dpi, bbox_inches='tight')
            print(f"✅ 已保存: {save_path}")

        plt.close()


# ──────────────────── 辅助函数 ───────────────────────────────────
def stats_norm_pdf(x: np.ndarray, mean: float, std: float) -> np.ndarray:
    """正态分布 PDF。"""
    return np.exp(-0.5 * ((x - mean) / std) ** 2) / (std * np.sqrt(2 * np.pi))
