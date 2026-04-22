"""
查询命令实现

提供多维查询碎屑锆石数据的命令行接口。
"""

import click
from typing import Optional, List, Tuple
from onedz_handler.cli.metadata import register_command, CommandMetadata
from onedz_handler.cli.validators import validate_period, validate_bbox, validate_age_range
from onedz_handler.cli.utils import echo_success, echo_error, format_list, format_age_range


# 定义命令元数据
query_metadata = CommandMetadata(
    name="query",
    group="Data Query",
    description="查询碎屑锆石数据，支持多维度过滤",
    category="data_operations",
    long_description=(
        "根据地质年代、岩石类型、地理位置、仪器类型等多个维度"
        "查询碎屑锆石数据。支持灵活的组合查询条件。"
    ),
    skill_trigger_phrases=[
        "query zircon data",
        "filter zircon by period",
        "search detrital zircon",
        "find zircon by location",
        "get zircon data",
        "filter by continent",
        "filter by age range"
    ],
    equivalent_api=(
        "handler.query(\n"
        "    periods=['Cretaceous'],\n"
        "    continent='Asia',\n"
        "    rock_class1=['detrital']\n"
        ")"
    ),
    parameters=[
        {
            "name": "--period",
            "description": "地质年代（可多选）",
            "type": "TEXT[]"
        },
        {
            "name": "--epoch",
            "description": "地质纪",
            "type": "TEXT"
        },
        {
            "name": "--rock-class",
            "description": "岩石分类（可多选）",
            "type": "TEXT[]"
        },
        {
            "name": "--region",
            "description": "地理区域",
            "type": "TEXT"
        },
        {
            "name": "--continent",
            "description": "大洲",
            "type": "TEXT"
        },
        {
            "name": "--country",
            "description": "国家/地区",
            "type": "TEXT"
        },
        {
            "name": "--bbox",
            "description": "边界框 (min_lon min_lat max_lon max_lat)",
            "type": "FLOAT FLOAT FLOAT FLOAT"
        },
        {
            "name": "--instrument",
            "description": "仪器类型（可多选）",
            "type": "TEXT[]"
        },
        {
            "name": "--age-range",
            "description": "年龄范围 (Ma)",
            "type": "FLOAT FLOAT"
        },
        {
            "name": "--formation",
            "description": "地层组名",
            "type": "TEXT"
        },
        {
            "name": "--max-records",
            "description": "最大记录数",
            "type": "INTEGER"
        },
        {
            "name": "--output / -o",
            "description": "输出文件",
            "type": "PATH"
        },
        {
            "name": "--format / -f",
            "description": "输出格式",
            "type": "csv|json|excel"
        }
    ],
    examples=[
        {
            "title": "查询亚洲白垩纪碎屑锆石",
            "user_input": "分析亚洲白垩纪碎屑锆石",
            "command": "onedz query --period Cretaceous --rock-class detrital --continent Asia -o asia.csv",
            "python_code": '''
from onedz_handler import OneDZHandler

handler = OneDZHandler()
handler.load(source="csv", table="zircon_upb")
df = handler.query(
    periods=["Cretaceous"],
    rock_class1=["detrital"],
    continent="Asia"
)
handler.export(df, "asia.csv")
print(f"✅ 查询完成: {df.height:,} 条记录")
'''
        },
        {
            "title": "查询特定年龄范围",
            "user_input": "查询100-500Ma的锆石数据",
            "command": "onedz query --age-range 100 500 -o young_zircons.csv",
            "python_code": '''
df = handler.query(age_range=(100, 500))
handler.export(df, "young_zircons.csv")
'''
        },
        {
            "title": "多条件组合查询",
            "user_input": "查询侏罗纪和白垩纪的LA-ICP-MS测试数据",
            "command": "onedz query --period Jurassic Cretaceous --instrument LA_ICP_MS -o multi_period.csv",
            "python_code": '''
df = handler.query(
    periods=["Jurassic", "Cretaceous"],
    instruments=["LA_ICP_MS"]
)
handler.export(df, "multi_period.csv")
'''
        }
    ],
    output_description=(
        "返回查询结果DataFrame，并根据需要导出到指定格式的文件。"
        "输出信息包括查询到的记录数和保存的文件路径。"
    )
)


@click.command()
@click.option(
    '--period',
    multiple=True,
    help='地质年代（可多选）如: Cretaceous, Jurassic, Triassic',
    callback=validate_period
)
@click.option(
    '--epoch',
    help='地质纪'
)
@click.option(
    '--rock-class',
    'rock_class',
    multiple=True,
    help='岩石分类（可多选）如: detrital, igneous'
)
@click.option(
    '--region',
    help='地理区域'
)
@click.option(
    '--continent',
    help='大洲如: Asia, Europe, North_America'
)
@click.option(
    '--country',
    'country_state',
    help='国家/地区'
)
@click.option(
    '--bbox',
    nargs=4,
    type=float,
    help='边界框 (min_lon min_lat max_lon max_lat)',
    callback=validate_bbox
)
@click.option(
    '--instrument',
    'instruments',
    multiple=True,
    help='仪器类型（可多选）如: LA_ICP_MS, SIMS, SHRIMP'
)
@click.option(
    '--age-range',
    nargs=2,
    type=float,
    help='年龄范围 Ma (min max)',
    callback=validate_age_range
)
@click.option(
    '--formation',
    help='地层组名'
)
@click.option(
    '--max-records',
    type=int,
    help='最大记录数限制'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='输出文件路径'
)
@click.option(
    '--format', '-f',
    'output_format',
    type=click.Choice(['csv', 'json', 'excel'], case_sensitive=False),
    help='输出格式 (根据文件扩展名自动识别)'
)
@click.pass_context
@register_command(query_metadata)
def query_cmd(
    ctx: click.Context,
    period: tuple,
    epoch: Optional[str],
    rock_class: tuple,
    region: Optional[str],
    continent: Optional[str],
    country_state: Optional[str],
    bbox: Optional[tuple],
    instruments: tuple,
    age_range: Optional[tuple],
    formation: Optional[str],
    max_records: Optional[int],
    output: Optional[str],
    output_format: Optional[str]
):
    """
    查询碎屑锆石数据

    支持多维度查询：地质年代、岩石类型、地理位置、仪器类型等。

    示例:
        # 查询亚洲白垩纪碎屑锆石
        onedz query --period Cretaceous --continent Asia -o asia.csv

        # 查询特定年龄范围
        onedz query --age-range 100 500 -o young.csv

        # 多条件查询
        onedz query --period Jurassic Cretaceous --instrument LA_ICP_MS
    """
    from onedz_handler import OneDZHandler
    import polars as pl

    # 获取或创建 Handler 实例
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

    # 构建查询参数
    query_params = {}

    if period:
        query_params['periods'] = list(period)
    if epoch:
        query_params['epoch'] = epoch
    if rock_class:
        query_params['rock_class1'] = list(rock_class)
    if region:
        query_params['region'] = region
    if continent:
        query_params['continent'] = continent
    if country_state:
        query_params['country_state'] = country_state
    if bbox:
        query_params['bbox'] = bbox
    if instruments:
        query_params['instruments'] = list(instruments)
    if age_range:
        query_params['age_range'] = age_range
    if formation:
        query_params['formation'] = formation
    if max_records:
        query_params['max_records'] = max_records

    # 如果没有任何查询条件，提示用户
    if not query_params:
        echo_error("请至少指定一个查询条件")
        echo_error("使用 --help 查看所有可用选项")
        raise click.Abort()

    # 显示查询条件
    if not ctx.obj.get('quiet'):
        click.echo("\n🔍 查询条件:")
        if period:
            click.echo(f"   地质年代: {format_list(list(period))}")
        if continent:
            click.echo(f"   大洲: {continent}")
        if rock_class:
            click.echo(f"   岩石类型: {format_list(list(rock_class))}")
        if age_range:
            click.echo(f"   年龄范围: {format_age_range(age_range)}")
        if instruments:
            click.echo(f"   仪器: {format_list(list(instruments))}")

    # 执行查询
    try:
        df = handler.query(**query_params)
    except Exception as e:
        echo_error(f"查询失败: {e}")
        raise click.Abort()

    # 显示结果
    echo_success(f"查询完成: {df.height:,} 条记录")

    # 导出数据
    if output:
        try:
            handler.export(df, output, fmt=output_format)
            echo_success(f"已保存: {output}")
        except Exception as e:
            echo_error(f"导出失败: {e}")
            raise click.Abort()

    return df
