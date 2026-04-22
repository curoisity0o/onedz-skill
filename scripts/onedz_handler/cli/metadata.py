"""
CLI 命令元数据系统 - 用于自动生成 Skill 文档

这个模块实现了 CLI 命令的元数据定义和注册系统，使得 CLI 和 Skill 文档
能够保持同步。每个 CLI 命令都应该使用 @register_command 装饰器注册其元数据。

核心概念：
- CommandMetadata: 命令元数据定义
- COMMAND_REGISTRY: 全局命令注册表
- register_command: 元数据装饰器
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any


@dataclass
class CommandMetadata:
    """
    CLI 命令元数据

    这个数据类包含了生成 Skill 文档所需的所有信息。

    Attributes
    ----------
    name : str
        命令名称（如 "query", "clean"）
    group : str
        命令组（如 "Data Query", "Analysis", "Visualization"）
    description : str
        命令描述，用于帮助文档
    category : str
        功能分类（如 "data_operations", "analysis", "visualization"）
    examples : List[Dict[str, str]]
        使用示例列表，每个示例包含：
        - title: 示例标题
        - user_input: 用户的自然语言输入
        - command: 生成的 CLI 命令
        - python_code: 等效的 Python API 代码（可选）
    skill_trigger_phrases : List[str]
        Skill 触发词列表，这些短语会触发 Claude Code 使用该功能
    equivalent_api : str
        等效的 Python API 调用示例
    parameters : List[Dict]
        参数列表，每个参数包含：
        - name: 参数名称
        - description: 参数描述
        - type: 参数类型（如 TEXT, PATH, FLOAT[]）
    long_description : str, optional
        命令的详细描述，用于文档
    output_description : str, optional
        命令输出的描述
    """

    name: str
    group: str
    description: str
    category: str
    examples: List[Dict[str, str]]
    skill_trigger_phrases: List[str]
    equivalent_api: str
    parameters: List[Dict[str, Any]]
    long_description: Optional[str] = None
    output_description: Optional[str] = None

    def to_skill_example(self, index: int) -> str:
        """
        生成 Skill 文档格式的示例

        Parameters
        ----------
        index : int
            示例索引（从 0 开始）

        Returns
        -------
        str
            Markdown 格式的示例文档
        """
        if index >= len(self.examples):
            raise IndexError(f"示例索引超出范围: {index} >= {len(self.examples)}")

        example = self.examples[index]

        python_code = example.get('python_code', self.equivalent_api)

        return f"""**Example: {example['title']}**

User input: "{example['user_input']}"

Generated command:
```bash
{example['command']}
```

Equivalent Python API:
```python
{python_code}
```"""

    def to_markdown(self) -> str:
        """
        生成完整的命令 Markdown 文档

        Returns
        -------
        str
            命令的 Markdown 文档
        """
        md = f"### {self.name}\n\n"
        md += f"{self.description}\n\n"

        if self.long_description:
            md += f"{self.long_description}\n\n"

        md += "**Parameters:**\n\n"
        for param in self.parameters:
            md += f"- `{param['name']}`: {param['description']}"
            if 'type' in param:
                md += f" ({param['type']})"
            md += "\n"

        md += "\n**Examples:**\n\n"
        for i, example in enumerate(self.examples):
            md += self.to_skill_example(i) + "\n\n"

        if self.output_description:
            md += f"**Output:**\n\n{self.output_description}\n\n"

        return md


# 全局命令注册表
# 存储所有已注册的命令元数据，键为命令名称
COMMAND_REGISTRY: Dict[str, CommandMetadata] = {}


def register_command(metadata: CommandMetadata) -> Callable:
    """
    注册命令元数据（装饰器工厂）

    使用这个装饰器将元数据附加到命令函数，并自动注册到全局注册表。

    Parameters
    ----------
    metadata : CommandMetadata
        命令的元数据对象

    Returns
    -------
    Callable
        装饰器函数

    Examples
    --------
    >>> metadata = CommandMetadata(
    ...     name="query",
    ...     group="Data Query",
    ...     description="查询碎屑锆石数据",
    ...     category="data_operations",
    ...     examples=[...],
    ...     skill_trigger_phrases=["query zircon data"],
    ...     equivalent_api="handler.query()",
    ...     parameters=[...]
    ... )
    >>> @register_command(metadata)
    ... def query_cmd():
    ...     pass
    """
    def decorator(func: Callable) -> Callable:
        # 注册到全局注册表
        COMMAND_REGISTRY[metadata.name] = metadata
        # 附加到函数对象，方便运行时访问
        func._onedz_metadata = metadata
        return func

    return decorator


def get_command_metadata(command_name: str) -> Optional[CommandMetadata]:
    """
    获取命令的元数据

    Parameters
    ----------
    command_name : str
        命令名称

    Returns
    -------
    CommandMetadata or None
        命令的元数据，如果不存在则返回 None
    """
    return COMMAND_REGISTRY.get(command_name)


def list_commands_by_group() -> Dict[str, List[CommandMetadata]]:
    """
    按组列出所有命令

    Returns
    -------
    Dict[str, List[CommandMetadata]]
        按组组织的命令字典
    """
    groups: Dict[str, List[CommandMetadata]] = {}

    for name, metadata in COMMAND_REGISTRY.items():
        if metadata.group not in groups:
            groups[metadata.group] = []
        groups[metadata.group].append(metadata)

    return groups


def list_all_trigger_phrases() -> List[str]:
    """
    列出所有 Skill 触发词

    Returns
    -------
    List[str]
        所有触发词的列表
    """
    phrases = []
    for metadata in COMMAND_REGISTRY.values():
        phrases.extend(metadata.skill_trigger_phrases)
    return sorted(set(phrases))


# 导出公共接口
__all__ = [
    "CommandMetadata",
    "COMMAND_REGISTRY",
    "register_command",
    "get_command_metadata",
    "list_commands_by_group",
    "list_all_trigger_phrases",
]
