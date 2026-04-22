"""
CLI 工具函数

提供 CLI 命令常用的辅助函数，包括进度显示、统计信息输出等。
"""

from typing import Optional
import click
from pathlib import Path


def show_progress(iterable, desc: str = "处理中", quiet: bool = False):
    """
    显示进度条

    Parameters
    ----------
    iterable : 可迭代对象
        要迭代的对象
    desc : str
        进度条描述
    quiet : bool
        是否静默模式（不显示进度条）

    Returns
    -------
    可迭代对象
        可能包装了 tqdm 进度条的对象
    """
    if quiet:
        return iterable

    try:
        from tqdm import tqdm
        return tqdm(iterable, desc=desc)
    except ImportError:
        # 如果没有 tqdm，直接返回原始对象
        return iterable


def show_stats(before: int, after: int, operation: str = "处理"):
    """
    显示处理统计信息

    Parameters
    ----------
    before : int
        处理前的记录数
    after : int
        处理后的记录数
    operation : str
        操作名称
    """
    retention = (after / before * 100) if before > 0 else 0

    click.echo(f"""
📊 {operation}结果:
   原始记录: {before:,}
   处理后: {after:,}
   保留率: {retention:.1f}%
""")


def validate_output_path(path: Optional[str]) -> Optional[Path]:
    """
    验证并创建输出路径

    Parameters
    ----------
    path : str or None
        输出路径

    Returns
    -------
    Path or None
        验证后的路径对象
    """
    if path is None:
        return None

    output_path = Path(path)

    # 如果路径是目录，确保目录存在
    if output_path.suffix == "":
        # 这是一个目录路径
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        # 这是一个文件路径，确保父目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

    return output_path


def format_age_range(age_range: tuple) -> str:
    """
    格式化年龄范围显示

    Parameters
    ----------
    age_range : tuple
        (min_age, max_age) 元组

    Returns
    -------
    str
        格式化的字符串
    """
    if age_range is None:
        return "未限制"
    return f"{age_range[0]:.1f} - {age_range[1]:.1f} Ma"


def format_list(items: list, max_items: int = 5) -> str:
    """
    格式化列表显示

    Parameters
    ----------
    items : list
        要显示的列表
    max_items : int
        最多显示的项数

    Returns
    -------
    str
        格式化的字符串
    """
    if not items:
        return "无"

    if len(items) <= max_items:
        return ", ".join(str(item) for item in items)

    return ", ".join(str(item) for item in items[:max_items]) + f" ... (共 {len(items)} 项)"


def echo_success(message: str):
    """显示成功消息"""
    click.echo(f"✅ {message}")


def echo_error(message: str):
    """显示错误消息"""
    click.echo(f"❌ {message}", err=True)


def echo_warning(message: str):
    """显示警告消息"""
    click.echo(f"⚠️  {message}", err=True)


def echo_info(message: str):
    """显示信息消息"""
    click.echo(f"ℹ️  {message}")


def echo_step(step: int, total: int, message: str):
    """显示步骤消息"""
    click.echo(f"\n[{step}/{total}] {message}")


__all__ = [
    "show_progress",
    "show_stats",
    "validate_output_path",
    "format_age_range",
    "format_list",
    "echo_success",
    "echo_error",
    "echo_warning",
    "echo_info",
    "echo_step",
]
