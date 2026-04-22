"""
OneDZ Handler CLI 主入口

这是 OneDZ Handler 的命令行接口主入口，提供统一的命令行访问方式。

使用示例:
    # 查询数据
    onedz query --period Cretaceous --continent Asia

    # 数据清洗
    onedz clean --input data.csv --concordance-min 0.90

    # 查看信息
    onedz info

    # 获取帮助
    onedz --help
    onedz query --help
"""

import click
import sys
from pathlib import Path
from typing import Dict, Any

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入子命令
from onedz_handler.cli.commands.query import query_cmd
from onedz_handler.cli.commands.clean import clean_cmd
from onedz_handler.cli.commands.info import info_cmd
from onedz_handler.cli.commands.analyze import analyze_cmd
from onedz_handler.cli.commands.plot import plot_cmd
from onedz_handler.cli.commands.export import export_cmd
from onedz_handler.cli.commands.luhf import luhf_group


@click.group()
@click.version_option(version="1.0.0", prog_name="onedz")
@click.option(
    '--config',
    type=click.Path(exists=True),
    help='YAML 配置文件路径'
)
@click.option(
    '--csv-dir',
    type=click.Path(exists=True),
    help='CSV 数据目录路径'
)
@click.option(
    '--output-dir',
    type=click.Path(),
    default='./onedz_output',
    help='输出目录 (默认: ./onedz_output)'
)
@click.option(
    '--log-level',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
    default='INFO',
    help='日志级别 (默认: INFO)'
)
@click.option(
    '--quiet',
    is_flag=True,
    help='静默模式，减少输出'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='详细输出模式'
)
@click.pass_context
def cli(ctx: click.Context, config: str, csv_dir: str, output_dir: str,
        log_level: str, quiet: bool, verbose: bool):
    """
    OneDZ Handler - 全球碎屑锆石数据库分析工具

    基于Li et al. (2025) OneDZ数据库，提供数据加载、科学清洗、统计分析、
    可视化、多格式导出的一站式命令行工具。

    全局选项:
        --config PATH        YAML 配置文件路径
        --csv-dir PATH       CSV 数据目录
        --output-dir PATH    输出目录 (默认: ./onedz_output)
        --log-level LEVEL    日志级别 (DEBUG/INFO/WARNING/ERROR)
        --quiet              静默模式
        --verbose, -v        详细输出

    示例:
        # 查询亚洲白垩纪碎屑锆石
        onedz query --period Cretaceous --continent Asia -o asia.csv

        # 清洗数据
        onedz clean --input raw.csv --concordance-min 0.90 -o clean.csv

        # 创建 KDE 图
        onedz plot --input data.csv --plot-type kde -o figure.png

        # 查看数据集信息
        onedz info
    """
    # 初始化上下文对象
    ctx.ensure_object(dict)

    # 存储全局配置
    ctx.obj.update({
        'config': config,
        'csv_dir': csv_dir,
        'output_dir': output_dir,
        'log_level': log_level,
        'quiet': quiet,
        'verbose': verbose,
        'handler': None,  # OneDZHandler 实例（延迟加载）
    })

    # 设置输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)


# 注册子命令
cli.add_command(query_cmd)
cli.add_command(clean_cmd)
cli.add_command(info_cmd)
cli.add_command(analyze_cmd)
cli.add_command(plot_cmd)
cli.add_command(export_cmd)
cli.add_command(luhf_group)


def main():
    """CLI 主入口函数"""
    cli()


if __name__ == '__main__':
    main()
