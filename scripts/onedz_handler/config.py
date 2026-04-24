"""
OneDZ Handler — 全局配置与常量定义

基于 Li et al. (2025) OneDZ 数据库结构，定义列名映射、默认阈值和地质常量。
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# ──────────────────────────── 数据路径 ────────────────────────────
# 优先级：ONEDZ_DATA_PATH 环境变量 > 默认路径
# 默认指向 modified/ 子目录（格式修正后的数据）
# 如果 modified/ 不存在，skill 会提示用户指定路径并自动写入此处
_DEFAULT_DATA_DIR = "/home/zry/my_earth/data/raw/OneDZ/onedz_csv_20260328/modified"
DEFAULT_CSV_DIR = Path(os.getenv("ONEDZ_DATA_PATH", _DEFAULT_DATA_DIR))
ZENODO_DOI = "10.5281/zenodo.17407937"
ZENODO_URL = "https://zenodo.org/records/17407937"
ONEDZ_DOWNLOAD_PAGE = "https://onedz.top/DownloadPage.html"

# ──────────────────────────── 表名 ────────────────────────────────
TABLE_UPB = "zircon_upb"
TABLE_LUHF = "zircon_luhf"

# ──────────────────────────── 列名规范 ────────────────────────────
class Cols:
    """OneDZ 数据库标准列名（兼容 CSV 和 MySQL 两种来源的命名差异）。"""

    # Publication metadata
    LEAD_AUTHOR = "Lead_Author"
    YEAR = "Year"
    JOURNAL = "Journal"
    TITLE = "Title"
    WEB_LINK = "Web_Link"
    REF_NO = "Ref_No."
    REF_SAMPLE_KEY = "Ref_Sample_Key"

    # Sample metadata
    PUBLISHED_SAMPLE_ID = "Published_Sample_ID"
    UNIQUE_SAMPLE_NO = "Unique_Sample_No."
    SAMPLE_GRAIN = "Sample&Grain"
    COUNTRY_STATE = "Country_State"
    REGION = "Region"
    CONTINENT = "Continent"
    MAJOR_GEO_DESC = "Major_Geographic_Geologic_Description"
    MINOR_GEO_UNIT = "Minor_Geologic_Geographic_Unit"
    FORMATION = "Formation"
    LOCALITY = "Locality"
    LATITUDE = "Latitude"
    LONGITUDE = "Longitude"

    # Depositional age
    DEPOS_AGE_PERIOD = "Depos.Age (Period)"
    DEPOS_AGE_EPOCH = "Depos.Age (Epoch)"
    DEPOS_AGE_STAGE = "Depos.Age (Age)"
    MAX_DEPOS_AGE = "Max. Depos. Age (Ma)"
    EST_DEPOS_AGE = "Est. Depos. Age (Ma)"
    MIN_DEPOS_AGE = "Min. Depos. Age (Ma)"

    # Analytical method
    MINERAL = "Mineral"
    MASS_SPECTROMETER = "Mass Spectrometer"
    SPECTROMETER_LOCATION = "Spectrometer Location"
    INSTITUTION = "Institution"

    # Rock classification
    CLASS1_ROCK = "Class-1 Rock Type"
    CLASS2_ROCK = "Class-2 Rock Type"
    CLASS3_ROCK = "Class-3 Rock Type"

    # U-Pb isotope ratios
    RATIO_206PB_238U = "206Pb/238U  isotope ratio"
    RATIO_206PB_238U_ERR = "206Pb/238U uncertainty (±1σ)"
    RATIO_207PB_235U = "207Pb/235U  isotope ratio"
    RATIO_207PB_235U_ERR = "207Pb/235U uncertainty (±1σ)"
    RATIO_207PB_206PB = "207Pb/206Pb  isotope ratio"
    RATIO_207PB_206PB_ERR = "207Pb/206Pb uncertainty (±1σ)"

    # U-Pb ages
    AGE_206PB_238U = "Published 206Pb/238U age (Ma)"
    AGE_206PB_238U_1S = "Published 206Pb/238U 1σ uncert."
    AGE_206PB_238U_2S = "Published 206Pb/238U 2σ uncert."
    AGE_207PB_235U = "Published 207Pb/235U age (Ma)"
    AGE_207PB_235U_1S = "Published 207Pb/235U 1σ uncert."
    AGE_207PB_235U_2S = "Published 207Pb/235U 2σ uncert."
    AGE_207PB_206PB = "Published 207Pb/206Pb age (Ma)"
    AGE_207PB_206PB_1S = "Published 207Pb/206Pb 1σ uncert."
    AGE_207PB_206PB_2S = "Published 207Pb/206Pb 2σ uncert."

    # Best age
    BEST_AGE = "Best Age"
    BEST_AGE_1S = "Best_Age_uncertainty_1sigma"
    BEST_AGE_2S = "Best_Age_uncertainty_2sigma"
    DISCORD_RATIO = "Discord ratio"

    # Elemental concentrations
    U_PPM = "U_ppm"
    TH_PPM = "Th_ppm"
    PB_PPM = "Pb_ppm"
    TH_U = "Th/U"

    # Grain details
    SPOT = "Spot"
    SPOT_DIAM = "Spot diam. (μm)"
    UPB_RECORD_COUNT = "U-Pb Record Count"


# ──────────────── 列名别名映射（处理 CSV/SQL/数据源差异）──────────────
COLUMN_ALIASES: Dict[str, List[str]] = {
    # U-Pb CSV: "Ref_No." ; Lu-Hf CSV: "Ref No."
    Cols.REF_NO: ["Ref No."],
    # U-Pb CSV: "Web_Link" ; Lu-Hf CSV: "Web Link"
    Cols.WEB_LINK: ["Web Link"],
    # U-Pb CSV: "Ref_Sample_Key" ; Lu-Hf CSV: "Ref-Sample Key"
    Cols.REF_SAMPLE_KEY: ["Ref-Sample Key"],
    # U-Pb CSV: "Unique_Sample_No." ; Lu-Hf CSV: same
    # U-Pb CSV: "Published_Sample_ID" ; Lu-Hf CSV: "Published Sample_ID"
    Cols.PUBLISHED_SAMPLE_ID: ["Published Sample_ID"],
    # Lu-Hf CSV 拼写错误: "Latitud" / "Logitud"
    Cols.LATITUDE: ["Latitud"],
    Cols.LONGITUDE: ["Logitud"],
    # Lu-Hf CSV: "Laboratory/Institution" vs U-Pb CSV: "Institution"
    Cols.INSTITUTION: ["Laboratory/Institution"],
    # Depos age — 兼容不同 CSV 版本
    Cols.DEPOS_AGE_PERIOD: ["Depos. Age (纪)"],
    Cols.DEPOS_AGE_EPOCH: ["Depos. Age (世)"],
    Cols.DEPOS_AGE_STAGE: ["Depos. Age (期)"],
    # Best Age uncertainty — CSV 用 "Best Age uncertainty (±1σ)"
    Cols.BEST_AGE_1S: [
        "Best_Age_uncertainty_1sigma",
        "Best Age uncertainty (±1σ)",
    ],
    Cols.BEST_AGE_2S: [
        "Best_Age_uncertainty_2sigma",
        "Best Age uncertainty (±2σ)",
    ],
    # Lu-Hf: U-Pb Age 列名
    "U-Pb Age (Ma)": ["U-Pb Age (Ma)"],
}

# ──────────────────────────── 地质常量 ────────────────────────────
# Lu-Hf 参考值 (Bouvier et al., 2008; Griffin et al., 2002)
LAMBDA_176LU = 1.867e-11       # 176Lu 衰变常数 (yr⁻¹), Söderlund et al. (2004)
CHUR_176HF_177HF_PRESENT = 0.282785   # 现今球粒陨石 176Hf/177Hf
CHUR_176LU_177HF_PRESENT = 0.0336     # 现今球粒陨石 176Lu/177Hf
DM_176HF_177HF_PRESENT = 0.28325      # 亏损地幔 176Hf/177Hf (Griffin et al., 2000)
DM_176LU_177HF_PRESENT = 0.0388       # 亏损地幔 176Lu/177Hf
LUC_176HF_177HF = 0.015              # 大陆壳平均 176Lu/177Hf (f_cc = -0.55)

# ──────────────────────────── 年龄选择 ────────────────────────────
AGE_CUTOFF_MA = 1000  # 1000 Ma 分界线：低于用 206Pb/238U，高于用 207Pb/206Pb

# ──────────────────────────── 默认 QC 阈值 ────────────────────────
DEFAULT_CONCORDANCE_MIN = 0.90   # 90%
DEFAULT_CONCORDANCE_MAX = 1.10   # 110%


# ──────────────────────────── 配置数据类 ──────────────────────────
@dataclass
class OneDZConfig:
    """OneDZ Handler 运行时配置。"""

    # 数据源
    csv_dir: Path = DEFAULT_CSV_DIR
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "onedz"
    dataset_version: Optional[str] = None  # None = 自动检测

    # QC 参数
    age_cutoff_ma: float = AGE_CUTOFF_MA
    concordance_min: float = DEFAULT_CONCORDANCE_MIN
    concordance_max: float = DEFAULT_CONCORDANCE_MAX
    error_sigma: int = 1  # 使用 1σ 或 2σ 误差 (1 | 2)

    # KDE 参数
    kde_bandwidth: Optional[float] = None  # None 表示自适应
    kde_min_bandwidth: float = 1.0
    kde_max_bandwidth: float = 50.0

    # 重采样参数
    n_bootstrap: int = 1000
    n_monte_carlo: int = 10000

    # 可视化
    figure_dpi: int = 150
    figure_format: str = "png"

    # 输出
    output_dir: Path = Path.home() / "onedz_output"
    use_timestamp_output: bool = True  # 是否使用带时间戳的输出目录
    timestamp_format: str = "%Y%m%d_%H%M%S"  # 时间戳格式


# ──────────────────────── 地质年代映射表 ──────────────────────────
GEO_PERIODS: Dict[str, Tuple[float, float]] = {
    "Quaternary":       (0.0, 2.58),
    "Neogene":          (2.58, 23.04),
    "Paleogene":        (23.04, 66.0),
    "Cretaceous":       (66.0, 145.0),
    "Jurassic":         (145.0, 201.4),
    "Triassic":         (201.4, 252.2),
    "Permian":          (252.2, 298.9),
    "Carboniferous":    (298.9, 358.9),
    "Devonian":         (358.9, 419.2),
    "Silurian":         (419.2, 443.8),
    "Ordovician":       (443.8, 485.4),
    "Cambrian":         (485.4, 541.0),
    "Ediacaran":        (541.0, 635.0),
    "Cryogenian":       (635.0, 720.0),
    "Tonian":           (720.0, 1000.0),
    "Stenian":          (1000.0, 1200.0),
    "Ectasian":         (1200.0, 1400.0),
    "Calymmian":        (1400.0, 1600.0),
    "Statherian":       (1600.0, 1800.0),
    "Orosirian":        (1800.0, 2050.0),
    "Rhyacian":         (2050.0, 2300.0),
    "Siderian":         (2300.0, 2500.0),
    "Neoarchean":       (2500.0, 2800.0),
    "Mesoarchean":      (2800.0, 3200.0),
    "Paleoarchean":     (3200.0, 3600.0),
    "Eoarchean":        (3600.0, 4000.0),
}
