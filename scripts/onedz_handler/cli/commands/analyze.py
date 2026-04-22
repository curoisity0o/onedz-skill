"""
分析命令实现

提供统计分析的命令行接口，包括分布分析、KDE、Bootstrap、K-S检验等。
"""

import click
from pathlib import Path
from typing import Optional
import numpy as np
from onedz_handler.cli.metadata import register_command, CommandMetadata
from onedz_handler.cli.validators import validate_file_exists, validate_age_range
from onedz_handler.cli.utils import echo_success, echo_error, format_age_range


# 定义命令元数据
analyze_metadata = CommandMetadata(
    name="analyze",
    group="Analysis",
    description="统计分析锆石年龄分布",
    category="analysis",
    long_description=(
        "对锆石年龄数据进行综合统计分析，包括基础统计、KDE估计、"
        "多峰识别、Bootstrap重采样、K-S检验等。"
    ),
    skill_trigger_phrases=[
        "analyze age distribution",
        "statistical analysis",
        "peak detection",
        "bootstrap analysis",
        "ks test"
    ],
    equivalent_api=(
        "handler.analyze(df)\n"
        "# 或\n"
        "handler.kde(ages)\n"
        "handler.bootstrap(ages)"
    ),
    parameters=[
        {
            "name": "--input",
            "description": "输入文件（CSV格式）",
            "type": "PATH"
        },
        {
            "name": "--age-col",
            "description": "年龄列名",
            "type": "TEXT"
        },
        {
            "name": "--kde",
            "description": "执行KDE分析"
        },
        {
            "name": "--bandwidth",
            "description": "KDE带宽（None=自适应）",
            "type": "FLOAT"
        },
        {
            "name": "--bootstrap",
            "description": "执行Bootstrap重采样"
        },
        {
            "name": "--n-iterations",
            "description": "Bootstrap迭代次数",
            "type": "INTEGER"
        },
        {
            "name": "--peaks",
            "description": "检测年龄峰值"
        },
        {
            "name": "--age-range",
            "description": "分析年龄范围 (Ma)",
            "type": "FLOAT FLOAT"
        },
        {
            "name": "--output / -o",
            "description": "输出文件（保存统计结果）",
            "type": "PATH"
        }
    ],
    examples=[
        {
            "title": "综合分布分析",
            "user_input": "分析锆石年龄分布，检测峰值",
            "command": "onedz analyze --input data.csv --peaks -o analysis.txt",
            "python_code": '''
from onedz_handler import OneDZHandler

handler = OneDZHandler()
df = pl.read_csv("data.csv")
result = handler.analyze(df)

print(f"平均年龄: {result['summary']['mean']:.1f} Ma")
print(f"峰值:")
for peak in result['peaks']:
    print(f"  {peak['peak_age']:.0f} ± {peak['age_uncertainty']:.0f} Ma")
'''
        },
        {
            "title": "Bootstrap 不确定性分析",
            "user_input": "使用Bootstrap分析年龄分布的不确定性",
            "command": "onedz analyze --input data.csv --bootstrap --n-iterations 1000",
            "python_code": '''
ages = df["Best Age"].drop_nulls().to_numpy()
bs_result = handler.bootstrap(ages, n_iterations=1000)
print(f"95% 置信区间: {bs_result['ci_low']:.1f} - {bs_result['ci_high']:.1f} Ma")
'''
        }
    ],
    output_description=(
        "显示统计结果包括：均值、中位数、标准差、年龄范围、"
        "检测到的峰值、KDE曲线数据等。"
    )
)


@click.command()
@click.option(
    '--input',
    type=click.Path(exists=True),
    help='输入文件（CSV格式）'
)
@click.option(
    '--age-col',
    default='Best Age',
    help='年龄列名（默认: Best Age）'
)
@click.option(
    '--kde',
    is_flag=True,
    help='执行KDE分析'
)
@click.option(
    '--bandwidth',
    type=float,
    help='KDE带宽（None=自适应）'
)
@click.option(
    '--bootstrap',
    is_flag=True,
    help='执行Bootstrap重采样'
)
@click.option(
    '--n-iterations',
    type=int,
    default=1000,
    help='Bootstrap迭代次数（默认: 1000）'
)
@click.option(
    '--peaks',
    is_flag=True,
    help='检测年龄峰值'
)
@click.option(
    '--age-range',
    nargs=2,
    type=float,
    help='分析年龄范围 Ma (min max)',
    callback=validate_age_range
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='输出文件（保存统计结果）'
)
@click.pass_context
@register_command(analyze_metadata)
def analyze_cmd(
    ctx: click.Context,
    input: Optional[str],
    age_col: str,
    kde: bool,
    bandwidth: Optional[float],
    bootstrap: bool,
    n_iterations: int,
    peaks: bool,
    age_range: Optional[tuple],
    output: Optional[str]
):
    """
    统计分析锆石年龄分布

    执行综合统计分析，包括：
    - 基础统计（均值、中位数、标准差）
    - KDE核密度估计
    - Bootstrap重采样（不确定性评估）
    - 多峰检测

    示例:
        # 综合分析
        onedz analyze --input data.csv --peaks

        # Bootstrap分析
        onedz analyze --input data.csv --bootstrap --n-iterations 1000
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

    # 确定输入数据
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

    # 检查年龄列
    if age_col not in df.columns:
        echo_error(f"数据中未找到年龄列: {age_col}")
        echo_error(f"可用的列: {', '.join(df.columns[:10])}...")
        raise click.Abort()

    # 提取年龄数据
    ages = df[age_col].drop_nulls().to_numpy()

    if len(ages) == 0:
        echo_error(f"年龄列 {age_col} 中没有有效数据")
        raise click.Abort()

    # 应用年龄范围过滤
    if age_range:
        mask = (ages >= age_range[0]) & (ages <= age_range[1])
        ages_filtered = ages[mask]
        click.echo(f"\n📊 年龄范围过滤: {format_age_range(age_range)}")
        click.echo(f"   保留: {len(ages_filtered)} / {len(ages)} 条记录")
        ages = ages_filtered

    click.echo(f"\n📊 统计分析 (n={len(ages):,})")

    # 基础统计
    click.echo(f"\n基础统计:")
    click.echo(f"  平均年龄: {np.mean(ages):.1f} Ma")
    click.echo(f"  中位数: {np.median(ages):.1f} Ma")
    click.echo(f"  标准差: {np.std(ages):.1f} Ma")
    click.echo(f"  年龄范围: {np.min(ages):.1f} - {np.max(ages):.1f} Ma")

    # KDE分析
    if kde or (not peaks and not bootstrap):
        # 默认执行KDE
        click.echo(f"\n📈 KDE 分析:")
        x, y = handler.kde(ages, bandwidth=bandwidth)
        click.echo(f"  KDE 曲线点数: {len(x)}")
        if bandwidth:
            click.echo(f"  带宽: {bandwidth:.2f}")
        else:
            click.echo(f"  带宽: 自适应")

    # 峰值检测
    if peaks:
        click.echo(f"\n🔍 峰值检测:")
        result = handler.analyze(df, age_col=age_col)
        detected_peaks = result.get('peaks', [])

        if detected_peaks:
            for i, peak in enumerate(detected_peaks[:10], 1):
                click.echo(f"  峰值 {i}: {peak['peak_age']:.0f} ± {peak['age_uncertainty']:.0f} Ma")
        else:
            click.echo(f"  未检测到明显峰值")

    # Bootstrap分析
    if bootstrap:
        click.echo(f"\n🔄 Bootstrap 重采样 (n={n_iterations}):")
        bs_result = handler.bootstrap(ages, n_iterations=n_iterations)

        click.echo(f"  均值: {bs_result['mean']:.1f} Ma")
        click.echo(f"  标准误: {bs_result['std']:.1f} Ma")
        click.echo(f"  95% 置信区间: {bs_result['ci_low']:.1f} - {bs_result['ci_high']:.1f} Ma")

    # 导出结果
    if output:
        try:
            output_lines = [
                f"# OneDZ 统计分析结果",
                f"",
                f"## 基础统计",
                f"样本数: {len(ages)}",
                f"平均年龄: {np.mean(ages):.2f} Ma",
                f"中位数: {np.median(ages):.2f} Ma",
                f"标准差: {np.std(ages):.2f} Ma",
                f"最小值: {np.min(ages):.2f} Ma",
                f"最大值: {np.max(ages):.2f} Ma",
            ]

            if peaks:
                result = handler.analyze(df, age_col=age_col)
                detected_peaks = result.get('peaks', [])
                if detected_peaks:
                    output_lines.extend([
                        f"",
                        f"## 检测到的峰值",
                    ])
                    for i, peak in enumerate(detected_peaks, 1):
                        output_lines.append(
                            f"峰值 {i}: {peak['peak_age']:.1f} ± {peak['age_uncertainty']:.1f} Ma"
                        )

            Path(output).write_text("\n".join(output_lines))
            echo_success(f"结果已保存: {output}")
        except Exception as e:
            echo_error(f"导出失败: {e}")

    echo_success("分析完成")

    return {
        'ages': ages,
        'n': len(ages),
        'mean': np.mean(ages),
        'median': np.median(ages),
        'std': np.std(ages)
    }
