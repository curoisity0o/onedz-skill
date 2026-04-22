"""
信息命令实现

提供数据集信息查询和统计的命令行接口。
"""

import click
from onedz_handler.cli.metadata import register_command, CommandMetadata
from onedz_handler.cli.utils import echo_success, echo_error


# 定义命令元数据
info_metadata = CommandMetadata(
    name="info",
    group="Information",
    description="显示数据集信息和统计",
    category="information",
    long_description=(
        "显示当前加载的 OneDZ 数据集的概览信息，包括记录数、"
        "列数、年龄统计、岩石类型分布等。"
    ),
    skill_trigger_phrases=[
        "show dataset info",
        "data summary",
        "database statistics",
        "show records count",
        "what data is available"
    ],
    equivalent_api="handler.info()",
    parameters=[
        {
            "name": "--detailed",
            "description": "显示详细信息",
            "type": "flag"
        }
    ],
    examples=[
        {
            "title": "查看数据集概览",
            "user_input": "显示数据集信息",
            "command": "onedz info",
            "python_code": '''
from onedz_handler import OneDZHandler

handler = OneDZHandler()
handler.load(source="csv", table="zircon_upb")
info = handler.info()
print(f"总记录数: {info['total_records']:,}")
print(f"总列数: {info['total_columns']}")
'''
        },
        {
            "title": "查看详细信息",
            "user_input": "显示数据集的详细统计",
            "command": "onedz info --detailed",
            "python_code": '''
info = handler.info()
if 'age_stats' in info:
    stats = info['age_stats']
    print(f"平均年龄: {stats['mean']:.1f} Ma")
    print(f"年龄范围: {stats['min']:.1f} - {stats['max']:.1f} Ma")
'''
        }
    ],
    output_description=(
        "显示数据集的统计信息，包括记录数、列数、年龄统计、"
        "岩石类型分布等。"
    )
)


@click.command()
@click.option(
    '--detailed',
    is_flag=True,
    help='显示详细信息'
)
@click.pass_context
@register_command(info_metadata)
def info_cmd(ctx: click.Context, detailed: bool):
    """
    显示数据集信息

    展示当前加载的 OneDZ 数据集的统计信息。

    示例:
        # 查看概览
        onedz info

        # 查看详细信息
        onedz info --detailed
    """
    from onedz_handler import OneDZHandler

    csv_dir = ctx.obj.get('csv_dir')

    click.echo("📦 OneDZ Handler 数据集信息\n")

    try:
        handler = OneDZHandler()
        handler.load(source="csv", table="zircon_upb", csv_dir=csv_dir)

        info = handler.info()

        # 基础信息
        click.echo(f"总记录数: {info['total_records']:,}")
        click.echo(f"总列数: {info['total_columns']}")

        # 年龄统计
        if 'age_stats' in info:
            stats = info['age_stats']
            click.echo(f"\n📊 年龄统计:")
            click.echo(f"  有效年龄数: {stats['n_valid']:,}")
            if stats['min'] is not None:
                click.echo(f"  年龄范围: {stats['min']:.1f} - {stats['max']:.1f} Ma")
                click.echo(f"  平均年龄: {stats['mean']:.1f} Ma")
                click.echo(f"  中位数: {stats['median']:.1f} Ma")
                click.echo(f"  标准差: {stats['std']:.1f} Ma")

        # 详细信息
        if detailed:
            # 岩石类型分布
            if 'class-1_rock_type_counts' in info:
                click.echo(f"\n🪨 岩石类型分布:")
                for item in info['class-1_rock_type_counts'][:10]:
                    rock_type = item['Class-1 Rock Type']
                    count = item['count']
                    click.echo(f"  {rock_type}: {count:,}")

            # 地理分布
            if 'continent_counts' in info:
                click.echo(f"\n🌍 地理分布（按大洲）:")
                for item in info['continent_counts'][:10]:
                    continent = item['Continent']
                    count = item['count']
                    click.echo(f"  {continent}: {count:,}")

        echo_success("数据加载成功")

    except Exception as e:
        echo_error(f"无法加载数据: {e}")
        if csv_dir is None:
            echo_error("请使用 --csv-dir 指定数据目录")
        raise click.Abort()
