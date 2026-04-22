"""
Skill ↔ CLI 同步检查工具

用于检查 Skill 文档中描述的功能是否已在 CLI 中实现。
这个工具可以推广到其他使用类似元数据系统的项目。

核心思路：
1. 解析 Skill 文档，提取提到的功能/示例
2. 读取 CLI 命令注册表
3. 对比两者，找出缺失的 CLI 命令
"""

import re
from pathlib import Path
from typing import List, Dict, Set
from onedz_handler.cli.metadata import COMMAND_REGISTRY


class SkillCLISyncChecker:
    """
    Skill 与 CLI 同步检查器

    这是专门针对 OneDZ 项目的实现，但设计模式可以推广到其他项目：
    - 其他项目需要实现自己的 Skill 解析器
    - 使用类似的元数据注册系统
    - 调用 check_sync() 方法进行对比
    """

    def __init__(self, skill_file: Path):
        """
        初始化检查器

        Parameters
        ----------
        skill_file : Path
            Skill 文档路径
        """
        self.skill_file = skill_file
        self.skill_content = ""

        # 确保所有命令都已注册（导入所有命令模块）
        try:
            from onedz_handler.cli.commands import (
                query, clean, info, analyze, plot, export, luhf
            )
            # 重新导入注册表（现在应该有数据了）
            from onedz_handler.cli.metadata import COMMAND_REGISTRY
            self.cli_commands = set(COMMAND_REGISTRY.keys())
        except ImportError as e:
            print(f"⚠️  无法导入命令模块: {e}")
            self.cli_commands = set()

    def parse_skill_features(self) -> Dict[str, List[str]]:
        """
        解析 Skill 文档，提取功能描述

        这个方法是项目特定的，不同项目的 Skill 文档格式可能不同。

        Returns
        -------
        Dict[str, List[str]]
            提取的功能信息
        """
        if not self.skill_file.exists():
            return {"errors": [f"Skill 文件不存在: {self.skill_file}"]}

        self.skill_content = self.skill_file.read_text()

        features = {
            "user_examples": [],  # 用户示例
            "code_snippets": [],  # 代码片段
            "mentioned_apis": [],  # 提到的 API
        }

        # 提取用户输入示例 (在 "User input:" 后面)
        user_input_pattern = r'User input:\s*"([^"]+)"'
        features["user_examples"] = re.findall(user_input_pattern, self.skill_content)

        # 提取代码片段 (在 ```python ``` 块中)
        code_pattern = r'```python\n(.*?)```'
        features["code_snippets"] = re.findall(code_pattern, self.skill_content, re.DOTALL)

        # 提取提到的 handler API 调用
        api_pattern = r'handler\.([a-z_]+)\('
        all_apis = set(re.findall(api_pattern, self.skill_content))
        features["mentioned_apis"] = list(all_apis)

        return features

    def check_sync(self) -> Dict:
        """
        检查 Skill 和 CLI 的同步状态

        Returns
        -------
        Dict
            同步检查结果
        """
        features = self.parse_skill_features()

        result = {
            "skill_file": str(self.skill_file),
            "cli_commands_count": len(self.cli_commands),
            "cli_commands": sorted(self.cli_commands),
            "skill_features": features,
            "sync_status": "unknown",
            "recommendations": []
        }

        # 分析 Skill 中提到的功能
        mentioned_methods = features.get("mentioned_apis", [])

        # 检查哪些方法有对应的 CLI 命令
        missing_commands = []
        for method in mentioned_methods:
            # 简单的映射规则
            if method == "query" and "query" not in self.cli_commands:
                missing_commands.append(f"query (handler.{method})")
            elif method in ["clean", "qc"] and "clean" not in self.cli_commands:
                missing_commands.append(f"clean (handler.{method})")
            elif method == "analyze" and "analyze" not in self.cli_commands:
                missing_commands.append(f"analyze (handler.{method})")
            elif method in ["plot_age", "plot"] and "plot" not in self.cli_commands:
                missing_commands.append(f"plot (handler.{method})")
            elif method == "export" and "export" not in self.cli_commands:
                missing_commands.append(f"export (handler.{method})")
            elif method in ["join_upb_luhf", "compute_epsilon_hf",
                           "plot_epsilon_hf", "plot_tdm"] and "luhf" not in self.cli_commands:
                if "luhf" not in missing_commands:
                    missing_commands.append("luhf (Lu-Hf 功能组)")

        # 生成建议
        if missing_commands:
            result["sync_status"] = "incomplete"
            result["missing_commands"] = missing_commands
            result["recommendations"].append(
                f"⚠️  Skill 中提到了 {len(missing_commands)} 个功能，但 CLI 尚未实现"
            )
            for cmd in missing_commands:
                result["recommendations"].append(f"  - 缺少命令: {cmd}")
        else:
            result["sync_status"] = "synced"
            result["recommendations"].append(
                "✅ Skill 中提到的所有功能都已在 CLI 中实现"
            )

        # 检查是否有额外的 CLI 命令（Skill 中未提到）
        extra_commands = []
        for cmd in self.cli_commands:
            if cmd not in ["query", "clean", "analyze", "plot", "export", "luhf", "info"]:
                extra_commands.append(cmd)

        if extra_commands:
            result["recommendations"].append(
                f"ℹ️  CLI 中有 {len(extra_commands)} 个额外命令（Skill 中未提到）"
            )
            for cmd in extra_commands:
                result["recommendations"].append(f"  - 额外命令: {cmd}")

        return result

    def print_report(self):
        """打印同步检查报告"""
        result = self.check_sync()

        print("=" * 70)
        print("📊 Skill ↔ CLI 同步检查报告")
        print("=" * 70)
        print(f"Skill 文件: {result['skill_file']}")
        print(f"CLI 命令数: {result['cli_commands_count']}")
        print(f"同步状态: {result['sync_status'].upper()}")
        print()

        print("📋 已实现的 CLI 命令:")
        for cmd in result['cli_commands']:
            print(f"  ✓ {cmd}")
        print()

        print("💡 建议:")
        for rec in result['recommendations']:
            print(f"  {rec}")
        print()

        return result


def check_skill_cli_sync(skill_file: Path) -> Dict:
    """
    便捷函数：检查 Skill 和 CLI 的同步状态

    Parameters
    ----------
    skill_file : Path
        Skill 文档路径

    Returns
    -------
    Dict
        同步检查结果

    Examples
    --------
    >>> result = check_skill_cli_sync(Path("skills/onedz.md"))
    >>> print(result['sync_status'])
    'synced'
    """
    checker = SkillCLISyncChecker(skill_file)
    return checker.check_sync()


# CLI 命令（可选，用于直接运行）
if __name__ == "__main__":
    import sys

    # 默认检查项目 Skill 文件
    project_skill = Path("/home/zry/my-OneDZ-skill/skills/onedz.md")

    if len(sys.argv) > 1:
        project_skill = Path(sys.argv[1])

    checker = SkillCLISyncChecker(project_skill)
    checker.print_report()
