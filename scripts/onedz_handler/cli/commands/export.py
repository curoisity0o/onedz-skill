"""
导出命令实现

提供数据导出的命令行接口，支持多种格式（CSV、JSON、Excel、GeoJSON、Shapefile）。
"""

import click
from pathlib import Path
from typing import Optional
from onedz_handler.cli.metadata import register_command, CommandMetadata
from onedz_handler.cli.utils import echo_success, echo_error


# 定义命令元数据
export_metadata = CommandMetadata(
    name="export",
    group="Export",
    description="导出数据到多种格式",
    category="export",
    long_description=(
        "将锆石数据导出为多种格式，包括CSV、JSON、Excel、GeoJSON、Shapefile等。"
    ),
    skill_trigger_phrases=[
        "export data",
        "save as csv",
        "export to geojson",
        "create shapefile",
        "save to excel"
    ],
    equivalent_api="handler.export(df, filename='output.csv')",
    parameters=[
        {
            "name": "--input",
            "description": "输入文件（CSV格式）",
            "type": "PATH"
        },
        {
            "name": "--output / -o",
            "description": "输出文件（根据扩展名自动识别格式）",
            "type": "PATH"
        },
        {
            "name": "--format / -f",
            "description": "输出格式",
            "type": "csv|json|excel|geojson|shp"
        },
        {
            "name": "--columns",
            "description": "导出的列（逗号分隔）",
            "type": "TEXT"
        }
    ],
    examples=[
        {
            "title": "导出为CSV",
            "user_input": "将数据导出为CSV文件",
            "command": "onedz export --input data.csv --output result.csv",
            "python_code": '''
from onedz_handler import OneDZHandler
handler = OneDZHandler()
df = pl.read_csv("data.csv")
handler.export(df, "result.csv")
'''
        },
        {
            "title": "导出为GeoJSON（用于QGIS）",
            "user_input": "导出为GeoJSON格式用于GIS分析",
            "command": "onedz export --input data.csv --output result.geojson",
            "python_code": '''
handler.export(df, "result.geojson", fmt="geojson")
'''
        },
        {
            "title": "导出特定列",
            "user_input": "只导出年龄和坐标列",
            "command": "onedz export --input data.csv --columns 'Best Age,Latitude,Longitude' -o subset.csv",
            "python_code": '''
cols = ['Best Age', 'Latitude', 'Longitude']
handler.export(df.select(cols), "subset.csv")
'''
        }
    ],
    output_description=(
        "将数据导出为指定格式的文件，支持自动格式识别。"
    )
)


@click.command()
@click.option(
    '--input',
    type=click.Path(exists=True),
    help='输入文件（CSV格式）'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    required=True,
    help='输出文件（根据扩展名自动识别格式）'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['csv', 'json', 'excel', 'geojson', 'shp'],
                      case_sensitive=False),
    help='输出格式（根据文件扩展名自动识别）'
)
@click.option(
    '--columns',
    help='导出的列（逗号分隔，如: Best Age,Latitude,Longitude）'
)
@click.pass_context
@register_command(export_metadata)
def export_cmd(
    ctx: click.Context,
    input: Optional[str],
    output: str,
    format: Optional[str],
    columns: Optional[str]
):
    """
    导出数据到多种格式

    支持的格式：
    - CSV: .csv
    - JSON: .json
    - Excel: .xlsx, .xls
    - GeoJSON: .geojson（用于QGIS/ArcGIS）
    - Shapefile: .shp（用于GIS软件）

    示例:
        # 导出为CSV
        onedz export --input data.csv --output result.csv

        # 导出为GeoJSON
        onedz export --input data.csv --output result.geojson

        # 导出特定列
        onedz export --input data.csv --columns 'Best Age,Latitude,Longitude' -o subset.csv
    """
    from onedz_handler import OneDZHandler
    import polars as pl

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
            raise click.Abort()

    # 加载数据
    if input:
        try:
            df = pl.read_csv(input)
        except Exception as e:
            echo_error(f"读取文件失败: {e}")
            raise click.Abort()
    else:
        df = handler.data
        if df is None or df.height == 0:
            echo_error("没有可用的数据，请使用 --input 指定输入文件")
            raise click.Abort()

    # 选择列
    if columns:
        try:
            col_list = [col.strip() for col in columns.split(',')]
            # 检查列是否存在
            missing_cols = set(col_list) - set(df.columns)
            if missing_cols:
                echo_error(f"数据中未找到列: {', '.join(missing_cols)}")
                raise click.Abort()
            df = df.select(col_list)
            click.echo(f"\n📊 导出 {len(col_list)} 列")
        except Exception as e:
            echo_error(f"列选择失败: {e}")
            raise click.Abort()
    else:
        click.echo(f"\n📊 导出 {df.height} 行 × {df.width} 列")

    # 自动识别格式
    if format is None:
        ext = Path(output).suffix.lower()
        format_map = {
            '.csv': 'csv',
            '.json': 'json',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.geojson': 'geojson',
            '.shp': 'shp'
        }
        format = format_map.get(ext, 'csv')

    click.echo(f"   格式: {format.upper()}")
    click.echo(f"   输出: {output}")

    try:
        result_path = handler.export(df, output, fmt=format)
        echo_success(f"导出成功: {result_path}")
    except Exception as e:
        echo_error(f"导出失败: {e}")
        raise click.Abort()

    return result_path
