"""
Lu-Hf 同位素分析命令组实现

提供Lu-Hf同位素分析的命令行接口，包括数据连接、εHf计算、可视化等。
"""

import click
from pathlib import Path
from typing import Optional
from onedz_handler.cli.metadata import register_command, CommandMetadata
from onedz_handler.cli.utils import echo_success, echo_error


# ──────────────────────────── join 子命令 ────────────────────────────

join_metadata = CommandMetadata(
    name="luhf-join",
    group="Lu-Hf Analysis",
    description="联合U-Pb和Lu-Hf数据表",
    category="luhf",
    long_description="将U-Pb年龄数据与Lu-Hf同位素数据连接",
    skill_trigger_phrases=[
        "join upb and luhf data",
        "combine upb luhf tables",
        "merge zircon data"
    ],
    equivalent_api=(
        "handler.load(source='csv', table='zircon_upb')\n"
        "handler.load(source='csv', table='zircon_luhf')\n"
        "df_joined = handler.join_upb_luhf(join_key='Ref_Sample_Key')"
    ),
    parameters=[
        {
            "name": "--join-key",
            "description": "连接键",
            "type": "Ref_Sample_Key|Sample&Grain"
        },
        {
            "name": "--how",
            "description": "连接方式",
            "type": "inner|left|right|outer"
        },
        {
            "name": "--output / -o",
            "description": "输出文件",
            "type": "PATH"
        }
    ],
    examples=[
        {
            "title": "连接U-Pb和Lu-Hf数据",
            "user_input": "联合U-Pb和Lu-Hf数据表",
            "command": "onedz luhf join --join-key Ref_Sample_Key -o joined.csv",
            "python_code": '''
handler.load(source="csv", table="zircon_upb")
handler.load(source="csv", table="zircon_luhf")
df_joined = handler.join_upb_luhf(join_key="Ref_Sample_Key", how="inner")
handler.export(df_joined, "joined.csv")
'''
        }
    ],
    output_description="返回连接后的DataFrame，包含U-Pb和Lu-Hf所有列"
)


@click.command()
@click.option(
    '--join-key',
    type=click.Choice(['Ref_Sample_Key', 'Sample&Grain'], case_sensitive=False),
    default='Ref_Sample_Key',
    help='连接键（默认: Ref_Sample_Key）'
)
@click.option(
    '--how',
    type=click.Choice(['inner', 'left', 'right', 'outer'], case_sensitive=False),
    default='inner',
    help='连接方式（默认: inner）'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='输出文件'
)
@click.pass_context
def join_cmd(ctx: click.Context, join_key: str, how: str, output: Optional[str]):
    """联合U-Pb和Lu-Hf数据表"""
    from onedz_handler import OneDZHandler

    csv_dir = ctx.obj.get('csv_dir')

    try:
        handler = OneDZHandler()

        click.echo("\n🔗 连接 U-Pb 和 Lu-Hf 数据")
        click.echo(f"   连接键: {join_key}")
        click.echo(f"   方式: {how}")

        # 加载数据
        click.echo(f"\n📥 加载数据...")
        handler.load(source="csv", table="zircon_upb", csv_dir=csv_dir)
        click.echo(f"   U-Pb: {handler.data.height:,} 条记录")

        handler.load(source="csv", table="zircon_luhf", csv_dir=csv_dir)
        click.echo(f"   Lu-Hf: {handler.engine.luhf.height:,} 条记录")

        # 连接
        df_joined = handler.join_upb_luhf(join_key=join_key, how=how)

        click.echo(f"\n✅ 连接完成: {df_joined.height:,} 条记录")
        click.echo(f"   列数: {df_joined.width}")

        # 导出
        if output:
            handler.export(df_joined, output)
            echo_success(f"已保存: {output}")

        return df_joined

    except Exception as e:
        echo_error(f"连接失败: {e}")
        raise click.Abort()


# ──────────────────────────── compute 子命令 ──────────────────────────

compute_metadata = CommandMetadata(
    name="luhf-compute",
    group="Lu-Hf Analysis",
    description="计算εHf(t)和TDM",
    category="luhf",
    long_description="基于Lu-Hf同位素比值计算εHf(t)和TDM模型年龄",
    skill_trigger_phrases=[
        "calculate epsilon hf",
        "compute epsilon Hf",
        "calculate tdm",
        "compute hf model age"
    ],
    equivalent_api=(
        "df_computed = handler.compute_epsilon_hf(\n"
        "    df_joined,\n"
        "    hf_col='176Hf/177Hf',\n"
        "    lu_col='176Lu/177Hf',\n"
        "    age_col='Best Age'\n"
        ")"
    ),
    parameters=[
        {
            "name": "--input",
            "description": "输入文件（已连接的U-Pb+Lu-Hf数据）",
            "type": "PATH"
        },
        {
            "name": "--hf-col",
            "description": "Hf同位素列名",
            "type": "TEXT"
        },
        {
            "name": "--lu-col",
            "description": "Lu同位素列名",
            "type": "TEXT"
        },
        {
            "name": "--age-col",
            "description": "年龄列名",
            "type": "TEXT"
        },
        {
            "name": "--no-tdm",
            "description": "不计算TDM",
            "type": "flag"
        },
        {
            "name": "--output / -o",
            "description": "输出文件",
            "type": "PATH"
        }
    ],
    examples=[
        {
            "title": "计算εHf(t)和TDM",
            "user_input": "计算εHf和TDM模型年龄",
            "command": "onedz luhf compute --input joined.csv -o computed.csv",
            "python_code": """
df_computed = handler.compute_epsilon_hf(
    df_joined,
    hf_col="176Hf/177Hf",
    lu_col="176Lu/177Hf",
    age_col="Best Age",
    compute_tdm=True
)
handler.export(df_computed, "computed.csv")
"""
        }
    ],
    output_description="返回添加了εHf(t)、TDM1、TDM2列的DataFrame"
)


@click.command()
@click.option(
    '--input',
    type=click.Path(exists=True),
    help='输入文件（已连接的U-Pb+Lu-Hf数据）'
)
@click.option(
    '--hf-col',
    default='176Hf/177Hf',
    help='Hf同位素列名（默认: 176Hf/177Hf）'
)
@click.option(
    '--lu-col',
    default='176Lu/177Hf',
    help='Lu同位素列名（默认: 176Lu/177Hf）'
)
@click.option(
    '--age-col',
    default='Best Age',
    help='年龄列名（默认: Best Age）'
)
@click.option(
    '--no-tdm',
    is_flag=True,
    help='不计算TDM'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='输出文件'
)
@click.pass_context
def compute_cmd(
    ctx: click.Context,
    input: Optional[str],
    hf_col: str,
    lu_col: str,
    age_col: str,
    no_tdm: bool,
    output: Optional[str]
):
    """计算εHf(t)和TDM"""
    from onedz_handler import OneDZHandler
    import polars as pl

    # 加载数据
    if input:
        try:
            df = pl.read_csv(input)
        except Exception as e:
            echo_error(f"读取文件失败: {e}")
            raise click.Abort()
    else:
        echo_error("请使用 --input 指定输入文件")
        raise click.Abort()

    click.echo(f"\n🧮 计算 εHf(t) 和 TDM")
    click.echo(f"   Hf列: {hf_col}")
    click.echo(f"   Lu列: {lu_col}")
    click.echo(f"   年龄列: {age_col}")
    click.echo(f"   计算TDM: {'否' if no_tdm else '是'}")

    try:
        handler = OneDZHandler()
        df_computed = handler.compute_epsilon_hf(
            df,
            hf_col=hf_col,
            lu_col=lu_col,
            age_col=age_col,
            compute_tdm=not no_tdm
        )

        # 显示统计
        if 'εHf(t)' in df_computed.columns:
            epsilon = df_computed['εHf(t)'].drop_nulls()
            click.echo(f"\n✅ 计算完成:")
            click.echo(f"   εHf(t) 有效值: {len(epsilon):,}")
            if len(epsilon) > 0:
                click.echo(f"   范围: {epsilon.min():.2f} ~ {epsilon.max():.2f}")

        # 导出
        if output:
            handler.export(df_computed, output)
            echo_success(f"已保存: {output}")

        return df_computed

    except Exception as e:
        echo_error(f"计算失败: {e}")
        raise click.Abort()


# ──────────────────────────── plot-epsilon 子命令 ─────────────────────

plot_epsilon_metadata = CommandMetadata(
    name="luhf-plot-epsilon",
    group="Lu-Hf Analysis",
    description="绘制εHf(t)演化图",
    category="luhf",
    long_description="创建εHf(t) vs Age散点图，包含CHUR和DM参考线",
    skill_trigger_phrases=[
        "plot epsilon hf",
        "epsilon hf evolution",
        "create hf evolution plot"
    ],
    equivalent_api=(
        "handler.plot_epsilon_hf(\n"
        "    df_computed,\n"
        "    age_col='Best Age',\n"
        "    epsilon_col='εHf(t)',\n"
        "    save='epsilon.png'\n"
        ")"
    ),
    parameters=[
        {
            "name": "--input",
            "description": "输入文件（包含εHf(t)的数据）",
            "type": "PATH"
        },
        {
            "name": "--age-col",
            "description": "年龄列名",
            "type": "TEXT"
        },
        {
            "name": "--epsilon-col",
            "description": "εHf(t)列名",
            "type": "TEXT"
        },
        {
            "name": "--color-by",
            "description": "分组着色列名",
            "type": "TEXT"
        },
        {
            "name": "--output / -o",
            "description": "输出图片文件",
            "type": "PATH"
        }
    ],
    examples=[
        {
            "title": "绘制εHf(t)演化图",
            "user_input": "创建εHf演化图",
            "command": "onedz luhf plot-epsilon --input computed.csv --color-by Continent -o epsilon.png",
            "python_code": '''
handler.plot_epsilon_hf(
    df_computed,
    color_by="Continent",
    save="epsilon.png"
)
'''
        }
    ],
    output_description="生成εHf(t) vs Age散点图，包含CHUR和DM参考线"
)


@click.command()
@click.option(
    '--input',
    type=click.Path(exists=True),
    help='输入文件（包含εHf(t)的数据）'
)
@click.option(
    '--age-col',
    default='Best Age',
    help='年龄列名（默认: Best Age）'
)
@click.option(
    '--epsilon-col',
    default='εHf(t)',
    help='εHf(t)列名（默认: εHf(t)）'
)
@click.option(
    '--color-by',
    help='分组着色列名'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    required=True,
    help='输出图片文件'
)
@click.pass_context
def plot_epsilon_cmd(
    ctx: click.Context,
    input: Optional[str],
    age_col: str,
    epsilon_col: str,
    color_by: Optional[str],
    output: str
):
    """绘制εHf(t)演化图"""
    from onedz_handler import OneDZHandler
    import polars as pl

    # 加载数据
    if input:
        try:
            df = pl.read_csv(input)
        except Exception as e:
            echo_error(f"读取文件失败: {e}")
            raise click.Abort()
    else:
        echo_error("请使用 --input 指定输入文件")
        raise click.Abort()

    click.echo(f"\n🎨 创建 εHf(t) 演化图")

    try:
        handler = OneDZHandler()
        fig = handler.plot_epsilon_hf(
            df,
            age_col=age_col,
            epsilon_col=epsilon_col,
            color_by=color_by,
            save=output
        )

        if color_by:
            click.echo(f"   分组: {color_by}")

        echo_success(f"图表已保存: {output}")

    except Exception as e:
        echo_error(f"绘图失败: {e}")
        raise click.Abort()

    return output


# ──────────────────────────── plot-tdm 子命令 ────────────────────────

plot_tdm_metadata = CommandMetadata(
    name="luhf-plot-tdm",
    group="Lu-Hf Analysis",
    description="绘制TDM分布图",
    category="luhf",
    long_description="创建TDM模型年龄的概率密度分布图",
    skill_trigger_phrases=[
        "plot tdm",
        "tdm distribution",
        "model age plot"
    ],
    equivalent_api=(
        "handler.plot_tdm(\n"
        "    df_computed,\n"
        "    tdm_col='TDM2',\n"
        "    save='tdm.png'\n"
        ")"
    ),
    parameters=[
        {
            "name": "--input",
            "description": "输入文件（包含TDM的数据）",
            "type": "PATH"
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
        }
    ],
    examples=[
        {
            "title": "绘制TDM2分布图",
            "user_input": "绘制TDM模型年龄分布",
            "command": "onedz luhf plot-tdm --input computed.csv --model dm2 -o tdm.png",
            "python_code": '''
handler.plot_tdm(df_computed, model="dm2", save="tdm.png")
'''
        }
    ],
    output_description="生成TDM模型年龄的KDE分布图"
)


@click.command()
@click.option(
    '--input',
    type=click.Path(exists=True),
    help='输入文件（包含TDM的数据）'
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
@click.pass_context
def plot_tdm_cmd(
    ctx: click.Context,
    input: Optional[str],
    model: str,
    output: str
):
    """绘制TDM分布图"""
    from onedz_handler import OneDZHandler
    import polars as pl

    # 加载数据
    if input:
        try:
            df = pl.read_csv(input)
        except Exception as e:
            echo_error(f"读取文件失败: {e}")
            raise click.Abort()
    else:
        echo_error("请使用 --input 指定输入文件")
        raise click.Abort()

    click.echo(f"\n🎨 创建 TDM{model.upper()} 分布图")

    try:
        handler = OneDZHandler()
        tdm_col = f"TDM{model.upper()}"

        fig = handler.plot_tdm(
            df,
            tdm_col=tdm_col,
            save=output
        )

        echo_success(f"图表已保存: {output}")

    except Exception as e:
        echo_error(f"绘图失败: {e}")
        raise click.Abort()

    return output


# ──────────────────────────── 创建命令组 ─────────────────────────────

# 创建 Click 命令组
luhf_group = click.Group(name='luhf', help='Lu-Hf 同位素分析')

# 添加子命令
luhf_group.add_command(join_cmd, name='join')
luhf_group.add_command(compute_cmd, name='compute')
luhf_group.add_command(plot_epsilon_cmd, name='plot-epsilon')
luhf_group.add_command(plot_tdm_cmd, name='plot-tdm')
