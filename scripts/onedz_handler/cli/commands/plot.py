"""
绘图命令实现

提供可视化绘图的命令行接口，支持KDE、PDP、εHf、TDM等多种图表。
"""

import click
from pathlib import Path
from typing import Optional, Tuple
from onedz_handler.cli.metadata import register_command, CommandMetadata
from onedz_handler.cli.validators import validate_age_range
from onedz_handler.cli.utils import echo_success, echo_error


# 定义命令元数据
plot_metadata = CommandMetadata(
    name="plot",
    group="Visualization",
    description="创建可视化图表",
    category="visualization",
    long_description=(
        "创建各种类型的锆石数据可视化图表，包括年龄分布图（KDE/PDP）、"
        "εHf演化图、TDM分布图等。Phase 5 新增岩石类型统计图、地理分布图、"
        "时间分布图等统计可视化功能。"
    ),
    skill_trigger_phrases=[
        "create plot",
        "generate kde plot",
        "plot age distribution",
        "create visualization",
        "plot epsilon hf",
        "plot tdm"
    ],
    equivalent_api=(
        "handler.plot_age(df, mode='kde')\n"
        "handler.plot_epsilon_hf(df)\n"
        "handler.plot_tdm(df)"
    ),
    parameters=[
        {
            "name": "--input",
            "description": "输入文件（CSV格式）",
            "type": "PATH"
        },
        {
            "name": "--plot-type",
            "description": "图表类型",
            "type": "kde|pdp|multi_kde|epsilon_hf|epsilon_hf_dist|tdm|rock_type_stats|geo_distribution|temporal_distribution"
        },
        {
            "name": "--age-col",
            "description": "年龄列名",
            "type": "TEXT"
        },
        {
            "name": "--mode",
            "description": "KDE/PDP模式",
            "type": "kde|pdp"
        },
        {
            "name": "--age-range",
            "description": "年龄范围 Ma (min max)",
            "type": "FLOAT FLOAT"
        },
        {
            "name": "--bandwidth",
            "description": "KDE带宽",
            "type": "FLOAT"
        },
        {
            "name": "--show-peaks",
            "description": "显示峰值标注"
        },
        {
            "name": "--color-by",
            "description": "分组着色列名",
            "type": "TEXT"
        },
        {
            "name": "--model",
            "description": "TDM模型类型",
            "type": "dm1|dm2"
        },
        {
            "name": "--output / -o",
            "description": "输出图片文件",
            "type": "PATH"
        },
        {
            "name": "--format",
            "description": "图片格式",
            "type": "png|pdf|svg"
        },
        {
            "name": "--dpi",
            "description": "分辨率",
            "type": "INTEGER"
        },
        {
            "name": "--class-level",
            "description": "岩石分类级别（Class1/Class2/Class3）",
            "type": "Class1|Class2|Class3"
        },
        {
            "name": "--geo-level",
            "description": "地理级别（continent/major/minor/country/formation）",
            "type": "continent|major|minor|country|formation"
        },
        {
            "name": "--top-n",
            "description": "显示前N个类别",
            "type": "INTEGER"
        },
        {
            "name": "--plot-format",
            "description": "图表格式（bar/pie）",
            "type": "bar|pie"
        }
    ],
    examples=[
        {
            "title": "创建KDE年龄分布图",
            "user_input": "创建锆石年龄的KDE分布图",
            "command": "onedz plot --input data.csv --plot-type kde --age-range 0 3000 -o kde.png",
            "python_code": '''
from onedz_handler import OneDZHandler

handler = OneDZHandler()
df = pl.read_csv("data.csv")
fig = handler.plot_age(df, mode="kde", age_range=(0, 3000), save="kde.png")
'''
        },
        {
            "title": "创建εHf演化图",
            "user_input": "绘制εHf随年龄的演化图",
            "command": "onedz plot --input data.csv --plot-type epsilon_hf --color-by Continent -o epsilon.png",
            "python_code": '''
df_computed = handler.compute_epsilon_hf(df_joined)
fig = handler.plot_epsilon_hf(df_computed, color_by="Continent", save="epsilon.png")
'''
        },
        {
            "title": "创建TDM分布图",
            "user_input": "绘制TDM模型年龄分布",
            "command": "onedz plot --input data.csv --plot-type tdm --model dm2 -o tdm.png",
            "python_code": '''
fig = handler.plot_tdm(df_computed, model="dm2", save="tdm.png")
'''
        }
    ],
    output_description=(
        "生成高质量的科研图表，保存为指定格式（PNG/PDF/SVG）。"
    )
)


@click.command()
@click.option(
    '--input',
    type=click.Path(exists=True),
    help='输入文件（CSV格式）'
)
@click.option(
    '--plot-type',
    type=click.Choice(['kde', 'pdp', 'multi_kde', 'epsilon_hf', 'epsilon_hf_dist', 'tdm',
                       'rock_type_stats', 'geo_distribution', 'temporal_distribution'],
                      case_sensitive=False),
    default='kde',
    help='图表类型（默认: kde）'
)
@click.option(
    '--age-col',
    default='Best Age',
    help='年龄列名（默认: Best Age）'
)
@click.option(
    '--mode',
    type=click.Choice(['kde', 'pdp'], case_sensitive=False),
    default='kde',
    help='KDE/PDP模式（默认: kde）'
)
@click.option(
    '--age-range',
    nargs=2,
    type=float,
    default=(0, 4000),
    help='年龄范围 Ma (min max，默认: 0 4000)',
    callback=validate_age_range
)
@click.option(
    '--bandwidth',
    type=float,
    help='KDE带宽（None=自适应）'
)
@click.option(
    '--show-peaks',
    is_flag=True,
    help='显示峰值标注'
)
@click.option(
    '--color-by',
    help='分组着色列名（用于epsilon_hf）'
)
@click.option(
    '--model',
    type=click.Choice(['dm1', 'dm2'], case_sensitive=False),
    default='dm2',
    help='TDM模型类型（默认: dm2）'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    required=True,
    help='输出图片文件'
)
@click.option(
    '--format',
    type=click.Choice(['png', 'pdf', 'svg'], case_sensitive=False),
    help='图片格式（根据文件扩展名自动识别）'
)
@click.option(
    '--dpi',
    type=int,
    default=150,
    help='分辨率（默认: 150）'
)
@click.option(
    '--class-level',
    type=click.Choice(['Class1', 'Class2', 'Class3'], case_sensitive=False),
    default='Class1',
    help='岩石分类级别（默认: Class1）'
)
@click.option(
    '--geo-level',
    type=click.Choice(['continent', 'major', 'minor', 'country', 'formation'],
                      case_sensitive=False),
    default='continent',
    help='地理级别（默认: continent）'
)
@click.option(
    '--top-n',
    type=int,
    default=15,
    help='显示前N个类别（默认: 15）'
)
@click.option(
    '--plot-format',
    type=click.Choice(['bar', 'pie'], case_sensitive=False),
    default='bar',
    help='图表格式（默认: bar）'
)
@click.pass_context
@register_command(plot_metadata)
def plot_cmd(
    ctx: click.Context,
    input: Optional[str],
    plot_type: str,
    age_col: str,
    mode: str,
    age_range: Tuple[float, float],
    bandwidth: Optional[float],
    show_peaks: bool,
    color_by: Optional[str],
    model: str,
    output: str,
    format: Optional[str],
    dpi: int,
    class_level: str,
    geo_level: str,
    top_n: int,
    plot_format: str
):
    """
    创建可视化图表

    支持多种图表类型：
    - kde/pdp: 年龄概率密度图
    - epsilon_hf: εHf(t) 演化图
    - epsilon_hf_dist: εHf(t) 分布图
    - tdm: TDM 模型年龄分布图
    - rock_type_stats: 岩石类型统计图（Phase 5）
    - geo_distribution: 地理分布图（Phase 5）
    - temporal_distribution: 时间分布图（Phase 5）

    示例:
        # KDE图
        onedz plot --input data.csv --plot-type kde -o kde.png

        # εHf演化图
        onedz plot --input data.csv --plot-type epsilon_hf -o epsilon.png

        # TDM分布图
        onedz plot --input data.csv --plot-type tdm -o tdm.png

        # 岩石类型统计图（Phase 5）
        onedz plot --input data.csv --plot-type rock_type_stats --class-level Class1 -o rock.png

        # 地理分布图（Phase 5）
        onedz plot --input data.csv --plot-type geo_distribution --geo-level continent -o geo.png

        # 时间分布图（Phase 5）
        onedz plot --input data.csv --plot-type temporal_distribution -o temporal.png
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

    click.echo(f"\n🎨 创建图表: {plot_type}")

    try:
        if plot_type in ['kde', 'pdp']:
            # 年龄分布图
            fig = handler.plot_age(
                df,
                age_col=age_col,
                mode=mode,
                bandwidth=bandwidth,
                age_range=age_range,
                show_peaks=show_peaks,
                save=output
            )
            click.echo(f"   类型: {mode.upper()} 年龄分布")
            click.echo(f"   年龄范围: {age_range[0]:.0f} - {age_range[1]:.0f} Ma")
            if show_peaks:
                click.echo(f"   峰值标注: ✓")

        elif plot_type == 'epsilon_hf':
            # εHf(t) 演化图
            fig = handler.plot_epsilon_hf(
                df,
                age_col=age_col,
                color_by=color_by,
                save=output
            )
            click.echo(f"   类型: εHf(t) 演化图")
            if color_by:
                click.echo(f"   分组: {color_by}")

        elif plot_type == 'epsilon_hf_dist':
            # εHf(t) 分布图
            fig = handler.plot_epsilon_hf_distribution(
                df,
                save=output
            )
            click.echo(f"   类型: εHf(t) 分布图")

        elif plot_type == 'tdm':
            # TDM 分布图
            tdm_col = f"TDM_{model.upper()}"
            fig = handler.plot_tdm(
                df,
                tdm_col=tdm_col,
                save=output
            )
            click.echo(f"   类型: TDM{model.upper()} 分布图")

        elif plot_type == 'rock_type_stats':
            # 岩石类型统计图（Phase 5）
            stats = handler.viz.plot_rock_type_statistics(
                df,
                class_level=class_level,
                plot_type=plot_format,
                top_n=top_n,
                save=output
            )
            click.echo(f"   类型: 岩石类型统计图")
            click.echo(f"   分类级别: {class_level}")
            click.echo(f"   图表格式: {plot_format}")
            click.echo(f"   显示前: {top_n} 个")

        elif plot_type == 'geo_distribution':
            # 地理分布图（Phase 5）
            stats = handler.viz.plot_geographic_distribution(
                df,
                geo_level=geo_level,
                top_n=top_n,
                save=output
            )
            click.echo(f"   类型: 地理分布图")
            click.echo(f"   地理级别: {geo_level}")
            click.echo(f"   显示前: {top_n} 个")

        elif plot_type == 'temporal_distribution':
            # 时间分布图（Phase 5）
            stats = handler.viz.plot_temporal_distribution(
                df,
                save=output
            )
            click.echo(f"   类型: 时间分布图")

        echo_success(f"图表已保存: {output}")

    except Exception as e:
        echo_error(f"绘图失败: {e}")
        raise click.Abort()

    return output
