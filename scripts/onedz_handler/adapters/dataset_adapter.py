"""
OneDZ Dataset Adapter — 数据集版本适配层

将不同版本的外部列名/文件格式统一映射为内部标准 (Cols.* 常量)。
新数据集只需添加对应的 JSON 配置文件，无需修改 Python 代码。
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

import polars as pl


# Lu-Hf 标准列名（这些列不在 Cols 类中，用固定映射）
LUHF_STANDARD_NAMES = {
    "HF_176_177": "176Hf/177Hf",
    "HF_176_177_1S": "176Hf/177Hf_1sigma",
    "HF_176_177_2S": "176Hf/177Hf_2sigma",
    "LU_176_177": "176Lu/177Hf",
    "LU_176_177_1S": "176Lu/177Hf_1sigma",
    "LU_176_177_2S": "176Lu/177Hf_2sigma",
    "EPSILON_HF_0": "εHf(0)",
    "EPSILON_HF_0_1S": "εHf(0)_1sigma",
    "EPSILON_HF_0_2S": "εHf(0)_2sigma",
    "EPSILON_HF_T": "εHf(t)",
    "EPSILON_HF_T_1S": "εHf(t)_1sigma",
    "EPSILON_HF_T_2S": "εHf(t)_2sigma",
    "TDM1": "TDM1 (Ma)",
    "TDM1_1S": "TDM1 (Ma)_1sigma",
    "TDM1_2S": "TDM1 (Ma)_2sigma",
    "TDM2": "TDM2 (Ma)",
    "TDM2_1S": "TDM2 (Ma)_1sigma",
    "TDM2_2S": "TDM2 (Ma)_2sigma",
    "UPB_AGE": "U-Pb Age (Ma)",
    "UPB_AGE_1S": "U-Pb Age (Ma)_1σ",
    "UPB_AGE_2S": "U-Pb Age (Ma)_2σ",
}


class DatasetAdapter:
    """数据集适配器：读取 JSON 配置，执行列名映射和文件加载。"""

    def __init__(self, config_dir: Optional[Path] = None):
        self._adapters: Dict[str, dict] = {}
        self._active_version: Optional[str] = None
        self._active_config: Optional[dict] = None
        self._column_rename_map: Dict[str, str] = {}  # {外部名: 标准名}
        self._luhf_rename_map: Dict[str, str] = {}
        self._luhf_extra_aliases: Dict[str, str] = {}

        if config_dir is None:
            config_dir = Path(__file__).parent
        self._config_dir = config_dir
        self._load_all_configs()

    def _load_all_configs(self):
        """加载所有 JSON 配置文件。"""
        for f in sorted(self._config_dir.glob("v*.json")):
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
                self._adapters[data["version"]] = data

    def detect_version(self, csv_dir: Path) -> Optional[str]:
        """自动检测数据集版本：读取 CSV 前几行，根据列名模式匹配。"""
        csv_files = list(csv_dir.glob("*.csv"))
        if not csv_files:
            for subdir in csv_dir.iterdir():
                if subdir.is_dir():
                    csv_files.extend(subdir.glob("*.csv"))
                    if csv_files:
                        break

        if not csv_files:
            return None

        try:
            df_sample = pl.read_csv(csv_files[0], n_rows=0, ignore_errors=True)
            columns = set(df_sample.columns)
        except Exception:
            return None

        best_version = None
        best_score = 0

        for version, config in self._adapters.items():
            score = 0
            col_map = config.get("column_map", {})
            for external_name in col_map.values():
                if external_name and external_name in columns:
                    score += 1

            if score > best_score:
                best_score = score
                best_version = version

        return best_version

    def activate(self, version: str):
        """激活指定版本的适配器，生成列名映射表。"""
        if version not in self._adapters:
            raise ValueError(
                f"未找到数据集版本 '{version}' 的配置。\n"
                f"可用版本: {list(self._adapters.keys())}"
            )

        self._active_version = version
        self._active_config = self._adapters[version]

        # 生成 U-Pb {外部列名: Cols标准名} 映射
        self._column_rename_map = {}
        from ..config import Cols

        for cols_attr, external_name in self._active_config.get("column_map", {}).items():
            if external_name is None:
                continue  # 新数据集移除的列
            standard_name = getattr(Cols, cols_attr, None)
            if standard_name and external_name != standard_name:
                self._column_rename_map[external_name] = standard_name

        # 生成 Lu-Hf {外部列名: 标准名} 映射
        self._luhf_rename_map = {}
        for key, external_name in self._active_config.get("luhf_column_map", {}).items():
            std = LUHF_STANDARD_NAMES.get(key)
            if std and external_name and external_name != std:
                self._luhf_rename_map[external_name] = std

        # Lu-Hf 额外别名（如 Lu-Hf CSV 中 Web Link, Latitud 等）
        self._luhf_extra_aliases = {}
        for cols_attr, external_name in self._active_config.get("luhf_extra_aliases", {}).items():
            standard_name = getattr(Cols, cols_attr, None)
            if standard_name and external_name != standard_name:
                self._luhf_extra_aliases[external_name] = standard_name

        print(f"[Adapter] 激活数据集版本: {version}")
        print(f"[Adapter]   U-Pb 列映射: {len(self._column_rename_map)} 个")
        print(f"[Adapter]   Lu-Hf 列映射: {len(self._luhf_rename_map)} 个")

    def auto_activate(self, csv_dir: Path) -> str:
        """自动检测并激活数据集版本。"""
        version = self.detect_version(csv_dir)
        if version is None:
            raise FileNotFoundError(
                f"无法自动检测 {csv_dir} 中的数据集版本。\n"
                f"请手动指定版本或添加对应的 JSON 配置。"
            )
        self.activate(version)
        return version

    @property
    def is_active(self) -> bool:
        return self._active_version is not None

    def normalize(self, df: pl.DataFrame, is_luhf: bool = False) -> pl.DataFrame:
        """将 DataFrame 的外部列名重命名为标准名。"""
        rename_map = dict(self._column_rename_map)

        # Lu-Hf 特有列映射
        if is_luhf:
            rename_map.update(self._luhf_rename_map)
            rename_map.update(self._luhf_extra_aliases)

        existing = set(df.columns)
        actual_rename = {ext: std for ext, std in rename_map.items() if ext in existing}

        if actual_rename:
            df = df.rename(actual_rename)
        return df

    def normalize_lazy(self, lf: pl.LazyFrame, is_luhf: bool = False) -> pl.LazyFrame:
        """LazyFrame 版本的列名标准化。"""
        rename_map = dict(self._column_rename_map)

        if is_luhf:
            rename_map.update(self._luhf_rename_map)
            rename_map.update(self._luhf_extra_aliases)

        schema = lf.collect_schema()
        existing = set(schema.names())
        actual_rename = {ext: std for ext, std in rename_map.items() if ext in existing}

        if actual_rename:
            lf = lf.rename(actual_rename)
        return lf

    @property
    def file_format(self) -> dict:
        if self._active_config is None:
            return {}
        return self._active_config.get("file_format", {})

    @property
    def is_split_mode(self) -> bool:
        return self.file_format.get("mode") == "split"

    @property
    def join_config(self) -> dict:
        if self._active_config is None:
            return {}
        return self._active_config.get("join_config", {})

    def get_composite_keys(self) -> List[str]:
        """获取复合 join 键列表。"""
        jc = self.join_config
        if jc.get("strategy") == "composite":
            return jc.get("composite_keys", [])
        return []

    def list_versions(self) -> List[str]:
        """列出所有可用的数据集版本。"""
        return list(self._adapters.keys())
