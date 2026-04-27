"""
OneDZ Handler 数据集提示信息模块

提供友好的数据集下载和配置提示
"""

DATA_DATASET_INFO = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                    OneDZ 数据集未找到或路径不正确                          ║
╚═══════════════════════════════════════════════════════════════════════════╝

OneDZ Skill 需要以下 CSV 格式数据集：
  • zircon_upb.csv  (约 1.5 GB - U-Pb 年龄数据，192 万条记录)
  • zircon_luhf.csv (约 183 MB - Lu-Hf 同位素数据，27 万条记录)

═══════════════════════════════════════════════════════════════════════════

📥 获取数据集
═══════════════════════════════════════════════════════════════════════════

方法 1: 官方网站下载（推荐）
  访问: https://onedz.top/DownloadPage.html
  下载: onedz_csv_YYYYMMDD.tar.gz

方法 2: Zenodo 下载
  DOI: 10.5281/zenodo.17407937
  链接: https://zenodo.org/records/17407937

═══════════════════════════════════════════════════════════════════════════

📂 指定数据集路径
═══════════════════════════════════════════════════════════════════════════

方法 1: 环境变量（推荐）
  export ONEDZ_DATA_PATH="/your/path/to/onedz_csv_20260328/"

方法 2: 初始化时指定
  from scripts.onedz_handler import OneDZHandler, OneDZConfig
  from pathlib import Path

  config = OneDZConfig()
  config.csv_dir = Path("/your/path/to/onedz_csv_20260328")
  handler = OneDZHandler(config=config)

方法 3: 用户配置文件（一次配置，永久生效）
  mkdir -p ~/.onedz
  echo '{"csv_dir": "/your/path/to/onedz_csv_20260328/modified"}' > ~/.onedz/config.json

方法 4: 加载时指定
  from scripts.onedz_handler import OneDZHandler
  from pathlib import Path

  handler = OneDZHandler()
  handler.load(
      source="csv",
      table="global_u-pb",
      csv_dir=Path("/your/path/to/onedz_csv_20260328")
  )

═══════════════════════════════════════════════════════════════════════════

📖 数据集说明
═══════════════════════════════════════════════════════════════════════════

基于以下论文：
  Li, K., Hu, X., Chai, R., Yang, J. et al. (2025)
  OneDZ: A Global Detrital Zircon Database and Implications for
  Constructing Giant Geoscience Database
  Earth System Science Data, 17, 1234-1256
  https://doi.org/10.5194/essd-17-1234-2025

═══════════════════════════════════════════════════════════════════════════

💡 需要帮助？
═══════════════════════════════════════════════════════════════════════════

查看文档: onedz-skill/references/dataset.md
获取帮助: https://github.com/KeranLi/Global-Detrital-Zircon/issues

"""

def check_dataset_exists(csv_dir) -> tuple[bool, str]:
    """
    检查数据集目录是否存在且包含必要文件

    Returns:
        (exists, message): (是否存在, 提示信息)
    """
    from pathlib import Path

    data_path = Path(csv_dir)

    if not data_path.exists():
        return False, f"数据目录不存在: {csv_dir}\n" + DATA_DATASET_INFO

    required_files = ["zircon_upb.csv", "zircon_luhf.csv"]
    missing_files = []

    for filename in required_files:
        file_path = data_path / filename
        if not file_path.exists():
            missing_files.append(filename)

    if missing_files:
        # 检查是否为分片格式（新数据集用 Total_UPb_split_parts/ 等目录）
        split_dirs = ["Total_UPb_split_parts", "Total_LuHf_split_parts"]
        has_split = all((data_path / d).is_dir() for d in split_dirs)
        if has_split:
            return True, f"✅ 数据集验证通过（分片格式）: {csv_dir}"
        return False, f"数据目录存在，但缺少文件: {', '.join(missing_files)}\n" + DATA_DATASET_INFO

    return True, f"✅ 数据集验证通过: {csv_dir}"

def print_dataset_info(csv_dir):
    """打印数据集信息"""
    from pathlib import Path

    data_path = Path(csv_dir)
    if data_path.exists():
        print(f"\n📂 当前数据集位置: {csv_dir}")

        upb_file = data_path / "zircon_upb.csv"
        luhf_file = data_path / "zircon_luhf.csv"

        if upb_file.exists():
            size_mb = upb_file.stat().st_size / (1024 * 1024)
            print(f"  • zircon_upb.csv: {size_mb:.1f} MB")

        if luhf_file.exists():
            size_mb = luhf_file.stat().st_size / (1024 * 1024)
            print(f"  • zircon_luhf.csv: {size_mb:.1f} MB")

        # 分片格式检测
        upb_split = data_path / "Total_UPb_split_parts"
        luhf_split = data_path / "Total_LuHf_split_parts"
        if upb_split.is_dir():
            n_parts = len(list(upb_split.glob("*.csv")))
            total_mb = sum(f.stat().st_size for f in upb_split.glob("*.csv")) / (1024 * 1024)
            print(f"  • Total_UPb_split_parts/: {n_parts} 个分片, 共 {total_mb:.1f} MB")
        if luhf_split.is_dir():
            n_parts = len(list(luhf_split.glob("*.csv")))
            total_mb = sum(f.stat().st_size for f in luhf_split.glob("*.csv")) / (1024 * 1024)
            print(f"  • Total_LuHf_split_parts/: {n_parts} 个分片, 共 {total_mb:.1f} MB")

        # 检测是否使用格式修正后的数据
        if not data_path.name.startswith("modified"):
            modified_dir = data_path / "modified"
            if modified_dir.is_dir() and (modified_dir / "zircon_upb.csv").exists():
                print(f"\n💡 提示: 检测到当前使用的是原始数据目录。")
                print(f"   格式修正后的数据位于: {modified_dir}")
                print(f"   修正内容: 编码乱码、仪器名称变体、分类值拼写等")
                print(f"   修正脚本: scripts/fix_dataset.py")
                print(f"   若需使用修正数据，请将 config.py 中的路径指向 modified/ 子目录")
    else:
        print(f"\n⚠️  数据集路径: {csv_dir}")
        print("   （路径不存在，请检查或重新配置）")
