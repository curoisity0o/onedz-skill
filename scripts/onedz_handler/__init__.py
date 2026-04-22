"""
OneDZ Handler — 全球碎屑锆石数据库集成 Skill

基于 Li et al. (2025) OneDZ 数据库 (Zenodo 17407937)
提供数据加载、科学清洗、统计分析、可视化、多格式导出一站式接口。

Usage
-----
    >>> from onedz_handler import OneDZHandler
    >>> handler = OneDZHandler()
    >>> handler.load()
    >>> df = handler.query(periods=["Cretaceous"], rock_class1=["detrital"])
    >>> df_clean = handler.clean(df)
    >>> handler.plot_age(df_clean)
    >>> handler.export(df_clean, "result.csv")
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime

import polars as pl
import numpy as np
import matplotlib.pyplot as plt

from .config import (
    Cols,
    OneDZConfig,
    TABLE_UPB,
    TABLE_LUHF,
    GEO_PERIODS,
)
from .data_engine import DataEngine
from .qc import QCMODULE
from .analytics import Analytics
from .viz import Viz
from .export import Export
from .luhf_calculator import LuHfCalculator
from .dataset_info import check_dataset_exists, print_dataset_info


class OneDZHandler:
    """
    OneDZ 全球碎屑锆石数据库统一处理接口。

    整合 DataEngine、QC、Analytics、Viz、Export 五大模块，
    提供从数据加载到可视化导出的完整科研工作流。

    Parameters
    ----------
    config : OneDZConfig, optional
        配置对象，None 则使用默认配置

    Examples
    --------
    >>> handler = OneDZHandler()
    >>> handler.load(source="csv")
    >>> df = handler.query(periods=["Cretaceous"], rock_class1=["detrital"])
    >>> df_clean = handler.clean(df)
    >>> handler.plot_age(df_clean, mode="kde")
    >>> handler.export(df_clean, "result.csv")
    """

    def __init__(self, config: Optional[OneDZConfig] = None, silent: bool = False) -> None:
        """
        初始化 OneDZ Handler。

        Parameters
        ----------
        config : OneDZConfig, optional
            配置对象，None 则使用默认配置
        silent : bool, default False
            是否静默模式（不显示数据集信息）

        Notes
        -----
        如果数据集不存在或路径不正确，会显示友好的提示信息。
        """
        self.config = config or OneDZConfig()

        # 先初始化子模块
        self.engine = DataEngine(self.config)
        self.qc = QCMODULE(self.config)
        self.analytics = Analytics(self.config)
        self.viz = Viz(self.config)
        self.exporter = Export(self.config)
        self.luhf_calc = LuHfCalculator()  # 使用默认参数初始化

        # 初始化输出目录（在子模块初始化后）
        self._init_output_dir()

        # 检查数据集（非静默模式）
        if not silent:
            exists, message = check_dataset_exists(self.config.csv_dir)
            if exists:
                print_dataset_info(self.config.csv_dir)
            else:
                print(message)

    def _init_output_dir(self) -> None:
        """初始化输出目录，如果启用时间戳则创建带时间戳的子目录。"""
        base_output_dir = self.config.output_dir

        # 创建基础输出目录
        base_output_dir.mkdir(parents=True, exist_ok=True)

        # 如果启用时间戳，创建带时间戳的子目录
        if self.config.use_timestamp_output:
            timestamp = datetime.now().strftime(self.config.timestamp_format)
            timestamped_dir = base_output_dir / f"onedz_output_{timestamp}"
            timestamped_dir.mkdir(parents=True, exist_ok=True)

            # 输出信息
            print(f"📁 输出目录: {timestamped_dir}")

            # 更新配置中的输出目录（不影响其他模块，因为它们已经有了自己的config引用）
            # 我们需要在使用输出时动态使用handler的output_dir
            self._timestamped_output_dir = timestamped_dir
        else:
            self._timestamped_output_dir = base_output_dir

    def get_output_path(self, filename: str) -> Path:
        """
        获取输出文件的完整路径。

        Parameters
        ----------
        filename : str
            文件名

        Returns
        -------
        Path
            输出文件的完整路径
        """
        return self._timestamped_output_dir / filename

    # ──────────────────────────── 数据加载 ────────────────────────
    def load(
        self,
        source: str = "csv",
        table: str = TABLE_UPB,
        csv_dir: Optional[Path] = None,
    ) -> pl.DataFrame:
        """
        加载 OneDZ 数据。

        Parameters
        ----------
        source : str
            "csv" 或 "mysql"
        table : str
            "global_u-pb" 或 "global_lu-hf"
        csv_dir : Path, optional
            CSV 目录路径

        Returns
        -------
        pl.DataFrame
        """
        if source == "csv":
            return self.engine.load_csv(table, csv_dir)
        elif source == "mysql":
            return self.engine.load_mysql(table)
        else:
            raise ValueError(f"不支持的数据源: {source}。请使用 'csv' 或 'mysql'")

    @property
    def data(self) -> pl.DataFrame:
        """获取当前已加载的 U-Pb 数据。"""
        return self.engine.upb

    # ──────────────────────────── 多维查询 ────────────────────────
    def query(
        self,
        table: str = TABLE_UPB,
        *,
        periods: Optional[List[str]] = None,
        epoch: Optional[str] = None,
        rock_class1: Optional[List[str]] = None,
        rock_class2: Optional[List[str]] = None,
        rock_class3: Optional[List[str]] = None,
        region: Optional[str] = None,
        continent: Optional[str] = None,
        country_state: Optional[str] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        instruments: Optional[List[str]] = None,
        age_range: Optional[Tuple[float, float]] = None,
        formation: Optional[str] = None,
        max_records: Optional[int] = None,
    ) -> pl.DataFrame:
        """
        多维联合查询数据。

        Parameters
        ----------
        periods : list[str], optional
            地质年代，如 ["Cretaceous", "Jurassic"]
        epoch : str, optional
        rock_class1/2/3 : list[str], optional
            岩石分类
        region, continent, country_state : str, optional
            地理区域
        bbox : tuple(min_lon, min_lat, max_lon, max_lat), optional
        instruments : list[str], optional
            如 ["LA_ICP_MS", "SIMS"]
        age_range : tuple(min_ma, max_ma), optional
        formation : str, optional
        max_records : int, optional

        Returns
        -------
        pl.DataFrame
        """
        return self.engine.query(
            table=table,
            periods=periods,
            epoch=epoch,
            rock_class1=rock_class1,
            rock_class2=rock_class2,
            rock_class3=rock_class3,
            region=region,
            continent=continent,
            country_state=country_state,
            bbox=bbox,
            instruments=instruments,
            age_range=age_range,
            formation=formation,
            max_records=max_records,
        )

    # ──────────────────── 内存友好的惰性方法 ─────────────────────
    def query_from_csv(
        self,
        table: str = TABLE_UPB,
        **kwargs,
    ) -> pl.DataFrame:
        """
        内存友好的惰性查询，直接从 CSV 扫描，不加载全表到内存。
        不需要先调用 load()，不会缓存全表。

        适用于内存不足（<16 GB）的场景。
        参数与 query() 完全一致。

        Example
        -------
        >>> # 不需要 load()，直接查询
        >>> df_china = handler.query_from_csv(country_state="China")
        >>> df_clean = handler.clean(df_china)
        """
        return self.engine.query_from_csv(table=table, **kwargs)

    def join_from_csv(
        self,
        join_key: str = "Ref_Sample_Key",
        how: str = "inner",
        upb_filters: Optional[Dict] = None,
    ) -> pl.DataFrame:
        """
        内存友好的惰性 U-Pb / Lu-Hf join。
        U-Pb 用惰性扫描（不占内存），Lu-Hf 直接加载（183 MB）。
        不需要先调用 load()。

        Parameters
        ----------
        join_key : str
            连接键，默认 "Ref_Sample_Key"
        how : str
            "inner" / "left" / "outer"
        upb_filters : dict, optional
            U-Pb 预过滤条件，如 {"country_state": "China"}

        Example
        -------
        >>> df_joined = handler.join_from_csv()
        >>> df_china_hf = handler.join_from_csv(upb_filters={"country_state": "China"})
        """
        return self.engine.join_from_csv(
            join_key=join_key, how=how, upb_filters=upb_filters
        )

    # ──────────────────────────── 数据清洗 ────────────────────────
    def clean(
        self,
        df: Optional[pl.DataFrame] = None,
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
        df : pl.DataFrame, optional
            默认使用已加载的 U-Pb 数据
        compute_best_age : bool
        filter_concordance : bool
        concordance_min, concordance_max : float, optional
        standardize_errors : bool
        target_sigma : int
        remove_null_ages : bool
        age_range : tuple, optional

        Returns
        -------
        pl.DataFrame
        """
        src = df if df is not None else self.data
        return self.qc.clean(
            src,
            compute_best_age=compute_best_age,
            filter_concordance=filter_concordance,
            concordance_min=concordance_min,
            concordance_max=concordance_max,
            standardize_errors=standardize_errors,
            target_sigma=target_sigma,
            remove_null_ages=remove_null_ages,
            age_range=age_range,
        )

    # ──────────────────────────── 统计分析 ────────────────────────
    def analyze(
        self,
        df: Optional[pl.DataFrame] = None,
        age_col: str = Cols.BEST_AGE,
    ) -> Dict:
        """
        年龄分布综合分析。

        Parameters
        ----------
        df : pl.DataFrame, optional
        age_col : str

        Returns
        -------
        dict — summary, kde, peaks, bootstrap_mean
        """
        src = df if df is not None else self.data
        return self.analytics.analyze_distribution(src, age_col)

    def kde(
        self,
        ages: np.ndarray,
        bandwidth: Optional[float] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """KDE 分析。"""
        return self.analytics.kde(ages, bandwidth=bandwidth)

    def bootstrap(
        self,
        ages: np.ndarray,
        statistic: str = "kde",
        n_iterations: Optional[int] = None,
    ) -> Dict:
        """Bootstrap 重采样。"""
        return self.analytics.bootstrap(ages, statistic=statistic, n_iterations=n_iterations)

    def monte_carlo(
        self,
        ages: np.ndarray,
        errors: Optional[np.ndarray] = None,
        n_simulations: Optional[int] = None,
    ) -> Dict:
        """Monte Carlo 重采样。"""
        return self.analytics.monte_carlo(ages, errors=errors, n_simulations=n_simulations)

    def ks_test(
        self,
        ages_a: np.ndarray,
        ages_b: np.ndarray,
        alpha: float = 0.05,
    ) -> Dict:
        """K-S 检验。"""
        return Analytics.ks_test(ages_a, ages_b, alpha=alpha)

    # ──────────────────────────── 可视化 ──────────────────────────
    def plot_age(
        self,
        df: Optional[pl.DataFrame] = None,
        age_col: str = Cols.BEST_AGE,
        mode: str = "kde",
        bandwidth: Optional[float] = None,
        age_range: Tuple[float, float] = (0, 4000),
        show_peaks: bool = True,
        save: Optional[str] = None,
    ) -> plt.Figure:
        """
        绘制年龄频率分布图。

        Parameters
        ----------
        df : pl.DataFrame, optional
        age_col : str
        mode : str
            "kde" 或 "pdp"
        bandwidth : float, optional
        age_range : tuple
        show_peaks : bool
        save : str, optional
            保存文件名

        Returns
        -------
        plt.Figure
        """
        src = df if df is not None else self.data
        fig = self.viz.plot_age_distribution(
            src, age_col=age_col, mode=mode, bandwidth=bandwidth,
            age_range=age_range, show_peaks=show_peaks,
        )
        if save:
            fig.savefig(self.get_output_path(save), dpi=self.config.figure_dpi, bbox_inches="tight")
            print(f"[Viz] 已保存: {self.get_output_path(save)}")
        return fig

    def plot_multi_kde(
        self,
        data_dict: Dict[str, np.ndarray],
        age_range: Tuple[float, float] = (0, 4000),
        save: Optional[str] = None,
    ) -> plt.Figure:
        """多样品 KDE 对比图。"""
        fig = self.viz.plot_multi_kde(data_dict, age_range=age_range)
        if save:
            fig.savefig(self.get_output_path(save), dpi=self.config.figure_dpi, bbox_inches="tight")
            print(f"[Viz] 已保存: {self.get_output_path(save)}")
        return fig

    def plot_epsilon_hf(
        self,
        df: Optional[pl.DataFrame] = None,
        epsilon_hf_col: str = "εHf(t)",
        age_col: str = Cols.BEST_AGE,
        save: Optional[str] = None,
    ) -> plt.Figure:
        """εHf(t) 演化散图。"""
        src = df if df is not None else self.data
        fig = self.viz.plot_epsilon_hf(src, age_col=age_col, epsilon_hf_col=epsilon_hf_col)
        if save:
            fig.savefig(self.get_output_path(save), dpi=self.config.figure_dpi, bbox_inches="tight")
            print(f"[Viz] 已保存: {self.get_output_path(save)}")
        return fig

    def plot_tdm(
        self,
        df: Optional[pl.DataFrame] = None,
        model: str = "dm2",
        save: Optional[str] = None,
    ) -> plt.Figure:
        """TDM 模型年龄分布图。"""
        src = df if df is not None else self.data
        fig = self.viz.plot_tdm_distribution(src, model=model)
        if save:
            fig.savefig(self.get_output_path(save), dpi=self.config.figure_dpi, bbox_inches="tight")
            print(f"[Viz] 已保存: {self.get_output_path(save)}")
        return fig

    # ──────────────────────────── 导出 ────────────────────────────
    def export(
        self,
        df: Optional[pl.DataFrame] = None,
        filename: str = "onedz_export.csv",
        fmt: Optional[str] = None,
        **kwargs,
    ) -> Path:
        """
        多格式数据导出。

        Parameters
        ----------
        df : pl.DataFrame, optional
        filename : str
            输出文件名（根据扩展名自动识别格式）
        fmt : str, optional
            "csv" | "json" | "excel" | "geojson" | "shp"

        Returns
        -------
        Path — 输出文件路径
        """
        src = df if df is not None else self.data
        output_path = self.get_output_path(filename)

        # 直接使用完整路径导出，不使用exporter（避免重复添加路径）
        if fmt is None:
            fmt = self._guess_format_from_filename(filename)

        if fmt == "csv":
            src.write_csv(str(output_path))
        elif fmt == "json":
            src.write_json(str(output_path))
        else:
            # 对于其他格式，仍然使用exporter，但需要修改路径处理
            return self.exporter.export(src, filename=str(output_path), fmt=fmt, **kwargs)

        print(f"💾 已保存: {output_path}")
        return output_path

    def _guess_format_from_filename(self, filename: str) -> str:
        """从文件名猜测格式"""
        ext = Path(filename).suffix.lower()
        format_map = {
            ".csv": "csv",
            ".json": "json",
            ".xlsx": "excel",
            ".xls": "excel",
            ".geojson": "geojson",
            ".shp": "shp",
        }
        return format_map.get(ext, "csv")

    def save_figure(
        self,
        fig: plt.Figure,
        filename: str,
        dpi: Optional[int] = None,
        **kwargs,
    ) -> Path:
        """
        保存图表到输出目录。

        Parameters
        ----------
        fig : plt.Figure
            matplotlib图表对象
        filename : str
            文件名
        dpi : int, optional
            分辨率，默认使用配置中的figure_dpi
        **kwargs
            传递给fig.savefig的其他参数

        Returns
        -------
        Path — 保存的文件路径
        """
        output_path = self.get_output_path(filename)
        dpi = dpi or self.config.figure_dpi

        fig.savefig(str(output_path), dpi=dpi, bbox_inches='tight', **kwargs)
        print(f"💾 已保存: {output_path}")

        return output_path

    # ──────────────────────────── 样品管理 ────────────────────────
    def get_samples(self, df: Optional[pl.DataFrame] = None) -> pl.DataFrame:
        """获取去重后的样品列表。"""
        return self.engine.get_samples(df or self.data)

    # ──────────────────────────── 信息摘要 ────────────────────────
    def info(self) -> Dict:
        """返回当前数据集概览。"""
        df = self.data
        info_dict = {
            "total_records": df.height,
            "total_columns": df.width,
            "columns": df.columns,
        }

        if Cols.BEST_AGE in df.columns:
            ages = df[Cols.BEST_AGE].drop_nulls()
            info_dict["age_stats"] = {
                "n_valid": len(ages),
                "min": float(ages.min()) if len(ages) > 0 else None,
                "max": float(ages.max()) if len(ages) > 0 else None,
                "mean": float(ages.mean()) if len(ages) > 0 else None,
            }

        for rock_col in [Cols.CLASS1_ROCK, Cols.CLASS2_ROCK, Cols.CLASS3_ROCK]:
            if rock_col in df.columns:
                key = rock_col.replace(" ", "_").replace("-", "_").lower()
                info_dict[f"{key}_counts"] = df[rock_col].value_counts().to_dicts()

        return info_dict

    # ──────────────────── Lu-Hf 功能 ───────────────────────────────
    def join_upb_luhf(
        self,
        join_key: str = "Ref_Sample_Key",
        how: str = "inner"
    ) -> pl.DataFrame:
        """
        联合查询 U-Pb 和 Lu-Hf 数据

        Parameters
        ----------
        join_key : str, optional
            连接键，默认 "Ref_Sample_Key"
            - "Ref_Sample_Key": 文献样品键（推荐）
            - "Sample&Grain": 样品颗粒号（精确）
        how : str, optional
            连接方式，默认 "inner"

        Returns
        -------
        pl.DataFrame
            联合后的数据

        Examples
        --------
        >>> handler.load(source="csv", table=TABLE_UPB)
        >>> handler.load(source="csv", table=TABLE_LUHF)
        >>> df_joined = handler.join_upb_luhf(join_key="Ref_Sample_Key")
        """
        return self.engine.join_upb_luhf(join_key=join_key, how=how)

    def compute_epsilon_hf(
        self,
        df: Optional[pl.DataFrame] = None,
        hf_col: str = "176Hf/177Hf",
        lu_col: str = "176Lu/177Hf",
        age_col: str = Cols.BEST_AGE,
        compute_tdm: bool = True
    ) -> pl.DataFrame:
        """
        计算 εHf(t) 和 TDM

        Parameters
        ----------
        df : pl.DataFrame, optional
            输入数据，默认使用当前数据
        hf_col : str, optional
            176Hf/177Hf 列名
        lu_col : str, optional
            176Lu/177Hf 列名
        age_col : str, optional
            年龄列名
        compute_tdm : bool, optional
            是否计算 TDM，默认 True

        Returns
        -------
        pl.DataFrame
            添加了 εHf(t) 和 TDM 列的数据

        Examples
        --------
        >>> df_joined = handler.join_upb_luhf()
        >>> df_computed = handler.compute_epsilon_hf(df_joined)
        >>> print(df_computed["εHf(t)"].describe())
        """
        src = df if df is not None else self.data
        return self.luhf_calc.compute_batch(
            src,
            hf_col=hf_col,
            lu_col=lu_col,
            age_col=age_col,
            compute_tdm=compute_tdm
        )

    def plot_epsilon_hf(
        self,
        df: Optional[pl.DataFrame] = None,
        age_col: str = Cols.BEST_AGE,
        epsilon_col: str = "εHf(t)",
        color_by: Optional[str] = None,
        save: Optional[str] = None
    ) -> plt.Figure:
        """
        绘制 εHf(t) vs Age 散点图

        Parameters
        ----------
        df : pl.DataFrame, optional
            输入数据
        age_col : str, optional
            年龄列名
        epsilon_col : str, optional
            εHf(t) 列名
        color_by : str, optional
            颜色分组的列名
        save : str, optional
            保存路径

        Returns
        -------
        plt.Figure

        Examples
        --------
        >>> handler.plot_epsilon_hf(
        ...     df_computed,
        ...     color_by="Continent",
        ...     save="epsilon_hf.png"
        ... )
        """
        src = df if df is not None else self.data
        return self.viz.plot_epsilon_hf_vs_age(
            src, age_col=age_col, epsilon_col=epsilon_col,
            color_by=color_by, save=save
        )

    def plot_epsilon_hf_distribution(
        self,
        df: Optional[pl.DataFrame] = None,
        epsilon_col: str = "εHf(t)",
        save: Optional[str] = None
    ) -> plt.Figure:
        """
        绘制 εHf(t) 分布图

        Parameters
        ----------
        df : pl.DataFrame, optional
            输入数据
        epsilon_col : str, optional
            εHf(t) 列名
        save : str, optional
            保存路径

        Returns
        -------
        plt.Figure
        """
        src = df if df is not None else self.data
        return self.viz.plot_epsilon_hf_distribution(
            src, epsilon_col=epsilon_col, save=save
        )

    def plot_tdm(
        self,
        df: Optional[pl.DataFrame] = None,
        tdm_col: str = "TDM1",
        save: Optional[str] = None
    ) -> plt.Figure:
        """
        绘制 TDM 分布图

        Parameters
        ----------
        df : pl.DataFrame, optional
            输入数据
        tdm_col : str, optional
            TDM 列名
        save : str, optional
            保存路径

        Returns
        -------
        plt.Figure
        """
        src = df if df is not None else self.data
        model = "dm1" if "TDM1" in tdm_col else "dm2"

        # 提取 TDM 数据
        if tdm_col in src.columns:
            tdm_data = src[tdm_col].drop_nulls().to_numpy()

            # 创建图表
            fig, ax = plt.subplots(figsize=(10, 6), dpi=self.config.figure_dpi)

            # KDE
            x, y = self.analytics.kde(tdm_data, bandwidth=None, n_points=1000)
            ax.plot(x, y, linewidth=2.5, color='darkblue')
            ax.fill_between(x, y, alpha=0.4, color='steelblue')

            # 峰值标注
            peaks = self.analytics.find_peaks(x, y)
            for i, peak in enumerate(peaks[:3]):
                ax.annotate(
                    f"Peak {i+1}: {peak['peak_age']:.0f} Ma",
                    xy=(peak["peak_age"], peak["peak_height"]),
                    xytext=(10, 10), textcoords='offset points',
                    fontsize=8, ha='left', color='red',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.3)
                )

            ax.set_xlabel(f'{tdm_col} Age (Ma)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Probability Density', fontsize=12, fontweight='bold')
            ax.set_title(f'{tdm_col} Distribution (n={len(tdm_data):,})',
                        fontsize=13, fontweight='bold')
            ax.grid(True, alpha=0.3)

            plt.tight_layout()

            if save:
                fig.savefig(self.get_output_path(save), dpi=self.config.figure_dpi, bbox_inches='tight')
                print(f"[Viz] 已保存: {self.get_output_path(save)}")

            return fig
        else:
            raise ValueError(f"数据中未找到列: {tdm_col}")

    def __repr__(self) -> str:
        try:
            n = self.data.height
        except Exception:
            n = 0
        return f"OneDZHandler(records={n})"


# ──────────────── 公共 API ───────────────────────────────────────
__all__ = [
    "OneDZHandler",
    "OneDZConfig",
    "Cols",
    "DataEngine",
    "QCMODULE",
    "Analytics",
    "Viz",
    "Export",
    "LuHfCalculator",
    "GEO_PERIODS",
]
