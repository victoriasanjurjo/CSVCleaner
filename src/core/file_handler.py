"""
Módulo de manejo de archivos de entrada y salida (CSV, Excel y reportes PDF).
"""
import os
import csv
from typing import Tuple, List, Optional, Any
from pathlib import Path
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.units import inch

from .cleaner import CleaningReport


class FileHandler:
    """
    Gestor de lectura de archivos heterogéneos y exportación de datos limpios y reportes.
    """

    SUPPORTED_ENCODINGS = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    COMMON_DELIMITERS = [',', ';', '\t', '|']

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
        Punto de entrada universal para leer archivos CSV o Excel.
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
    def generate_pdf_report(cls, report: CleaningReport, source_name: str, output_pdf_path: str) -> str:
        """
        Genera un reporte ejecutivo en PDF estructurado con la bitácora y métricas de limpieza.
        Diseño formal y monocromático alineado a las directrices de la app.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)
        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        
        # Estilos tipográficos monocromáticos
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#09090B'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#52525B'),
            spaceAfter=15
        )
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=colors.HexColor('#18181B'),
            spaceBefore=14,
            spaceAfter=8
        )
        cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#27272A')
        )
        cell_header_style = ParagraphStyle(
            'TableHeadCell',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#FFFFFF')
        )

        elements = []

        # Título y cabecera
        elements.append(Paragraph("CSVCleaner - Reporte de Auditoría y Limpieza", title_style))
        elements.append(Paragraph(f"Archivo procesado: <b>{source_name}</b>", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E4E4E7'), spaceBefore=2, spaceAfter=14))

        # Sección 1: Métricas de Transformación
        elements.append(Paragraph("1. Resumen Ejecutivo de Métricas", section_style))

        metrics_data = [
            [Paragraph("Métrica", cell_header_style), Paragraph("Antes", cell_header_style), Paragraph("Después", cell_header_style), Paragraph("Diferencia", cell_header_style)],
            [Paragraph("Total de Filas", cell_style), Paragraph(str(report.rows_before), cell_style), Paragraph(str(report.rows_after), cell_style), Paragraph(f"-{report.rows_before - report.rows_after}", cell_style)],
            [Paragraph("Total de Columnas", cell_style), Paragraph(str(report.cols_before), cell_style), Paragraph(str(report.cols_after), cell_style), Paragraph(f"-{report.cols_before - report.cols_after}", cell_style)],
            [Paragraph("Celdas Vacías (NaN)", cell_style), Paragraph(str(report.missing_cells_before), cell_style), Paragraph(str(report.missing_cells_after), cell_style), Paragraph(f"-{report.missing_cells_before - report.missing_cells_after}", cell_style)],
            [Paragraph("Filas Duplicadas Removidas", cell_style), Paragraph("-", cell_style), Paragraph(str(report.duplicates_removed), cell_style), Paragraph(str(report.duplicates_removed), cell_style)],
            [Paragraph("Filas Vacías Descartadas", cell_style), Paragraph("-", cell_style), Paragraph(str(report.empty_rows_dropped), cell_style), Paragraph(str(report.empty_rows_dropped), cell_style)],
            [Paragraph("Columnas Vacías Descartadas", cell_style), Paragraph("-", cell_style), Paragraph(str(report.empty_cols_dropped), cell_style), Paragraph(str(report.empty_cols_dropped), cell_style)],
        ]

        metric_table = Table(metrics_data, colWidths=[200, 100, 100, 100])
        metric_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#18181B')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E4E4E7')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F4F4F5')]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(metric_table)
        elements.append(Spacer(1, 15))

        # Sección 2: Bitácora de Acciones
        elements.append(Paragraph("2. Registro Cronológico de Operaciones", section_style))
        if report.operations_log:
            log_data = [[Paragraph(f"• {log}", cell_style)] for log in report.operations_log]
            log_table = Table(log_data, colWidths=[500])
            log_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FAFAFA')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E4E4E7')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(log_table)
        else:
            elements.append(Paragraph("No se registraron transformaciones en los datos.", cell_style))

        doc.build(elements)
        return output_pdf_path
