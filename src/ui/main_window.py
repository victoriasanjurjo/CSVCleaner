"""
Ventana principal de CSVCleaner construida con PySide6.
Filosofía MVP: Flujo lineal, limpio y sin fricciones.
Cargar archivo -> Previsualizar -> Limpiar con un clic -> Exportar.
"""
import os
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableView, QTabWidget,
    QFileDialog, QMessageBox, QFrame, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent

import pandas as pd

from ..core.cleaner import DataCleaner, CleaningOptions, CleaningReport
from ..core.file_handler import FileHandler
from .table_model import PandasTableModel


class MetricCard(QFrame):
    """Tarjeta minimalista clara para presentar métricas clave."""

    def __init__(self, title: str, value: str = "0"):
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)

        self.label_title = QLabel(title.upper())
        self.label_title.setObjectName("metric_label")

        self.label_value = QLabel(value)
        self.label_value.setObjectName("metric_value")

        layout.addWidget(self.label_title)
        layout.addWidget(self.label_value)

    def set_value(self, value: str):
        self.label_value.setText(value)


class DropZone(QFrame):
    """Área interactiva para arrastrar y soltar 1 archivo o abrir explorador."""

    def __init__(self, on_file_selected):
        super().__init__()
        self.on_file_selected = on_file_selected
        self.setObjectName("drop_zone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self.lbl_main = QLabel("Arrastra y suelta tu archivo CSV o Excel aquí")
        self.lbl_main.setStyleSheet("font-weight: 600; font-size: 13px; color: #27272A;")
        self.lbl_main.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_sub = QLabel("O haz clic para seleccionarlo de tu equipo (.csv, .xlsx, .xls)")
        self.lbl_sub.setObjectName("subtitle")
        self.lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.lbl_main)
        layout.addWidget(self.lbl_sub)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            default_dir = str(FileHandler.get_downloads_directory())
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar archivo CSV o Excel",
                default_dir,
                "Archivos Tabulares (*.csv *.xlsx *.xls);;Archivos CSV (*.csv);;Archivos Excel (*.xlsx *.xls)"
            )
            if file_path:
                self.on_file_selected(file_path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith(('.csv', '.xlsx', '.xls', '.txt')):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith(('.csv', '.xlsx', '.xls', '.txt')):
                self.on_file_selected(path)


class MainWindow(QMainWindow):
    """
    Ventana principal de CSVCleaner con diseño horizontal MVP.
    """

    def __init__(self, initial_file: Optional[str] = None):
        super().__init__()
        self.setWindowTitle("CSVCleaner")
        self.resize(1080, 700)
        self.setMinimumSize(800, 500)

        # Cargar ícono de la aplicación
        icon_path = Path(__file__).resolve().parent.parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Estado interno
        self.current_filepath: Optional[str] = None
        self.original_df: Optional[pd.DataFrame] = None
        self.cleaned_df: Optional[pd.DataFrame] = None
        self.last_report: Optional[CleaningReport] = None
        self.file_metadata: dict = {}

        self.init_ui()

        if initial_file and os.path.exists(initial_file):
            self.load_file(initial_file)

    def init_ui(self):
        """Inicializa la interfaz lineal y minimalista."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # 1. Cabecera superior
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        lbl_title = QLabel("CSVCleaner")
        lbl_title.setObjectName("title")
        lbl_sub = QLabel("Limpieza y normalización automática de datos")
        lbl_sub.setObjectName("subtitle")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.lbl_file_info = QLabel("Ningún archivo cargado")
        self.lbl_file_info.setStyleSheet("color: #71717A; font-size: 12px; font-weight: 500;")
        header_layout.addWidget(self.lbl_file_info)

        main_layout.addLayout(header_layout)

        # 2. Zona de carga (Drag and Drop)
        self.drop_zone = DropZone(self.load_file)
        main_layout.addWidget(self.drop_zone)

        # 3. Métricas clave (Tarjetas horizontales)
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(10)
        self.card_rows = MetricCard("Filas", "0")
        self.card_cols = MetricCard("Columnas", "0")
        self.card_duplicates = MetricCard("Duplicados", "0")
        self.card_missing = MetricCard("Celdas Nulas", "0")
        metrics_layout.addWidget(self.card_rows)
        metrics_layout.addWidget(self.card_cols)
        metrics_layout.addWidget(self.card_duplicates)
        metrics_layout.addWidget(self.card_missing)
        main_layout.addLayout(metrics_layout)

        # 4. Pestañas de previsualización ocupando el 100% del ancho
        self.tabs = QTabWidget()

        # Tab 1: Datos Originales
        self.table_original = QTableView()
        self.table_original.horizontalHeader().setStretchLastSection(True)
        self.table_original.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.model_original = PandasTableModel()
        self.table_original.setModel(self.model_original)
        self.tabs.addTab(self.table_original, "Datos Originales")

        # Tab 2: Datos Limpios
        self.table_cleaned = QTableView()
        self.table_cleaned.horizontalHeader().setStretchLastSection(True)
        self.table_cleaned.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.model_cleaned = PandasTableModel()
        self.table_cleaned.setModel(self.model_cleaned)
        self.tabs.addTab(self.table_cleaned, "Datos Limpios")

        main_layout.addWidget(self.tabs, 1)

        # 5. Barra inferior con botón central destacado de limpieza y exportaciones
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 4, 0, 0)
        bottom_layout.setSpacing(10)

        self.btn_reset = QPushButton("Cargar Nuevo Archivo")
        self.btn_reset.clicked.connect(self.reset_all)
        bottom_layout.addWidget(self.btn_reset)

        bottom_layout.addStretch()

        # Botón central y destacado para limpiar con un solo clic
        self.btn_clean = QPushButton("✨ Limpiar Datos Automáticamente")
        self.btn_clean.setObjectName("primary_button")
        self.btn_clean.setEnabled(False)
        self.btn_clean.clicked.connect(self.process_cleaning)
        bottom_layout.addWidget(self.btn_clean)

        bottom_layout.addStretch()

        self.btn_export_excel = QPushButton("Exportar como Excel (.xlsx)")
        self.btn_export_excel.setEnabled(False)
        self.btn_export_excel.clicked.connect(lambda: self.export_data("excel"))
        bottom_layout.addWidget(self.btn_export_excel)

        self.btn_export_csv = QPushButton("Exportar como CSV (.csv)")
        self.btn_export_csv.setEnabled(False)
        self.btn_export_csv.clicked.connect(lambda: self.export_data("csv"))
        bottom_layout.addWidget(self.btn_export_csv)

        main_layout.addLayout(bottom_layout)

        # Barra de estado
        self.statusBar().showMessage("Listo. Seleccione o arrastre un archivo para comenzar.")

    # --- Flujo de Carga, Limpieza y Exportación ---

    def load_file(self, file_path: str):
        """Carga y procesa un archivo CSV o Excel."""
        try:
            self.statusBar().showMessage(f"Cargando archivo: {Path(file_path).name}...")
            df, metadata = FileHandler.load_file(file_path)

            self.current_filepath = file_path
            self.file_metadata = metadata
            self.original_df = df
            self.cleaned_df = None
            self.last_report = None

            # Actualizar cabecera informativa
            name = metadata.get("filename", Path(file_path).name)
            enc = metadata.get("encoding", "")
            sep = metadata.get("delimiter", "")
            info_str = f"Archivo: {name}"
            if enc:
                info_str += f" | {enc.upper()}"
            if sep:
                info_str += f" | Sep: '{sep}'"
            self.lbl_file_info.setText(info_str)

            # Cargar datos en tabla original y reiniciar tabla limpia
            self.model_original.set_data(self.original_df)
            self.model_cleaned.set_data(pd.DataFrame())

            # Actualizar métricas del original
            self._update_metrics(self.original_df)

            # Habilitar botón de limpieza y deshabilitar exportaciones previas
            self.btn_clean.setEnabled(True)
            self.btn_export_csv.setEnabled(False)
            self.btn_export_excel.setEnabled(False)

            self.tabs.setCurrentIndex(0)
            self.statusBar().showMessage(f"Archivo cargado: {len(df)} filas, {len(df.columns)} columnas.")

        except Exception as e:
            QMessageBox.critical(self, "Error al cargar archivo", f"No se pudo abrir el archivo seleccionado:\n{str(e)}")
            self.statusBar().showMessage("Error al cargar el archivo.")

    def _update_metrics(self, df: pd.DataFrame):
        """Refresca las tarjetas de resumen numérico."""
        if df is None or df.empty:
            self.card_rows.set_value("0")
            self.card_cols.set_value("0")
            self.card_duplicates.set_value("0")
            self.card_missing.set_value("0")
            return

        rows = len(df)
        cols = len(df.columns)
        duplicates = int(df.duplicated().sum())
        missing = int(df.isna().sum().sum())

        self.card_rows.set_value(f"{rows:,}")
        self.card_cols.set_value(f"{cols:,}")
        self.card_duplicates.set_value(f"{duplicates:,}")
        self.card_missing.set_value(f"{missing:,}")

    def process_cleaning(self):
        """
        Ejecuta la limpieza con reglas automáticas predeterminadas (MVP).
        El usuario no necesita configurar nada manualmente.
        """
        if self.original_df is None:
            return

        # Reglas fijas predeterminadas (a prueba de errores)
        options = CleaningOptions(
            remove_duplicates=True,
            drop_empty_rows=True,
            drop_empty_cols=True,
            trim_whitespace=True,
            clean_headers=True,
            handle_missing="none",
            strip_accents=True,
            selected_columns=None
        )

        try:
            cleaned_df, report = DataCleaner.clean(self.original_df, options)
            self.cleaned_df = cleaned_df
            self.last_report = report

            # Refrescar modelo limpio
            self.model_cleaned.set_data(self.cleaned_df)

            # Refrescar métricas con el dataset limpio
            self._update_metrics(self.cleaned_df)

            # Habilitar exportaciones
            self.btn_export_csv.setEnabled(True)
            self.btn_export_excel.setEnabled(True)

            # Cambiar a la pestaña de datos limpios
            self.tabs.setCurrentIndex(1)

            self.statusBar().showMessage(
                f"Limpieza completada: {report.rows_after} filas y {len(cleaned_df.columns)} columnas conservadas."
            )

        except Exception as e:
            QMessageBox.critical(self, "Error durante la limpieza", f"Ocurrió un error inesperado:\n{str(e)}")

    def export_data(self, file_format: str):
        """
        Exporta el archivo limpio (CSV o Excel) y genera automáticamente
        el archivo .txt con el registro de cambios en la carpeta de Descargas.
        """
        if self.cleaned_df is None or self.last_report is None:
            QMessageBox.warning(self, "Aviso", "Primero debe ejecutar la limpieza de datos.")
            return

        downloads_dir = FileHandler.get_downloads_directory()
        stem = Path(self.current_filepath).stem if self.current_filepath else "datos"
        source_name = Path(self.current_filepath).name if self.current_filepath else "datos_originales"

        default_file_name = f"{stem}_limpio"

        if file_format == "csv":
            default_path = str(downloads_dir / f"{default_file_name}.csv")
            path, _ = QFileDialog.getSaveFileName(
                self, "Exportar CSV Limpio", default_path, "Archivo CSV (*.csv)"
            )
            if not path:
                return
            FileHandler.export_csv(self.cleaned_df, path)

        elif file_format == "excel":
            default_path = str(downloads_dir / f"{default_file_name}.xlsx")
            path, _ = QFileDialog.getSaveFileName(
                self, "Exportar Excel Limpio", default_path, "Libro de Excel (*.xlsx)"
            )
            if not path:
                return
            FileHandler.export_excel(self.cleaned_df, path)
        else:
            return

        # Generar automáticamente el archivo TXT con el registro de cambios junto al archivo limpio
        out_parent = Path(path).parent
        clean_stem = Path(path).stem
        txt_path = str(out_parent / f"{clean_stem}_registro_cambios.txt")
        FileHandler.export_txt_log(self.last_report, source_name, txt_path)

        msg = (
            f"Se han generado exitosamente los 2 archivos en:\n\n"
            f"1. Archivo limpio: {Path(path).name}\n"
            f"2. Registro de cambios: {Path(txt_path).name}\n\n"
            f"Ubicación: {out_parent}"
        )
        QMessageBox.information(self, "Exportación Exitosa", msg)
        self.statusBar().showMessage(f"Archivos exportados exitosamente en {out_parent.name}")

    def reset_all(self):
        """Reinicia el estado de la aplicación para procesar un nuevo archivo."""
        self.current_filepath = None
        self.original_df = None
        self.cleaned_df = None
        self.last_report = None
        self.file_metadata = {}

        self.model_original.set_data(pd.DataFrame())
        self.model_cleaned.set_data(pd.DataFrame())

        self.lbl_file_info.setText("Ningún archivo cargado")
        self._update_metrics(None)
        self.btn_clean.setEnabled(False)
        self.btn_export_csv.setEnabled(False)
        self.btn_export_excel.setEnabled(False)

        self.tabs.setCurrentIndex(0)
        self.statusBar().showMessage("Listo para cargar un nuevo archivo.")
