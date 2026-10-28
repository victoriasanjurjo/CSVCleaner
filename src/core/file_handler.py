"""
Módulo de manejo de archivos de entrada y salida (CSV, Excel y registros de auditoría TXT).
"""
import os
import csv
from datetime import datetime
from typing import Tuple, List, Optional, Any
from pathlib import Path
import pandas as pd

from .cleaner import CleaningReport


class FileHandler:
    """
    Gestor de lectura de archivos heterogéneos y exportación de datos limpios y registros TXT.
    """

    SUPPORTED_ENCODINGS = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    COMMON_DELIMITERS = [',', ';', '\t', '|']

    @classmethod
    def get_downloads_directory(cls) -> Path:
        """
        Retorna la ruta absoluta del directorio de Descargas del usuario.
        """
        downloads = Path.home() / "Downloads"
        if not downloads.exists():
            downloads.mkdir(parents=True, exist_ok=True)
        return downloads

    @classmethod
    def detect_csv_delimiter(cls, file_path: str, encoding: str = 'utf-8') -> str:
        """
        Detecta automáticamente el delimitador de un archivo CSV mediante análisis de muestra.
        """
        try:
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                sample = f.read(4096)
                if not sample:
                    return ','
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample, delimiters=cls.COMMON_DELIMITERS)
                return dialect.delimiter
        except Exception:
            return ','

    @classmethod
    def load_csv(cls, file_path: str, delimiter: Optional[str] = None) -> Tuple[pd.DataFrame, str, str]:
        """
        Carga un archivo CSV probando diferentes codificaciones y detectando el separador.

        :return: Tupla (DataFrame, encoding_usado, delimiter_usado)
        """
        last_error = None
        for enc in cls.SUPPORTED_ENCODINGS:
            try:
                sep = delimiter or cls.detect_csv_delimiter(file_path, encoding=enc)
                df = pd.read_csv(file_path, encoding=enc, sep=sep, low_memory=False)
                return df, enc, sep
            except Exception as e:
                last_error = e
                continue
        raise ValueError(f"No se pudo leer el archivo CSV con las codificaciones habituales: {last_error}")

    @classmethod
    def get_excel_sheets(cls, file_path: str) -> List[str]:
        """
        Retorna la lista de hojas disponibles en un archivo Excel garantizando el cierre del descriptor.
        """
        with pd.ExcelFile(file_path) as excel_file:
            return list(excel_file.sheet_names)

    @classmethod
    def load_excel(cls, file_path: str, sheet_name: Optional[str] = None) -> Tuple[pd.DataFrame, str]:
        """
        Carga una hoja de cálculo Excel en un DataFrame de pandas.

        :return: Tupla (DataFrame, nombre_de_hoja_cargada)
        """
        sheets = cls.get_excel_sheets(file_path)
        target_sheet = sheet_name if sheet_name in sheets else sheets[0]
        df = pd.read_excel(file_path, sheet_name=target_sheet)
        return df, target_sheet

    @classmethod
    def load_file(cls, file_path: str) -> Tuple[pd.DataFrame, dict]:
        """
        Punto de entrada universal para leer archivos CSV o Excel (1 archivo a la vez).
        """
        ext = Path(file_path).suffix.lower()
        metadata: dict[str, Any] = {"filepath": file_path, "filename": Path(file_path).name, "format": ext}

        if ext in ['.csv', '.txt']:
            df, enc, sep = cls.load_csv(file_path)
            metadata["encoding"] = enc
            metadata["delimiter"] = sep
            return df, metadata
        elif ext in ['.xlsx', '.xls']:
            sheets = cls.get_excel_sheets(file_path)
            df, loaded_sheet = cls.load_excel(file_path, sheets[0])
            metadata["sheets"] = sheets
            metadata["active_sheet"] = loaded_sheet
            return df, metadata
        else:
            raise ValueError(f"Formato de archivo no compatible: {ext}. Utilice .csv, .xlsx o .xls.")

    @classmethod
    def export_csv(cls, df: pd.DataFrame, output_path: str, delimiter: str = ',', encoding: str = 'utf-8', index: bool = False) -> str:
        """
        Guarda el DataFrame procesado en formato CSV.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        df.to_csv(output_path, sep=delimiter, encoding=encoding, index=index)
        return output_path

    @classmethod
    def export_excel(cls, df: pd.DataFrame, output_path: str, sheet_name: str = 'CleanedData', index: bool = False) -> str:
        """
        Guarda el DataFrame procesado en formato Excel (.xlsx).
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=index)
        return output_path

    @classmethod
    def export_txt_log(cls, report: CleaningReport, source_name: str, output_txt_path: str) -> str:
        """
        Genera un archivo simple .txt con el registro de cambios y la bitácora de acciones
        aplicadas sobre el archivo original.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_txt_path)), exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        diff_rows = report.rows_before - report.rows_after
        diff_cols = report.cols_before - report.cols_after
        diff_missing = report.missing_cells_before - report.missing_cells_after

        lines = [
            "=" * 70,
            "CSVCleaner - REGISTRO DE CAMBIOS Y ACCIONES DE LIMPIEZA",
            "=" * 70,
            f"Archivo original : {source_name}",
            f"Fecha y hora     : {timestamp}",
            "",
            "-" * 70,
            "1. RESUMEN ESTADÍSTICO DE TRANSFORMACIONES",
            "-" * 70,
            f"• Filas totales          : {report.rows_before} (antes) -> {report.rows_after} (después) | Diferencia: -{diff_rows}",
            f"• Columnas totales       : {report.cols_before} (antes) -> {report.cols_after} (después) | Diferencia: -{diff_cols}",
            f"• Celdas vacías (NaN)    : {report.missing_cells_before} (antes) -> {report.missing_cells_after} (después) | Corregidas/removidas: {diff_missing}",
            f"• Filas duplicadas       : {report.duplicates_removed} eliminadas",
            f"• Filas vacías           : {report.empty_rows_dropped} descartadas",
            f"• Columnas vacías        : {report.empty_cols_dropped} descartadas",
            "",
            "-" * 70,
            "2. BITÁCORA DETALLADA DE OPERACIONES REALIZADAS",
            "-" * 70,
        ]

        if report.operations_log:
            for i, op in enumerate(report.operations_log, start=1):
                lines.append(f"  {i}. {op}")
        else:
            lines.append("  (No se realizaron modificaciones sobre los datos)")

        lines.extend([
            "",
            "=" * 70,
            "Fin del registro de cambios.",
            "=" * 70,
            ""
        ])

        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return output_txt_path
