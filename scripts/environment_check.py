#!/usr/bin/env python3
"""
OneDZ 环境检查脚本

在当前 Python 环境中检查 OneDZ 依赖是否满足要求
"""

import sys
import importlib
from pathlib import Path

# ANSI 颜色代码
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(text):
    """打印标题"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

def print_success(text):
    """打印成功信息"""
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    """打印错误信息"""
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    """打印警告信息"""
    print(f"{YELLOW}⚠️  {text}{RESET}")

def check_python_version():
    """检查 Python 版本"""
    print(f"📍 Python 版本: {sys.version}")
    print(f"📍 Python 路径: {sys.executable}")

    major, minor = sys.version_info[:2]
    if major >= 3 and minor >= 11:
        print_success(f"Python {major}.{minor} 符合要求 (≥3.11)")
        return True
    else:
        print_error(f"Python {major}.{minor} 不符合要求 (需要 ≥3.11)")
        return False

def check_environment():
    """检查当前环境"""
    env_name = Path(sys.executable).parent.parent.name
    print(f"📍 当前环境: {env_name}")

    if env_name == "OneDZHHandler":
        print_success("正在 OneDZHHandler 环境中运行")
        return True
    else:
        print_warning(f"不在 OneDZHHandler 环境中（当前: {env_name}）")
        return False

def check_dependencies():
    """检查所有依赖包"""
    dependencies = {
        "核心库": [
            ("polars", "0.20.0"),
            ("pandas", "2.0.0"),
            ("numpy", "1.24.0"),
        ],
        "数据处理": [
            ("scipy", "1.11.0"),
            ("geopandas", "0.14.0"),
            ("shapely", "2.0.0"),
        ],
        "可视化": [
            ("matplotlib", "3.7.0"),
        ],
        "导出": [
            ("openpyxl", "3.1.0"),
        ],
        "分析": [
            ("scikit_learn", "1.3.0"),
        ],
        "CLI": [
            ("click", "8.0.0"),
            ("yaml", "6.0"),  # pyyaml 在代码中是 yaml
        ],
        "其他": [
            ("tqdm", "4.65.0"),
            ("jinja2", "3.1.0"),
        ],
    }

    all_ok = True
    missing_packages = []

    for category, packages in dependencies.items():
        print(f"\n{BLUE}📦 {category}{RESET}")

        for package_name, min_version in packages:
            try:
                # 处理包名差异
                import_name = package_name
                if package_name == "scikit_learn":
                    import_name = "sklearn"
                elif package_name == "yaml":
                    import_name = "yaml"

                module = importlib.import_module(import_name)

                # 尝试获取版本
                version = getattr(module, "__version__", "unknown")
                print_success(f"{package_name:20s} ({version})")

            except ImportError:
                print_error(f"{package_name:20s} (缺失)")
                missing_packages.append(package_name)
                all_ok = False

    return all_ok, missing_packages

def check_onedz_handler():
    """检查 OneDZ Handler"""
    print(f"\n{BLUE}🔍 OneDZ Handler{RESET}")

    try:
        from scripts.onedz_handler import OneDZHandler
        print_success("OneDZ Handler 可以导入")

        # 尝试实例化
        try:
            handler = OneDZHandler()
            print_success("OneDZ Handler 可以实例化")
            return True
        except Exception as e:
            print_warning(f"OneDZ Handler 实例化失败: {e}")
            return False

    except ImportError as e:
        print_error(f"OneDZ Handler 导入失败: {e}")
        return False

def check_cli():
    """检查 CLI 命令"""
    print(f"\n{BLUE}🔧 CLI 命令{RESET}")

    import shutil
    onedz_path = shutil.which("onedz")

    if onedz_path:
        print_success(f"onedz 命令可用: {onedz_path}")
        return True
    else:
        print_error("onedz 命令不可用（可能不在 PATH 中或未安装）")
        return False

def main():
    """主函数"""
    print_header("OneDZ 环境检查工具")

    # 1. Python 版本
    python_ok = check_python_version()
    print()

    # 2. 环境检查
    env_ok = check_environment()
    print()

    # 3. 依赖检查
    deps_ok, missing = check_dependencies()

    # 4. OneDZ Handler 检查
    onedz_ok = check_onedz_handler()

    # 5. CLI 检查
    cli_ok = check_cli()

    # 总结
    print_header("检查结果总结")

    results = {
        "Python 版本": python_ok,
        "Conda 环境": env_ok,
        "依赖包": deps_ok,
        "OneDZ Handler": onedz_ok,
        "CLI 命令": cli_ok,
    }

    for name, ok in results.items():
        status = "✅ 通过" if ok else "❌ 失败"
        color = GREEN if ok else RED
        print(f"{color}{name:20s}: {status}{RESET}")

    # 建议
    if not all(results.values()):
        print_header("修复建议")

        if not env_ok:
            print_warning("不在 OneDZHHandler 环境中")
            print("\n解决方案：")
            print("  conda activate OneDZHHandler")
            print("\n或使用：")
            print("  conda run -n OneDZHHandler python your_script.py")

        if missing:
            print_warning(f"缺少 {len(missing)} 个依赖包")
            print(f"\n缺失的包: {', '.join(missing)}")
            print("\n解决方案：")
            print("  pip install -r requirements.txt")

        if not onedz_ok and not missing:
            print_warning("OneDZ Handler 无法使用")
            print("\n解决方案：")
            print("  pip install -e /home/zry/my-OneDZ-skill")

        if not cli_ok:
            print_warning("CLI 命令不可用")
            print("\n解决方案：")
            print("  pip install -e /home/zry/my-OneDZ-skill")
            print("\n或使用 conda run：")
            print("  conda run -n OneDZHHandler onedz --version")

        return 1
    else:
        print_header("🎉 所有检查通过！")
        print("\n✅ OneDZ 已准备就绪，可以开始使用了！")
        print("\n快速开始：")
        print("  Python API: from scripts.onedz_handler import OneDZHandler")
        print("  CLI: onedz query --period Cretaceous")
        print("  Skill: 在 Claude Code 中自然语言调用")
        return 0

if __name__ == "__main__":
    sys.exit(main())
