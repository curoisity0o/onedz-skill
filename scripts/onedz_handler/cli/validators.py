"""
CLI 参数验证器

提供 Click 参数验证函数，用于验证用户输入的参数。
"""

import click
from typing import Optional, List, Tuple
from onedz_handler.config import GEO_PERIODS


def validate_period(ctx: click.Context, param: click.Parameter, value: Optional[tuple]) -> Optional[List[str]]:
    """
    验证地质年代参数

    Parameters
    ----------
    ctx : click.Context
        Click 上下文
    param : click.Parameter
        当前参数
    value : tuple or None
        用户输入的值（multiple=True 时为 tuple）

    Returns
    -------
    list or None
        验证后的年代列表

    Raises
    ------
    click.BadParameter
        如果年代无效
    """
    if value is None or len(value) == 0:
        return None

    periods = list(value)

    # 检查年代是否有效
    invalid_periods = []
    for period in periods:
        # 尝试直接匹配
        if period in GEO_PERIODS:
            continue

        # 尝试不区分大小写匹配
        found = False
        for key in GEO_PERIODS:
            if period.lower() == key.lower():
                # 自动更正大小写
                periods[periods.index(period)] = key
                found = True
                break

        if not found:
            invalid_periods.append(period)

    if invalid_periods:
        all_periods = ", ".join(sorted(GEO_PERIODS.keys()))
        raise click.BadParameter(
            f"无效的地质年代: {', '.join(invalid_periods)}\n"
            f"支持的年代: {all_periods}"
        )

    return periods


def validate_bbox(ctx: click.Context, param: click.Parameter, value: Optional[tuple]) -> Optional[Tuple[float, float, float, float]]:
    """
    验证边界框参数

    Parameters
    ----------
    ctx : click.Context
        Click 上下文
    param : click.Parameter
        当前参数
    value : tuple or None
        用户输入的值 (min_lon, min_lat, max_lon, max_lat)

    Returns
    -------
    tuple or None
        验证后的边界框元组

    Raises
    ------
    click.BadParameter
        如果边界框无效
    """
    if value is None or len(value) != 4:
        return None

    min_lon, min_lat, max_lon, max_lat = value

    # 验证经度范围 (-180 to 180)
    if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
        raise click.BadParameter(
            f"经度必须在 -180 到 180 之间，当前值: {min_lon}, {max_lon}"
        )

    # 验证纬度范围 (-90 to 90)
    if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
        raise click.BadParameter(
            f"纬度必须在 -90 到 90 之间，当前值: {min_lat}, {max_lat}"
        )

    # 验证 min < max
    if min_lon >= max_lon or min_lat >= max_lat:
        raise click.BadParameter(
            f"边界框最小值必须小于最大值，当前值: "
            f"({min_lon}, {min_lat}, {max_lon}, {max_lat})"
        )

    return (min_lon, min_lat, max_lon, max_lat)


def validate_age_range(ctx: click.Context, param: click.Parameter, value: Optional[tuple]) -> Optional[Tuple[float, float]]:
    """
    验证年龄范围参数

    Parameters
    ----------
    ctx : click.Context
        Click 上下文
    param : click.Parameter
        当前参数
    value : tuple or None
        用户输入的值 (min_age, max_age)

    Returns
    -------
    tuple or None
        验证后的年龄范围元组

    Raises
    ------
    click.BadParameter
        如果年龄范围无效
    """
    if value is None or len(value) != 2:
        return None

    min_age, max_age = value

    # 验证年龄为正数
    if min_age < 0 or max_age < 0:
        raise click.BadParameter(
            f"年龄必须为非负数，当前值: {min_age}, {max_age}"
        )

    # 验证 min < max
    if min_age >= max_age:
        raise click.BadParameter(
            f"最小年龄必须小于最大年龄，当前值: {min_age}, {max_age}"
        )

    return (min_age, max_age)


def validate_concordance(ctx: click.Context, param: click.Parameter, value: Optional[float]) -> Optional[float]:
    """
    验证谐和度参数

    Parameters
    ----------
    ctx : click.Context
        Click 上下文
    param : click.Parameter
        当前参数
    value : float or None
        用户输入的值

    Returns
    -------
    float or None
        验证后的谐和度值

    Raises
    ------
    click.BadParameter
        如果谐和度无效
    """
    if value is None:
        return None

    # 谐和度通常在 0.5 到 1.5 之间
    if not (0.0 <= value <= 2.0):
        raise click.BadParameter(
            f"谐和度应该在 0.0 到 2.0 之间，当前值: {value}"
        )

    return value


def validate_file_exists(ctx: click.Context, param: click.Parameter, value: Optional[str]) -> Optional[str]:
    """
    验证文件是否存在

    Parameters
    ----------
    ctx : click.Context
        Click 上下文
    param : click.Parameter
        当前参数
    value : str or None
        文件路径

    Returns
    -------
    str or None
        验证后的文件路径

    Raises
    ------
    click.BadParameter
        如果文件不存在
    """
    if value is None:
        return None

    from pathlib import Path
    file_path = Path(value)

    if not file_path.exists():
        raise click.BadParameter(
            f"文件不存在: {value}"
        )

    if not file_path.is_file():
        raise click.BadParameter(
            f"路径不是文件: {value}"
        )

    return value


__all__ = [
    "validate_period",
    "validate_bbox",
    "validate_age_range",
    "validate_concordance",
    "validate_file_exists",
]
