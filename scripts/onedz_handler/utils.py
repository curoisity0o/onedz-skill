"""
OneDZ Handler — 工具函数

列名标准化、类型转换、坐标修复等公共逻辑。
"""

from typing import Dict, List, Optional

import polars as pl
import numpy as np

from .config import COLUMN_ALIASES, Cols


# ──────────────────────────── 列名标准化 ─────────────────────────
def normalize_columns(df: pl.DataFrame, adapter=None, is_luhf: bool = False) -> pl.DataFrame:
    """
    将 DataFrame 列名统一为 config.Cols 中定义的标准名。
    处理 CSV 和 MySQL 来源的命名差异。

    Parameters
    ----------
    df : pl.DataFrame
    adapter : DatasetAdapter, optional
        适配器实例，优先使用 adapter 的映射
    is_luhf : bool
        是否为 Lu-Hf 数据（需要额外的列名映射）
    """
    if adapter is not None:
        return adapter.normalize(df, is_luhf=is_luhf)

    # 向后兼容：无 adapter 时使用旧逻辑
    rename_map: Dict[str, str] = {}
    existing = set(df.columns)

    for std_name, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in existing and alias != std_name:
                rename_map[alias] = std_name
                break

    if rename_map:
        df = df.rename(rename_map)
    return df


def standardize_column_name(col_name: str, df, adapter=None) -> str:
    """
    标准化列名，返回在 DataFrame/LazyFrame 中实际存在的列名。

    Parameters
    ----------
    col_name : str
        期望的列名（标准名）
    df : pl.DataFrame | pl.LazyFrame
        数据框
    adapter : DatasetAdapter, optional
        适配器实例
    """
    # 获取列名列表
    if isinstance(df, pl.DataFrame):
        columns = df.columns
    elif isinstance(df, pl.LazyFrame):
        columns = df.collect_schema().names()
    else:
        columns = list(df.columns) if hasattr(df, 'columns') else []

    if col_name in columns:
        return col_name

    # 使用 adapter 的反向映射
    if adapter is not None and adapter.is_active:
        for ext, std in adapter._column_rename_map.items():
            if std == col_name and ext in columns:
                return ext
        for ext, std in adapter._luhf_rename_map.items():
            if std == col_name and ext in columns:
                return ext

    # 向后兼容：COLUMN_ALIASES
    if col_name in COLUMN_ALIASES:
        for alias in COLUMN_ALIASES[col_name]:
            if alias in columns:
                return alias

    return col_name


# ──────────────────────────── 类型安全读取 ───────────────────────
def safe_get_column(
    df: pl.DataFrame,
    col: str,
    *,
    default=None,
) -> Optional[pl.Series]:
    """安全获取列，不存在时返回 default。"""
    try:
        return df[col]
    except (pl.ColumnNotFoundError, KeyError):
        return default


def coerce_numeric(
    df: pl.DataFrame,
    cols: List[str],
) -> pl.DataFrame:
    """将指定列强制转为 Float64 类型，非法值变 null。"""
    for c in cols:
        if c in df.columns:
            df = df.with_columns(pl.col(c).cast(pl.Float64, strict=False).alias(c))
    return df


# ──────────────────────────── 坐标修复 ───────────────────────────
def estimate_missing_coordinates(df: pl.DataFrame) -> pl.DataFrame:
    """
    对缺失坐标的记录，基于同一 Formation / Locality 内已有坐标的中位数进行填充。

    若 Formation 级别无可用坐标，再向上回退到 Major_Geographic_Geologic_Description。
    仅修复 Lat/Lon 同时缺失的行，保留部分缺失标记。
    """
    lat_col = Cols.LATITUDE
    lon_col = Cols.LONGITUDE
    if lat_col not in df.columns or lon_col not in df.columns:
        return df

    df = df.with_columns([
        pl.col(lat_col).cast(pl.Float64, strict=False),
        pl.col(lon_col).cast(pl.Float64, strict=False),
    ])

    both_null = pl.col(lat_col).is_null() & pl.col(lon_col).is_null()
    needs_fix = df.filter(both_null)
    if needs_fix.is_empty():
        return df

    has_coords = df.filter(~both_null)
    if has_coords.is_empty():
        return df

    # 按 Formation 取中位数
    group_col = Cols.FORMATION if Cols.FORMATION in df.columns else None
    if group_col is None:
        # 退而用 Major_Geo_Desc
        group_col = Cols.MAJOR_GEO_DESC if Cols.MAJOR_GEO_DESC in df.columns else None

    if group_col is not None:
        median_coords = (
            has_coords.group_by(group_col)
            .agg([
                pl.col(lat_col).median().alias("_est_lat"),
                pl.col(lon_col).median().alias("_est_lon"),
            ])
        )
        needs_fix = needs_fix.drop(["_est_lat", "_est_lon"], strict=False).join(
            median_coords, on=group_col, how="left"
        )
        needs_fix = needs_fix.with_columns([
            pl.col("_est_lat").alias(lat_col),
            pl.col("_est_lon").alias(lon_col),
        ]).drop(["_est_lat", "_est_lon"])
    else:
        # 全局中位数兜底
        g_lat = has_coords[lat_col].median()
        g_lon = has_coords[lon_col].median()
        needs_fix = needs_fix.with_columns([
            pl.lit(g_lat).alias(lat_col),
            pl.lit(g_lon).alias(lon_col),
        ])

    # 合并回原 df
    result = pl.concat([df.filter(~both_null), needs_fix], how="diagonal_relaxed")
    return result


# ──────────────────────── 地质年代查询辅助 ───────────────────────
def period_to_age_range(period: str) -> Optional[tuple]:
    """将地质年代名称转为 (min_age, max_age) 范围 (Ma)。"""
    from .config import GEO_PERIODS

    return GEO_PERIODS.get(period)
