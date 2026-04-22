"""
OneDZ Handler — 工具函数

列名标准化、类型转换、坐标修复等公共逻辑。
"""

from typing import Dict, List, Optional

import polars as pl
import numpy as np

from .config import COLUMN_ALIASES, Cols


# ──────────────────────────── 列名标准化 ─────────────────────────
def normalize_columns(df: pl.DataFrame) -> pl.DataFrame:
    """
    将 DataFrame 列名统一为 config.Cols 中定义的标准名。
    处理 CSV 和 MySQL 来源的命名差异。
    """
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


def standardize_column_name(col_name: str, df: pl.DataFrame) -> str:
    """
    标准化列名，返回在 DataFrame 中实际存在的列名

    处理 CSV/SQL 格式差异，返回标准列名或原始列名

    Parameters
    ----------
    col_name : str
        期望的列名（标准名）
    df : pl.DataFrame
        数据框

    Returns
    -------
    str
        实际存在的列名

    Examples
    --------
    >>> df = pl.DataFrame({"Ref No.": [1, 2], "Age": [100, 200]})
    >>> standardize_column_name("Ref_No.", df)
    'Ref No.'
    >>> standardize_column_name("NonExistent", df)
    'NonExistent'
    """
    # 如果列名直接存在，返回它
    if col_name in df.columns:
        return col_name

    # 检查是否是标准列名，寻找别名
    if col_name in COLUMN_ALIASES:
        for alias in COLUMN_ALIASES[col_name]:
            if alias in df.columns:
                return alias

    # 不存在，返回原始名称（调用者可以处理错误）
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
