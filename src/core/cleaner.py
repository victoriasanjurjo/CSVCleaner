"""
Módulo de limpieza y transformación de datos tabulares (CSV y Excel).
Proporciona operaciones parametrizadas y métricas de antes/después.
"""
from dataclasses import dataclass, field
from typing import Any, List, Optional
import unicodedata
import re
import pandas as pd
import numpy as np


@dataclass
class CleaningOptions:
    """Opciones de configuración para el proceso de limpieza."""
    remove_duplicates: bool = True
    drop_empty_rows: bool = True
    drop_empty_cols: bool = True
    trim_whitespace: bool = True
    clean_headers: bool = True
    handle_missing: str = "none"      # 'none', 'drop_any', 'fill_value'
    missing_fill_value: str = ""
    strip_accents: bool = True
    selected_columns: Optional[List[str]] = None


@dataclass
class CleaningReport:
    """Resumen estadístico y bitácora del proceso de limpieza."""
    rows_before: int = 0
    rows_after: int = 0
    cols_before: int = 0
    cols_after: int = 0
    duplicates_removed: int = 0
    empty_rows_dropped: int = 0
    empty_cols_dropped: int = 0
    missing_cells_before: int = 0
    missing_cells_after: int = 0
    operations_log: List[str] = field(default_factory=list)


class DataCleaner:
    """
    Motor encargado de ejecutar las transformaciones y limpiezas sobre un DataFrame.
    """

    @staticmethod
    def normalize_header(name: Any, strip_accents: bool = True) -> str:
        """
        Normaliza el nombre de una columna forzando internamente el formato snake_case.

        :param name: Nombre original de la columna.
        :param strip_accents: Si es True, elimina acentos y diacríticos.
        :return: Nombre de columna normalizado en snake_case.
        """
        text = str(name).strip()
        if not text:
            return "unnamed_column"

        if strip_accents:
            # Normalizar caracteres unicode descomponiendo tildes
            nfkd = unicodedata.normalize('NFKD', text)
            text = "".join([c for c in nfkd if not unicodedata.combining(c)])

        # Reemplazar caracteres no alfanuméricos por guiones bajos
        text = re.sub(r'[\s\-_./\\+]+', '_', text)
        # Insertar guión bajo antes de mayúsculas intermedias (CamelCase a snake_case)
        text = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text)
        text = re.sub(r'[^a-zA-Z0-9_]', '', text)
        text = re.sub(r'_+', '_', text).strip('_').lower()
        return text if text else "column"

    @classmethod
    def clean(cls, df: pd.DataFrame, options: CleaningOptions) -> tuple[pd.DataFrame, CleaningReport]:
        """
        Ejecuta la secuencia de transformaciones de limpieza sobre el DataFrame.

        :param df: DataFrame original de pandas.
        :param options: Instancia de CleaningOptions con las operaciones a aplicar.
        :return: Tupla con (DataFrame limpio, CleaningReport detallado).
        """
        report = CleaningReport()
        report.rows_before = len(df)
        report.cols_before = len(df.columns)
        report.missing_cells_before = int(df.isna().sum().sum())

        cleaned = df.copy()

        # 1. Filtrado de columnas seleccionadas si se especificó
        if options.selected_columns is not None:
            cols_to_keep = [c for c in options.selected_columns if c in cleaned.columns]
            if not cols_to_keep:
                raise ValueError("Debe seleccionar al menos una columna válida para conservar.")
            dropped_count = report.cols_before - len(cols_to_keep)
            cleaned = cleaned[cols_to_keep]
            report.operations_log.append(
                f"Selección de columnas: {len(cols_to_keep)} conservadas, {dropped_count} descartadas."
            )

        # 2. Normalización de cabeceras forzada a snake_case
        if options.clean_headers:
            new_cols = []
            seen = set()
            for col in cleaned.columns:
                norm = cls.normalize_header(col, strip_accents=options.strip_accents)
                # Manejar posibles duplicados en nombres generados
                orig_norm = norm
                counter = 1
                while norm in seen:
                    norm = f"{orig_norm}_{counter}"
                    counter += 1
                seen.add(norm)
                new_cols.append(norm)
            cleaned.columns = new_cols
            report.operations_log.append("Cabeceras normalizadas al estilo snake_case.")

        # 3. Eliminar filas y columnas completamente vacías
        if options.drop_empty_rows:
            initial_rows = len(cleaned)
            cleaned = cleaned.dropna(how='all')
            report.empty_rows_dropped = initial_rows - len(cleaned)
            if report.empty_rows_dropped > 0:
                report.operations_log.append(f"Filas completamente vacías eliminadas: {report.empty_rows_dropped}.")

        if options.drop_empty_cols:
            initial_cols = len(cleaned.columns)
            cleaned = cleaned.dropna(axis=1, how='all')
            report.empty_cols_dropped = initial_cols - len(cleaned.columns)
            if report.empty_cols_dropped > 0:
                report.operations_log.append(f"Columnas completamente vacías eliminadas: {report.empty_cols_dropped}.")

        # 4. Trimming de espacios en columnas de texto
        if options.trim_whitespace:
            str_cols = cleaned.select_dtypes(include=['object', 'string']).columns
            for col in str_cols:
                cleaned[col] = cleaned[col].map(
                    lambda x: re.sub(r'\s+', ' ', x.strip()) if isinstance(x, str) else x
                )
            report.operations_log.append("Espacios en blanco innecesarios recortados en campos de texto.")

        # 5. Eliminación de filas duplicadas
        if options.remove_duplicates:
            initial_rows = len(cleaned)
            cleaned = cleaned.drop_duplicates()
            report.duplicates_removed = initial_rows - len(cleaned)
            if report.duplicates_removed > 0:
                report.operations_log.append(f"Filas duplicadas eliminadas: {report.duplicates_removed}.")

        # 6. Tratamiento de valores faltantes (NaN / None)
        if options.handle_missing == "drop_any":
            initial_rows = len(cleaned)
            cleaned = cleaned.dropna(how='any')
            dropped = initial_rows - len(cleaned)
            report.operations_log.append(f"Filas con algún valor nulo eliminadas: {dropped}.")
        elif options.handle_missing == "fill_value":
            fill_val = options.missing_fill_value
            # Intentar convertir valor numérico si procede
            try:
                num_val = float(fill_val)
                if num_val.is_integer():
                    num_val = int(num_val)
            except ValueError:
                num_val = None

            for col in cleaned.columns:
                if num_val is not None and pd.api.types.is_numeric_dtype(cleaned[col]):
                    cleaned[col] = cleaned[col].fillna(num_val)
                else:
                    if cleaned[col].isna().any():
                        cleaned[col] = cleaned[col].astype(object).fillna(fill_val)
            report.operations_log.append(f"Valores nulos rellenados con: '{fill_val}'.")

        # Métricas finales
        report.rows_after = len(cleaned)
        report.cols_after = len(cleaned.columns)
        report.missing_cells_after = int(cleaned.isna().sum().sum())

        return cleaned, report
