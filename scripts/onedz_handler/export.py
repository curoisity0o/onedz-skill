"""
OneDZ Handler — 导出与地理集成 (Export Module)

支持 CSV / JSON / Excel / GeoJSON 多格式导出。
"""

import json
from pathlib import Path
from typing import Optional, Union

import polars as pl
import numpy as np

from .config import Cols, OneDZConfig


class Export:
    """多格式数据导出。"""

    def __init__(self, config: OneDZConfig) -> None:
        self.config = config
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, filename: str, suffix: str) -> Path:
        """解析输出路径。"""
        if not filename.endswith(suffix):
            filename += suffix
        return self.config.output_dir / filename

    # ──────────────────── CSV ─────────────────────────────────────
    def to_csv(
        self,
        df: pl.DataFrame,
        filename: str = "onedz_export.csv",
    ) -> Path:
        """
        导出 CSV。

        Parameters
        ----------
        df : pl.DataFrame
        filename : str

        Returns
        -------
        Path — 输出文件路径
        """
        path = self._resolve_path(filename, ".csv")
        df.write_csv(path)
        print(f"[Export] CSV → {path} ({df.height} 行)")
        return path

    # ──────────────────── JSON ────────────────────────────────────
    def to_json(
        self,
        df: pl.DataFrame,
        filename: str = "onedz_export.json",
        orient: str = "records",
    ) -> Path:
        """
        导出 JSON。

        Parameters
        ----------
        df : pl.DataFrame
        filename : str
        orient : str
            "records" (列表 of dict) 或 "columns" (列式)

        Returns
        -------
        Path
        """
        path = self._resolve_path(filename, ".json")
        df.write_json(path, row_oriented=(orient == "records"))
        print(f"[Export] JSON → {path} ({df.height} 行)")
        return path

    # ──────────────────── Excel ───────────────────────────────────
    def to_excel(
        self,
        df: pl.DataFrame,
        filename: str = "onedz_export.xlsx",
        sheet_name: str = "OneDZ",
    ) -> Path:
        """
        导出 Excel (.xlsx)。

        Parameters
        ----------
        df : pl.DataFrame
        filename : str
        sheet_name : str

        Returns
        -------
        Path
        """
        path = self._resolve_path(filename, ".xlsx")
        # Polars → Pandas → Excel (openpyxl)
        try:
            pdf = df.to_pandas()
            pdf.to_excel(path, sheet_name=sheet_name, index=False)
        except ImportError:
            # 回退: 导出 CSV 格式的 xlsx
            raise ImportError("Excel 导出需要 openpyxl: pip install openpyxl")
        print(f"[Export] Excel → {path} ({df.height} 行)")
        return path

    # ──────────────────── GeoJSON ─────────────────────────────────
    def to_geojson(
        self,
        df: pl.DataFrame,
        filename: str = "onedz_export.geojson",
        lat_col: str = Cols.LATITUDE,
        lon_col: str = Cols.LONGITUDE,
        properties: Optional[list] = None,
    ) -> Path:
        """
        导出 GeoJSON（兼容 QGIS / ArcGIS）。

        Parameters
        ----------
        df : pl.DataFrame
        filename : str
        lat_col, lon_col : str
            经纬度列名
        properties : list, optional
            要包含的属性列名列表。None 则包含所有列

        Returns
        -------
        Path
        """
        if lat_col not in df.columns or lon_col not in df.columns:
            raise ValueError(f"数据中缺少经纬度列: {lat_col}, {lon_col}")

        path = self._resolve_path(filename, ".geojson")

        valid = df.filter(
            pl.col(lat_col).is_not_null() & pl.col(lon_col).is_not_null()
        )

        prop_cols = properties or [c for c in valid.columns if c not in (lat_col, lon_col)]

        features = []
        for row in valid.iter_rows(named=True):
            props = {}
            for c in prop_cols:
                if c in row:
                    val = row[c]
                    # 处理 polars/numpy 类型
                    if isinstance(val, (np.integer,)):
                        val = int(val)
                    elif isinstance(val, (np.floating,)):
                        val = float(val)
                    elif isinstance(val, (np.bool_,)):
                        val = bool(val)
                    elif val is None:
                        continue
                    props[c] = val

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row[lon_col]), float(row[lat_col])],
                },
                "properties": props,
            }
            features.append(feature)

        geojson = {
            "type": "FeatureCollection",
            "features": features,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)

        print(f"[Export] GeoJSON → {path} ({len(features)} 个要素)")
        return path

    # ──────────────────── Shapefile (via GeoPandas) ───────────────
    def to_shapefile(
        self,
        df: pl.DataFrame,
        filename: str = "onedz_export.shp",
        lat_col: str = Cols.LATITUDE,
        lon_col: str = Cols.LONGITUDE,
    ) -> Path:
        """
        导出 Shapefile（需 geopandas）。

        Parameters
        ----------
        df : pl.DataFrame
        filename : str
        lat_col, lon_col : str

        Returns
        -------
        Path
        """
        try:
            import geopandas as gpd
            from shapely.geometry import Point
        except ImportError:
            raise ImportError("Shapefile 导出需要 geopandas: pip install geopandas shapely")

        if lat_col not in df.columns or lon_col not in df.columns:
            raise ValueError(f"数据中缺少经纬度列")

        valid = df.filter(
            pl.col(lat_col).is_not_null() & pl.col(lon_col).is_not_null()
        )
        pdf = valid.to_pandas()
        geometry = [Point(xy) for xy in zip(pdf[lon_col], pdf[lat_col])]
        gdf = gpd.GeoDataFrame(pdf, geometry=geometry, crs="EPSG:4326")

        path = self._resolve_path(filename, ".shp")
        gdf.to_file(path)
        print(f"[Export] Shapefile → {path} ({len(gdf)} 个要素)")
        return path

    # ──────────────────── 通用导出 ───────────────────────────────
    def export(
        self,
        df: pl.DataFrame,
        filename: str,
        fmt: Optional[str] = None,
        **kwargs,
    ) -> Path:
        """
        通用导出接口（根据文件扩展名自动选择格式）。

        Parameters
        ----------
        df : pl.DataFrame
        filename : str
        fmt : str, optional
            "csv" | "json" | "excel" | "geojson" | "shp"

        Returns
        -------
        Path
        """
        if fmt is None:
            ext = Path(filename).suffix.lower()
            fmt_map = {
                ".csv": "csv",
                ".json": "json",
                ".xlsx": "excel",
                ".xls": "excel",
                ".geojson": "geojson",
                ".shp": "shp",
            }
            fmt = fmt_map.get(ext)
            if fmt is None:
                raise ValueError(f"无法识别的文件格式: {ext}")

        dispatch = {
            "csv": self.to_csv,
            "json": self.to_json,
            "excel": self.to_excel,
            "geojson": self.to_geojson,
            "shp": self.to_shapefile,
        }
        func = dispatch.get(fmt)
        if func is None:
            raise ValueError(f"不支持的格式: {fmt}")

        return func(df, filename=filename, **kwargs)
