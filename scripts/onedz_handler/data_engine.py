"""
OneDZ Handler — 数据引擎 (Data Engine)

支持 CSV (Polars) 和 MySQL 双模式数据加载，提供多维联合查询接口。
v1.3.0: 新增惰性查询 query_from_csv() 和惰性 join join_from_csv()，解决内存不足问题。
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import polars as pl
import numpy as np

from .config import (
    Cols,
    OneDZConfig,
    TABLE_UPB,
    TABLE_LUHF,
    GEO_PERIODS,
)
from .utils import (
    normalize_columns,
    coerce_numeric,
    estimate_missing_coordinates,
    period_to_age_range,
    standardize_column_name,
)


class DataEngine:
    """OneDZ 多源数据引擎：统一 CSV / MySQL 数据访问层。"""

    def __init__(self, config: OneDZConfig) -> None:
        self.config = config
        self._upb_df: Optional[pl.DataFrame] = None
        self._luhf_df: Optional[pl.DataFrame] = None
        self._mysql_engine = None

    # ──────────────────── 内部共享方法 ─────────────────────────

    def _find_csv_file(self, table: str, directory: Optional[Path] = None) -> Path:
        """
        根据表名查找对应的 CSV 文件。

        Parameters
        ----------
        table : str
            "global_u-pb" 或 "global_lu-hf"
        directory : Path, optional
            CSV 所在目录，默认使用 config.csv_dir

        Returns
        -------
        Path — 匹配的 CSV 文件路径
        """
        directory = directory or self.config.csv_dir

        # 搜索根目录和 Structured/ 子目录
        all_dirs = [directory]
        structured = directory / "Structured"
        if structured.is_dir():
            all_dirs.append(structured)

        all_csvs = []
        for d in all_dirs:
            all_csvs.extend(d.glob("*.csv"))
            all_csvs.extend(d.glob("*.CSV"))

        if not all_csvs:
            raise FileNotFoundError(f"在 {directory} 中未找到 CSV 文件")

        # 根据表名匹配
        target = None
        for f in all_csvs:
            fname = f.stem.lower()
            if table == TABLE_UPB and ("upb" in fname or "u-pb" in fname):
                target = f
                break
            elif table == TABLE_LUHF and ("luhf" in fname or "lu-hf" in fname):
                target = f
                break

        if target is None and all_csvs:
            target = all_csvs[0]
        if target is None:
            raise FileNotFoundError(f"在 {directory} 中未找到匹配 '{table}' 的 CSV 文件")

        return target

    def _build_filters(self, df_or_schema, *, periods=None, epoch=None,
                       rock_class1=None, rock_class2=None, rock_class3=None,
                       region=None, continent=None, country_state=None,
                       bbox=None, instruments=None, age_range=None,
                       formation=None):
        """
        构建过滤条件列表（query() 和 query_from_csv() 共用）。

        Parameters
        ----------
        df_or_schema : pl.DataFrame | pl.LazyFrame | pl.Schema
            DataFrame 或其 schema，用于检查列是否存在

        其余参数与 query() 一致。

        Returns
        -------
        list[pl.Expr] — 过滤表达式列表
        """
        filters = []

        # 辅助函数：检查列是否存在
        def has_col(name):
            if isinstance(df_or_schema, pl.DataFrame):
                return name in df_or_schema.columns
            elif isinstance(df_or_schema, pl.LazyFrame):
                return name in df_or_schema.collect_schema().names()
            elif isinstance(df_or_schema, pl.Schema):
                return name in df_or_schema.names()
            return False

        # 地质年代 → 沉积年龄范围
        if periods:
            ranges = [period_to_age_range(p) for p in periods]
            ranges = [r for r in ranges if r is not None]
            if ranges:
                period_expr = pl.lit(False)
                for min_a, max_a in ranges:
                    period_expr = period_expr | (
                        (pl.col(Cols.EST_DEPOS_AGE) >= min_a)
                        & (pl.col(Cols.EST_DEPOS_AGE) <= max_a)
                    )
                filters.append(period_expr)

        if epoch and has_col(Cols.DEPOS_AGE_EPOCH):
            filters.append(pl.col(Cols.DEPOS_AGE_EPOCH).str.contains(epoch, literal=True))

        # 岩石分类
        if rock_class1 and has_col(Cols.CLASS1_ROCK):
            filters.append(pl.col(Cols.CLASS1_ROCK).is_in(rock_class1))
        if rock_class2 and has_col(Cols.CLASS2_ROCK):
            filters.append(pl.col(Cols.CLASS2_ROCK).is_in(rock_class2))
        if rock_class3 and has_col(Cols.CLASS3_ROCK):
            filters.append(pl.col(Cols.CLASS3_ROCK).is_in(rock_class3))

        # 地理
        if region and has_col(Cols.REGION):
            filters.append(pl.col(Cols.REGION).str.contains(region, literal=False))
        if continent and has_col(Cols.CONTINENT):
            filters.append(pl.col(Cols.CONTINENT).str.contains(continent, literal=False))
        if country_state and has_col(Cols.COUNTRY_STATE):
            filters.append(pl.col(Cols.COUNTRY_STATE).str.contains(country_state, literal=False))

        # 空间范围
        if bbox:
            min_lon, min_lat, max_lon, max_lat = bbox
            filters.extend([
                (pl.col(Cols.LONGITUDE) >= min_lon) & (pl.col(Cols.LONGITUDE) <= max_lon),
                (pl.col(Cols.LATITUDE) >= min_lat) & (pl.col(Cols.LATITUDE) <= max_lat),
            ])

        # 仪器
        if instruments and has_col(Cols.MASS_SPECTROMETER):
            filters.append(pl.col(Cols.MASS_SPECTROMETER).is_in(instruments))

        # 年龄范围
        if age_range:
            filters.append(
                (pl.col(Cols.BEST_AGE) >= age_range[0])
                & (pl.col(Cols.BEST_AGE) <= age_range[1])
            )

        # 地层
        if formation and has_col(Cols.FORMATION):
            filters.append(pl.col(Cols.FORMATION).str.contains(formation, literal=False))

        return filters

    @staticmethod
    def _apply_filters(df_or_lf, filters, max_records=None):
        """将过滤条件列表应用到 DataFrame 或 LazyFrame，返回过滤后的对象。"""
        if filters:
            combined = filters[0]
            for f in filters[1:]:
                combined = combined & f
            df_or_lf = df_or_lf.filter(combined)
        if max_records:
            df_or_lf = df_or_lf.head(max_records)
        return df_or_lf

    @staticmethod
    def _post_process(df):
        """加载后的后处理：数值列转换 + 坐标修复。"""
        numeric_cols = [
            Cols.LATITUDE, Cols.LONGITUDE,
            Cols.AGE_206PB_238U, Cols.AGE_207PB_206PB, Cols.AGE_207PB_235U,
            Cols.BEST_AGE, Cols.BEST_AGE_1S, Cols.BEST_AGE_2S,
            Cols.DISCORD_RATIO,
            Cols.MAX_DEPOS_AGE, Cols.EST_DEPOS_AGE, Cols.MIN_DEPOS_AGE,
            Cols.U_PPM, Cols.TH_PPM, Cols.TH_U,
            "176Hf/177Hf", "176Hf/177Hf_1sigma", "176Hf/177Hf_2sigma",
            "176Lu/177Hf", "176Lu/177Hf_1sigma",
            "εHf(0)", "εHf(0)_1sigma",
            "εHf(t)", "εHf(t)_1sigma", "εHf(t)_2sigma",
            "TDM1 (Ma)", "TDM1 (Ma)_1sigma",
            "TDM2 (Ma)", "TDM2 (Ma)_1sigma",
            "U-Pb Age (Ma)", "U-Pb Age (Ma)_1σ", "U-Pb Age (Ma)_2σ",
        ]
        existing_numeric = [c for c in numeric_cols if c in df.columns]
        df = coerce_numeric(df, existing_numeric)
        df = estimate_missing_coordinates(df)
        return df

    # ──────────────────── 数据加载（原有，不变） ─────────────────

    def load_csv(
        self,
        table: str = TABLE_UPB,
        csv_dir: Optional[Path] = None,
    ) -> pl.DataFrame:
        """
        从 CSV 文件加载数据（全量加载到内存并缓存）。

        Parameters
        ----------
        table : str
            "global_u-pb" 或 "global_lu-hf"
        csv_dir : Path, optional

        Returns
        -------
        pl.DataFrame
        """
        target = self._find_csv_file(table, csv_dir)

        print(f"[DataEngine] 加载 CSV: {target}")
        df = pl.read_csv(target, infer_schema_length=50000, ignore_errors=True)
        df = normalize_columns(df)
        df = self._post_process(df)

        # 缓存
        if table == TABLE_UPB:
            self._upb_df = df
        else:
            self._luhf_df = df

        print(f"[DataEngine] 加载完成: {df.height} 行, {df.width} 列")
        return df

    def load_mysql(
        self,
        table: str = TABLE_UPB,
        query: Optional[str] = None,
    ) -> pl.DataFrame:
        """从 MySQL 数据库加载数据。"""
        try:
            import pymysql
            from sqlalchemy import create_engine
        except ImportError:
            raise ImportError("MySQL 模式需要安装 pymysql 和 sqlalchemy")

        cfg = self.config
        url = (
            f"mysql+pymysql://{cfg.mysql_user}:{cfg.mysql_password}"
            f"@{cfg.mysql_host}:{cfg.mysql_port}/{cfg.mysql_database}"
        )
        engine = create_engine(url, pool_size=5, max_overflow=10, pool_recycle=3600)
        self._mysql_engine = engine

        sql = query or f"SELECT * FROM `{table}`"
        print(f"[DataEngine] 执行 SQL: {sql[:100]}...")

        import pandas as pd
        pdf = pd.read_sql(sql, engine)
        df = pl.from_pandas(pdf)
        df = normalize_columns(df)

        if table == TABLE_UPB or "u-pb" in table:
            self._upb_df = df
        else:
            self._luhf_df = df

        print(f"[DataEngine] MySQL 加载完成: {df.height} 行")
        return df

    # ──────────────────── 数据获取 ─────────────────────────────────

    @property
    def upb(self) -> pl.DataFrame:
        """获取 U-Pb 数据，未加载时自动尝试 CSV 加载。"""
        if self._upb_df is None:
            return self.load_csv(TABLE_UPB)
        return self._upb_df

    @property
    def luhf(self) -> pl.DataFrame:
        """获取 Lu-Hf 数据。"""
        if self._luhf_df is None:
            return self.load_csv(TABLE_LUHF)
        return self._luhf_df

    # ──────────────────── 多维查询（原有，重构为复用 _build_filters） ───

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
        多维联合查询（从已缓存的全表中过滤）。
        需要先调用 load() 加载数据。

        Parameters
        ----------
        table : str
            "global_u-pb" 或 "global_lu-hf"
        periods : list[str], optional
        epoch : str, optional
        rock_class1/2/3 : list[str], optional
        region, continent, country_state : str, optional
        bbox : tuple
        instruments : list[str], optional
        age_range : tuple, optional
        formation : str, optional
        max_records : int, optional

        Returns
        -------
        pl.DataFrame
        """
        df = self.upb if table == TABLE_UPB else self.luhf
        filters = self._build_filters(
            df, periods=periods, epoch=epoch,
            rock_class1=rock_class1, rock_class2=rock_class2, rock_class3=rock_class3,
            region=region, continent=continent, country_state=country_state,
            bbox=bbox, instruments=instruments, age_range=age_range, formation=formation,
        )
        df = self._apply_filters(df, filters, max_records)

        print(f"[DataEngine] 查询结果: {df.height} 行")
        return df

    # ──────────────────── 惰性查询（新增） ────────────────────────────

    def query_from_csv(
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
        内存友好的惰性查询，直接从 CSV 文件过滤，不加载全表到内存。
        不需要先调用 load()，不会缓存全表。

        与 query() 的区别：
        - query()          从 self._upb_df 缓存中过滤（需要先 load()，全表在内存）
        - query_from_csv() 从 CSV 文件惰性扫描，只加载匹配的行（省内存）

        Parameters: 与 query() 完全一致。

        Returns
        -------
        pl.DataFrame

        Example
        -------
        >>> # 不需要 load()，直接查询，内存占用 ~0.5 GB
        >>> df_china = engine.query_from_csv(country_state="China")
        """
        target = self._find_csv_file(table)

        # 惰性读取（不占内存）
        lf = pl.scan_csv(target, infer_schema_length=50000, ignore_errors=True)
        # 列名标准化（lazy 版本）
        lf = self._normalize_lazy(lf)

        # 构建过滤条件
        filters = self._build_filters(
            lf, periods=periods, epoch=epoch,
            rock_class1=rock_class1, rock_class2=rock_class2, rock_class3=rock_class3,
            region=region, continent=continent, country_state=country_state,
            bbox=bbox, instruments=instruments, age_range=age_range, formation=formation,
        )

        # 应用过滤
        lf = self._apply_filters(lf, filters, max_records)

        # collect() 时才真正读取文件，只加载匹配的行
        print(f"[DataEngine] 惰性查询: 扫描 {target.name} ...")
        df = lf.collect()

        # 后处理
        df = normalize_columns(df)
        df = self._post_process(df)

        print(f"[DataEngine] 惰性查询结果: {df.height} 行")
        return df

    def _normalize_lazy(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        """
        LazyFrame 版本的列名标准化。
        scan_csv 后列名可能是原始 CSV 列名，需要映射到标准名。
        """
        rename_map = {}
        schema = lf.collect_schema()
        existing = set(schema.names())

        from .config import COLUMN_ALIASES
        for std_name, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                if alias in existing and alias != std_name:
                    rename_map[alias] = std_name
                    break

        if rename_map:
            lf = lf.rename(rename_map)
        return lf

    # ──────────────────── 惰性 join（新增） ───────────────────────────

    def join_from_csv(
        self,
        join_key: str = "Ref_Sample_Key",
        how: str = "inner",
        upb_filters: Optional[Dict] = None,
    ) -> pl.DataFrame:
        """
        内存友好的惰性 U-Pb / Lu-Hf join。
        U-Pb 用 scan_csv 惰性加载（不占内存），Lu-Hf 直接加载（183 MB，很小）。
        polars lazy 引擎自动优化：扫描 U-Pb 时只保留能 join 上的行。
        不需要先调用 load()。

        Parameters
        ----------
        join_key : str
            连接键，默认 "Ref_Sample_Key"
        how : str
            连接方式 "inner" / "left" / "outer"
        upb_filters : dict, optional
            U-Pb 预过滤条件，如 {"country_state": "China"}。
            指定后先过滤 U-Pb 再 join，进一步节省内存。

        Returns
        -------
        pl.DataFrame

        Example
        -------
        >>> # 全量 join（内存 ~1 GB）
        >>> df = engine.join_from_csv()

        >>> # 带预过滤（只要中国的 Lu-Hf 数据，内存 ~0.5 GB）
        >>> df = engine.join_from_csv(upb_filters={"country_state": "China"})
        """
        upb_file = self._find_csv_file(TABLE_UPB)
        luhf_file = self._find_csv_file(TABLE_LUHF)

        # U-Pb: 惰性加载（0 内存）
        lf_upb = pl.scan_csv(upb_file, infer_schema_length=50000, ignore_errors=True)
        lf_upb = self._normalize_lazy(lf_upb)

        # 可选：先过滤 U-Pb
        if upb_filters:
            filters = self._build_filters(lf_upb, **upb_filters)
            if filters:
                combined = filters[0]
                for f in filters[1:]:
                    combined = combined & f
                lf_upb = lf_upb.filter(combined)
            print(f"[DataEngine] 惰性 join: U-Pb 预过滤 {upb_filters}")

        # Lu-Hf: 直接加载（183 MB，没问题）
        print(f"[DataEngine] 惰性 join: 加载 Lu-Hf {luhf_file.name} ...")
        df_luhf = pl.read_csv(luhf_file, infer_schema_length=50000, ignore_errors=True)
        df_luhf = normalize_columns(df_luhf)

        # 标准化连接键名称
        upb_key = standardize_column_name(join_key, lf_upb.collect_schema())
        luhf_key = standardize_column_name(join_key, df_luhf)

        # 检查连接键是否存在
        if upb_key not in lf_upb.collect_schema().names():
            schema_names = lf_upb.collect_schema().names()[:10]
            raise ValueError(
                f"U-Pb 数据中未找到连接键 '{upb_key}'。\n"
                f"可用列（前10个）: {', '.join(schema_names)}..."
            )
        if luhf_key not in df_luhf.columns:
            available_cols = ", ".join(df_luhf.columns[:10])
            raise ValueError(
                f"Lu-Hf 数据中未找到连接键 '{luhf_key}'。\n"
                f"可用列（前10个）: {available_cols}..."
            )

        # 惰性 join
        print(f"[DataEngine] 惰性 join: 连接键={join_key}, 方式={how}")
        lf_result = lf_upb.join(df_luhf, left_on=upb_key, right_on=luhf_key, how=how)

        # collect() 才真正执行
        print(f"[DataEngine] 惰性 join: 执行中 ...")
        df_result = lf_result.collect()
        df_result = normalize_columns(df_result)

        print(f"[DataEngine] 惰性 join 完成: {df_result.height} 行, {df_result.width} 列")
        return df_result

    # ──────────────────── 按样品聚合（原有，不变） ─────────────────

    def get_samples(self, df: Optional[pl.DataFrame] = None) -> pl.DataFrame:
        """获取去重后的样品列表（按 Unique_Sample_No. 聚合）。"""
        src = df or self.upb
        if Cols.UNIQUE_SAMPLE_NO not in src.columns:
            raise ValueError("数据中缺少 Unique_Sample_No. 列")

        sample_cols = [
            Cols.UNIQUE_SAMPLE_NO, Cols.PUBLISHED_SAMPLE_ID,
            Cols.LATITUDE, Cols.LONGITUDE,
            Cols.FORMATION, Cols.REGION, Cols.CONTINENT,
            Cols.CLASS1_ROCK, Cols.EST_DEPOS_AGE,
        ]
        available = [c for c in sample_cols if c in src.columns]

        result = (
            src.group_by(Cols.UNIQUE_SAMPLE_NO)
            .agg([
                pl.col(c).first().alias(c) for c in available if c != Cols.UNIQUE_SAMPLE_NO
            ] + [
                pl.count().alias("grain_count")
            ])
        )
        return result

    # ──────────────────── SQL 直通查询（原有，不变） ────────────────

    def raw_sql(self, sql: str) -> pl.DataFrame:
        """执行自定义 SQL 查询（仅 MySQL 模式）。"""
        if self._mysql_engine is None:
            raise RuntimeError("MySQL 未连接。请先调用 load_mysql() 初始化连接。")

        import pandas as pd
        pdf = pd.read_sql(sql, self._mysql_engine)
        return pl.from_pandas(pdf)

    # ──────────────────── U-Pb 与 Lu-Hf 联合查询（原有，不变） ───────

    def join_upb_luhf(
        self,
        join_key: str = "Ref_Sample_Key",
        how: str = "inner",
        upb_df: Optional[pl.DataFrame] = None,
        luhf_df: Optional[pl.DataFrame] = None
    ) -> pl.DataFrame:
        """联合查询 U-Pb 和 Lu-Hf 数据（需要先 load()）。"""
        # 获取数据
        upb = upb_df if upb_df is not None else self.upb
        luhf = luhf_df if luhf_df is not None else self.luhf

        # 检查数据是否存在
        if upb is None or upb.height == 0:
            raise ValueError("U-Pb 数据未加载或为空。请先调用 load_csv() 加载数据。")
        if luhf is None or luhf.height == 0:
            raise ValueError("Lu-Hf 数据未加载或为空。请先调用 load_csv() 加载数据。")

        # 标准化连接键名称
        upb_key = standardize_column_name(join_key, upb)
        luhf_key = standardize_column_name(join_key, luhf)

        # 检查连接键是否存在
        if upb_key not in upb.columns:
            available_cols = ", ".join(upb.columns[:10])
            raise ValueError(
                f"U-Pb 数据中未找到连接键 '{upb_key}'。\n"
                f"可用列（前10个）: {available_cols}..."
            )
        if luhf_key not in luhf.columns:
            available_cols = ", ".join(luhf.columns[:10])
            raise ValueError(
                f"Lu-Hf 数据中未找到连接键 '{luhf_key}'。\n"
                f"可用列（前10个）: {available_cols}..."
            )

        # 执行 JOIN
        print(f"[DataEngine] 执行 U-Pb 与 Lu-Hf 联合查询")
        print(f"[DataEngine]   连接键: {join_key}")
        print(f"[DataEngine]   连接方式: {how}")
        print(f"[DataEngine]   U-Pb 记录: {upb.height:,}")
        print(f"[DataEngine]   Lu-Hf 记录: {luhf.height:,}")

        result = upb.join(luhf, left_on=upb_key, right_on=luhf_key, how=how)

        print(f"[DataEngine] 联合查询完成: {result.height} 行, {result.width} 列")

        if how == "inner":
            match_rate = result.height / min(upb.height, luhf.height) * 100
            print(f"[DataEngine] 匹配率: {match_rate:.1f}%")

        return result

    def get_join_statistics(
        self,
        join_key: str = "Ref_Sample_Key"
    ) -> Dict[str, int]:
        """获取 U-Pb 与 Lu-Hf 数据的匹配统计信息。"""
        upb = self.upb
        luhf = self.luhf

        upb_key = standardize_column_name(join_key, upb)
        luhf_key = standardize_column_name(join_key, luhf)

        if upb_key not in upb.columns or luhf_key not in luhf.columns:
            return {
                "error": f"连接键 '{join_key}' 在一个或两个数据集中不存在",
                "upb_columns": list(upb.columns[:20]),
                "luhf_columns": list(luhf.columns[:20])
            }

        upb_unique = upb[upb_key].unique().len()
        luhf_unique = luhf[luhf_key].unique().len()

        common_keys = set(upb[upb_key].to_list()) & set(luhf[luhf_key].to_list())

        return {
            "upb_total": upb.height,
            "luhf_total": luhf.height,
            "upb_unique": upb_unique,
            "luhf_unique": luhf_unique,
            "common_unique": len(common_keys),
            "match_potential_max": min(upb.height, luhf.height),
            "match_potential_min": len(common_keys)
        }
