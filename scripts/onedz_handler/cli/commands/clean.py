"""
清洗命令实现

提供数据清洗和质量控制的命令行接口。
"""

import click
from pathlib import Path
from typing import Optional
import polars as pl
from onedz_handler.cli.metadata import register_command, CommandMetadata
from onedz_handler.cli.validators import validate_concordance, validate_age_range, validate_file_exists
from onedz_handler.cli.utils import echo_success, echo_error, show_stats


# 定义命令元数据
clean_metadata = CommandMetadata(
    name="clean",
    group="Data Quality",
    description="数据清洗和质量控制",
    category="data_operations",
    long_description=(
        "对锆石数据进行科学级质量控制，包括计算最佳年龄、"
        "谐和度过滤、误差标准化等操作。"
    ),
    skill_trigger_phrases=[
        "clean zircon data",
        "filter concordance",
        "quality control",
        "remove discordant grains",
        "standardize errors"
    ],
    equivalent_api=(
        "handler.clean(\n"
        "    df,\n"
        "    compute_best_age=True,\n"
        "    filter_concordance=True,\n"
        "    concordance_min=0.90,\n"
        "    concordance_max=1.10\n"
        ")"
    ),
    parameters=[
        {
            "name": "--input",
            "description": "输入文件（CSV格式）",
            "type": "PATH"
        },
        {
            "name": "--no-best-age",
            "description": "不计算最佳年龄",
            "type": "flag"
        },
        {
            "name": "--no-concordance",
            "description": "不过滤谐和度",
            "type": "flag"
        },
        {
            "name": "--concordance-min",
            "description": "最小谐和度（默认: 0.90）",
            "type": "FLOAT"
        },
        {
            "name": "--concordance-max",
            "description": "最大谐和度（默认: 1.10）",
            "type": "FLOAT"
        },
        {
            "name": "--no-standardize",
            "description": "不标准化误差",
            "type": "flag"
        },
        {
            "name": "--target-sigma",
            "description": "目标标准差（1或2）",
            "type": "INTEGER"
        },
        {
            "name": "--keep-null-ages",
            "description": "保留空年龄",
            "type": "flag"
        },
        {
            "name": "--age-range",
            "description": "年龄范围过滤 (Ma)",
            "type": "FLOAT FLOAT"
        },
        {
            "name": "--output / -o",
            "description": "输出文件",
            "type": "PATH"
        },
        {
            "name": "--summary",
            "description": "显示清洗摘要",
            "type": "flag"
        }
    ],
    examples=[
        {
            "title": "基础数据清洗",
            "user_input": "清洗数据，使用默认的谐和度过滤",
            "command": "onedz clean --input raw.csv --concordance-min 0.90 -o clean.csv",
            "python_code": '''
from onedz_handler import OneDZHandler

handler = OneDZHandler()
df_raw = pl.read_csv("raw.csv")
df_clean = handler.clean(
    df_raw,
    compute_best_age=True,
    filter_concordance=True,
    concordance_min=0.90,
    concordance_max=1.10
)
handler.export(df_clean, "clean.csv")
print(f"✅ 清洗完成: {df_raw.height} -> {df_clean.height}")
'''
        },
        {
            "title": "严格质量控制",
            "user_input": "严格清洗数据，95%谐和度",
            "command": "onedz clean --input raw.csv --concordance-min 0.95 --concordance-max 1.05 -o strict_clean.csv",
            "python_code": '''
df_clean = handler.clean(
    df_raw,
    concordance_min=0.95,
    concordance_max=1.05
)
'''
        },
        {
            "title": "查看清洗摘要",
            "user_input": "查看清洗效果统计",
            "command": "onedz clean --input raw.csv --summary",
            "python_code": '''
df_clean = handler.clean(df_raw)
# 显示统计信息
print(f"原始记录: {df_raw.height}")
print(f"清洗后: {df_clean.height}")
print(f"保留率: {df_clean.height/df_raw.height*100:.1f}%")
'''
        }
    ],
    output_description=(
        "返回清洗后的DataFrame，显示清洗前后的统计信息。"
        "如果指定 --summary，会显示详细的清洗摘要。"
    )
)


@click.command()
@click.option(
    '--input',
    type=click.Path(exists=True),
    help='输入文件（CSV格式）'
)
@click.option(
    '--no-best-age',
    is_flag=True,
    help='不计算最佳年龄'
)
@click.option(
    '--no-concordance',
    is_flag=True,
    help='不过滤谐和度'
)
@click.option(
    '--concordance-min',
    type=float,
    default=0.90,
    callback=validate_concordance,
    help='最小谐和度（默认: 0.90）'
)
@click.option(
    '--concordance-max',
    type=float,
    default=1.10,
    callback=validate_concordance,
    help='最大谐和度（默认: 1.10）'
)
@click.option(
    '--no-standardize',
    is_flag=True,
    help='不标准化误差'
)
@click.option(
    '--target-sigma',
    type=click.Choice(['1', '2']),
    default='1',
    help='目标标准差（1或2，默认: 1）'
)
@click.option(
    '--keep-null-ages',
    is_flag=True,
    help='保留空年龄'
)
@click.option(
    '--age-range',
    nargs=2,
    type=float,
    help='年龄范围过滤 Ma (min max)',
    callback=validate_age_range
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='输出文件路径'
)
@click.option(
    '--summary',
    is_flag=True,
    help='显示清洗摘要'
)
@click.pass_context
@register_command(clean_metadata)
def clean_cmd(
    ctx: click.Context,
    input: Optional[str],
    no_best_age: bool,
    no_concordance: bool,
    concordance_min: float,
    concordance_max: float,
    no_standardize: bool,
    target_sigma: str,
    keep_null_ages: bool,
    age_range: Optional[tuple],
    output: Optional[str],
    summary: bool
):
    """
    数据清洗和质量控制

    执行科学级数据清洗，包括：
    - 计算最佳年龄（自适应选择 ²⁰⁶Pb/²³⁸U 或 ²⁰⁷Pb/²⁰⁶Pb）
    - 谐和度过滤（默认 90-110%）
    - 误差标准化（统一为 1σ 或 2σ）
    - 移除空年龄
    - 年龄范围过滤

    示例:
        # 基础清洗
        onedz clean --input raw.csv -o clean.csv

        # 严格清洗
        onedz clean --input raw.csv --concordance-min 0.95 -o clean.csv

        # 查看摘要
        onedz clean --input raw.csv --summary
    """
    from onedz_handler import OneDZHandler

    # 获取 Handler 实例
    handler = ctx.obj.get('handler')
    csv_dir = ctx.obj.get('csv_dir')

    if handler is None:
        try:
            handler = OneDZHandler()
            handler.load(source="csv", table="zircon_upb", csv_dir=csv_dir)
            ctx.obj['handler'] = handler
        except Exception as e:
            echo_error(f"数据加载失败: {e}")
            if csv_dir is None:
                echo_error("请使用 --csv-dir 指定数据目录")
            raise click.Abort()

    # 确定输入数据
    if input:
        # 从文件加载
        try:
            df = pl.read_csv(input)
        except Exception as e:
            echo_error(f"读取文件失败: {e}")
            raise click.Abort()
    else:
        # 使用已加载的数据
        df = handler.data
        if df is None or df.height == 0:
            echo_error("没有可用的数据，请使用 --input 指定输入文件")
            raise click.Abort()

    # 记录清洗前的记录数
    n_before = df.height

    # 构建清洗参数
    clean_params = {
        'compute_best_age': not no_best_age,
        'filter_concordance': not no_concordance,
        'standardize_errors': not no_standardize,
        'target_sigma': int(target_sigma),
        'remove_null_ages': not keep_null_ages,
    }

    # 添加可选参数
    if not no_concordance:
        clean_params['concordance_min'] = concordance_min
        clean_params['concordance_max'] = concordance_max

    if age_range:
        clean_params['age_range'] = age_range

    # 显示清洗条件
    if not ctx.obj.get('quiet'):
        click.echo("\n🧹 数据清洗:")

        if clean_params['compute_best_age']:
            click.echo("   ✓ 计算最佳年龄（自适应选择）")

        if clean_params['filter_concordance']:
            click.echo(f"   ✓ 谐和度过滤: {concordance_min*100:.0f}% - {concordance_max*100:.0f}%")

        if clean_params['standardize_errors']:
            click.echo(f"   ✓ 误差标准化: {target_sigma}σ")

        if clean_params['remove_null_ages']:
            click.echo("   ✓ 移除空年龄")

        if age_range:
            click.echo(f"   ✓ 年龄范围: {age_range[0]:.1f} - {age_range[1]:.1f} Ma")

    # 执行清洗
    try:
        df_clean = handler.clean(df, **clean_params)
    except Exception as e:
        echo_error(f"清洗失败: {e}")
        raise click.Abort()

    # 显示统计信息
    n_after = df_clean.height
    show_stats(n_before, n_after, "清洗")

    # 显示详细摘要
    if summary or ctx.obj.get('verbose'):
        click.echo("\n📋 详细统计:")

        # 检查可用的列
        if "Best Age" in df_clean.columns:
            ages = df_clean["Best Age"].drop_nulls()
            if len(ages) > 0:
                click.echo(f"   年龄统计:")
                click.echo(f"     有效年龄数: {len(ages):,}")
                click.echo(f"     平均年龄: {ages.mean():.1f} Ma")
                click.echo(f"     中位数: {ages.median():.1f} Ma")
                click.echo(f"     年龄范围: {ages.min():.1f} - {ages.max():.1f} Ma")

        # 检查岩石类型分布
        if "Class-1 Rock Type" in df_clean.columns:
            rock_counts = df_clean["Class-1 Rock Type"].value_counts()
            click.echo(f"\n   岩石类型分布:")
            for row in rock_counts.iter_rows(named=True):
                click.echo(f"     {row['Class-1 Rock Type']}: {row['count']:,}")

    # 导出数据
    if output:
        try:
            handler.export(df_clean, output)
            echo_success(f"已保存: {output}")
        except Exception as e:
            echo_error(f"导出失败: {e}")
            raise click.Abort()

    return df_clean
