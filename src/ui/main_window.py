"""
Ventana principal de CSVCleaner construida con PySide6.
Proporciona carga por arrastrar y soltar (1 archivo a la vez), previsualización
en tiempo real (Datos Originales y Datos Limpios), configuración de transformaciones
en la barra lateral izquierda y exportación dual a la carpeta de Descargas (Archivo limpio + Registro TXT).
"""
import os
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QCheckBox, QComboBox, QLineEdit,
    QTableView, QTabWidget, QFileDialog, QMessageBox, QFrame,
    QHeaderView, QListWidget, QListWidgetItem, QAbstractItemView, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent

import pandas as pd

from ..core.cleaner import DataCleaner, CleaningOptions, CleaningReport
from ..core.file_handler import FileHandler
from .table_model import PandasTableModel


class MetricCard(QFrame):
    """Tarjeta monocromática minimalista para presentar métricas clave."""

    def __init__(self, title: str, value: str = "0"):
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
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
        layout.setSpacing(6)

        self.lbl_main = QLabel("Arrastra y suelta tu archivo CSV o Excel aquí (1 archivo a la vez)")
        self.lbl_main.setStyleSheet("font-weight: 600; font-size: 14px; color: #18181B;")
        self.lbl_main.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_sub = QLabel("O haz clic para buscar en tu equipo (.csv, .xlsx, .xls)")
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
    Ventana principal de la aplicación CSVCleaner.
    """

    def __init__(self, initial_file: Optional[str] = None):
        super().__init__()
        self.setWindowTitle("CSVCleaner - Depuración de Datos")
        self.resize(1120, 740)
        self.setMinimumSize(850, 550)

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
        """Inicializa la disposición de los componentes y controladores."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(14)

        # 1. Cabecera superior
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        lbl_title = QLabel("CSVCleaner")
        lbl_title.setObjectName("title")
        lbl_sub = QLabel("Herramienta minimalista para inspección, limpieza y normalización de CSV y Excel")
        lbl_sub.setObjectName("subtitle")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.lbl_file_info = QLabel("Ningún archivo cargado")
        self.lbl_file_info.setStyleSheet("color: #71717A; font-size: 12px; font-weight: 500;")
        header_layout.addWidget(self.lbl_file_info)

        # Selector de hoja si es Excel
        self.cmb_sheet = QComboBox()
        self.cmb_sheet.setVisible(False)
        self.cmb_sheet.currentIndexChanged.connect(self._on_sheet_changed)
        header_layout.addWidget(self.cmb_sheet)

        main_layout.addLayout(header_layout)

        # 2. Zona de carga (Drag and Drop - 1 archivo a la vez)
        self.drop_zone = DropZone(self.load_file)
        main_layout.addWidget(self.drop_zone)

        # 3. Métricas clave (Fila de tarjetas monocromáticas)
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

        # 4. Cuerpo central: Splitter (Opciones a la izquierda, Vistas a la derecha)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # Panel izquierdo: Opciones de limpieza con QScrollArea
        options_card = QFrame()
        options_card.setObjectName("card")
        options_layout = QVBoxLayout(options_card)
        options_layout.setContentsMargins(14, 14, 14, 14)
        options_layout.setSpacing(10)

        # 4.1. Sección Selección de Columnas
        lbl_cols_sec = QLabel("Columnas a Conservar")
        lbl_cols_sec.setObjectName("section_heading")
        options_layout.addWidget(lbl_cols_sec)

        self.lbl_cols_count = QLabel("0 seleccionadas")
        self.lbl_cols_count.setObjectName("subtitle")
        options_layout.addWidget(self.lbl_cols_count)

        # Botones rápidos: [Todas] [Ninguna] [Invertir]
        col_btn_layout = QHBoxLayout()
        col_btn_layout.setSpacing(4)

        self.btn_select_all_cols = QPushButton("Todas")
        self.btn_select_all_cols.setObjectName("compact_btn")
        self.btn_select_all_cols.clicked.connect(self._select_all_columns)
        col_btn_layout.addWidget(self.btn_select_all_cols)

        self.btn_select_none_cols = QPushButton("Ninguna")
        self.btn_select_none_cols.setObjectName("compact_btn")
        self.btn_select_none_cols.clicked.connect(self._select_none_columns)
        col_btn_layout.addWidget(self.btn_select_none_cols)

        self.btn_invert_cols = QPushButton("Invertir")
        self.btn_invert_cols.setObjectName("compact_btn")
        self.btn_invert_cols.clicked.connect(self._invert_columns)
        col_btn_layout.addWidget(self.btn_invert_cols)

        options_layout.addLayout(col_btn_layout)

        # Filtro de búsqueda de columnas
        self.txt_filter_cols = QLineEdit()
        self.txt_filter_cols.setPlaceholderText("Filtrar columnas...")
        self.txt_filter_cols.textChanged.connect(self._filter_column_list)
        options_layout.addWidget(self.txt_filter_cols)

        # Lista interactiva con casillas de verificación
        self.list_columns = QListWidget()
        self.list_columns.setMinimumHeight(140)
        self.list_columns.setMaximumHeight(200)
        self.list_columns.itemChanged.connect(self._on_column_item_changed)
        options_layout.addWidget(self.list_columns)

        # Separador visual
        sep_cols = QFrame()
        sep_cols.setFrameShape(QFrame.Shape.HLine)
        sep_cols.setStyleSheet("background-color: #E4E4E7; margin: 4px 0px;")
        options_layout.addWidget(sep_cols)

        # 4.2. Sección Reglas de Limpieza
        lbl_opts = QLabel("Reglas de Limpieza")
        lbl_opts.setObjectName("section_heading")
        options_layout.addWidget(lbl_opts)

        self.chk_duplicates = QCheckBox("Eliminar filas duplicadas")
        self.chk_duplicates.setChecked(True)
        options_layout.addWidget(self.chk_duplicates)

        self.chk_empty_rows = QCheckBox("Descartar filas vacías")
        self.chk_empty_rows.setChecked(True)
        options_layout.addWidget(self.chk_empty_rows)

        self.chk_empty_cols = QCheckBox("Descartar columnas vacías")
        self.chk_empty_cols.setChecked(True)
        options_layout.addWidget(self.chk_empty_cols)

        self.chk_trim = QCheckBox("Recortar espacios en texto")
        self.chk_trim.setChecked(True)
        options_layout.addWidget(self.chk_trim)

        self.chk_headers = QCheckBox("Normalizar nombres de columna")
        self.chk_headers.setChecked(True)
        self.chk_headers.toggled.connect(self._toggle_header_options)
        options_layout.addWidget(self.chk_headers)

        # Formato de cabeceras
        self.cmb_case = QComboBox()
        self.cmb_case.addItems(["snake_case", "lowercase", "uppercase", "title"])
        options_layout.addWidget(self.cmb_case)

        self.chk_strip_accents = QCheckBox("Eliminar acentos / tildes")
        self.chk_strip_accents.setChecked(True)
        options_layout.addWidget(self.chk_strip_accents)

        # Separador visual
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #E4E4E7; margin: 4px 0px;")
        options_layout.addWidget(sep)

        lbl_missing = QLabel("Tratamiento de Nulos")
        lbl_missing.setStyleSheet("font-weight: 600; font-size: 12px; color: #18181B;")
        options_layout.addWidget(lbl_missing)

        self.cmb_missing = QComboBox()
        self.cmb_missing.addItem("No modificar (conservar nulos)", "none")
        self.cmb_missing.addItem("Eliminar filas con algún nulo", "drop_any")
        self.cmb_missing.addItem("Rellenar con valor fijo", "fill_value")
        self.cmb_missing.addItem("Propagar valor anterior (ffill)", "ffill")
        self.cmb_missing.addItem("Propagar valor siguiente (bfill)", "bfill")
        self.cmb_missing.currentIndexChanged.connect(self._toggle_missing_input)
        options_layout.addWidget(self.cmb_missing)

        self.txt_fill_value = QLineEdit()
        self.txt_fill_value.setPlaceholderText("Valor de reemplazo...")
        self.txt_fill_value.setVisible(False)
        options_layout.addWidget(self.txt_fill_value)

        options_layout.addStretch()

        # Botón principal de procesar
        self.btn_clean = QPushButton("Limpiar Datos")
        self.btn_clean.setObjectName("primary_button")
        self.btn_clean.setEnabled(False)
        self.btn_clean.clicked.connect(self.process_cleaning)
        options_layout.addWidget(self.btn_clean)

        # Envolver en ScrollArea
        scroll_options = QScrollArea()
        scroll_options.setWidgetResizable(True)
        scroll_options.setWidget(options_card)
        scroll_options.setMaximumWidth(330)
        scroll_options.setMinimumWidth(270)

        splitter.addWidget(scroll_options)

        # Panel derecho: 2 Pestañas de previsualización (Originales y Limpios)
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

        splitter.addWidget(self.tabs)
        splitter.setSizes([300, 820])
        main_layout.addWidget(splitter, 1)

        # 5. Barra inferior de acciones (Exportar en Descargas y Reset)
        bottom_layout = QHBoxLayout()
        self.btn_reset = QPushButton("Cargar Nuevo Archivo")
        self.btn_reset.clicked.connect(self.reset_all)
        bottom_layout.addWidget(self.btn_reset)

        bottom_layout.addStretch()

        self.btn_export_excel = QPushButton("Exportar como Excel (.xlsx)")
        self.btn_export_excel.setEnabled(False)
        self.btn_export_excel.clicked.connect(lambda: self.export_data("excel"))
        bottom_layout.addWidget(self.btn_export_excel)

        self.btn_export_csv = QPushButton("Exportar como CSV (.csv)")
        self.btn_export_csv.setObjectName("primary_button")
        self.btn_export_csv.setEnabled(False)
        self.btn_export_csv.clicked.connect(lambda: self.export_data("csv"))
        bottom_layout.addWidget(self.btn_export_csv)

        main_layout.addLayout(bottom_layout)

        # Barra de estado
        self.statusBar().showMessage("Listo. Seleccione o arrastre un archivo para comenzar.")

    def _toggle_header_options(self, checked: bool):
        self.cmb_case.setEnabled(checked)
        self.chk_strip_accents.setEnabled(checked)

    def _toggle_missing_input(self, index: int):
        val = self.cmb_missing.currentData()
        self.txt_fill_value.setVisible(val == "fill_value")

    # --- Métodos de Selección de Columnas ---

    def _populate_columns_list(self, df: pd.DataFrame):
        """Llena la lista de selección con las columnas del DataFrame actual."""
        self.list_columns.blockSignals(True)
        self.list_columns.clear()
        if df is not None and not df.empty:
            for col in df.columns:
                item = QListWidgetItem(str(col))
                item.setData(Qt.ItemDataRole.UserRole, col)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                self.list_columns.addItem(item)
        self.list_columns.blockSignals(False)
        self._update_column_selection_state()

    def _get_selected_columns(self) -> list:
        """Obtiene la lista de columnas que el usuario ha marcado para conservar."""
        selected = []
        for i in range(self.list_columns.count()):
            item = self.list_columns.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                col_obj = item.data(Qt.ItemDataRole.UserRole)
                selected.append(col_obj if col_obj is not None else item.text())
        return selected

    def _select_all_columns(self):
        """Marca todas las columnas visibles."""
        self.list_columns.blockSignals(True)
        for i in range(self.list_columns.count()):
            item = self.list_columns.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.CheckState.Checked)
        self.list_columns.blockSignals(False)
        self._update_column_selection_state()

    def _select_none_columns(self):
        """Desmarca todas las columnas visibles."""
        self.list_columns.blockSignals(True)
        for i in range(self.list_columns.count()):
            item = self.list_columns.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.CheckState.Unchecked)
        self.list_columns.blockSignals(False)
        self._update_column_selection_state()

    def _invert_columns(self):
        """Invierte la selección de las columnas visibles."""
        self.list_columns.blockSignals(True)
        for i in range(self.list_columns.count()):
            item = self.list_columns.item(i)
            if not item.isHidden():
                new_state = Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked
                item.setCheckState(new_state)
        self.list_columns.blockSignals(False)
        self._update_column_selection_state()

    def _filter_column_list(self, text: str):
        """Filtra visualmente la lista de columnas por texto."""
        filter_str = text.strip().lower()
        for i in range(self.list_columns.count()):
            item = self.list_columns.item(i)
            item.setHidden(filter_str not in item.text().lower())

    def _on_column_item_changed(self, item: QListWidgetItem):
        self._update_column_selection_state()

    def _update_column_selection_state(self):
        total = self.list_columns.count()
        selected = len(self._get_selected_columns())
        self.lbl_cols_count.setText(f"{selected} de {total} seleccionadas")
        self.btn_clean.setEnabled(selected > 0 and self.original_df is not None)

    # --- Flujo de Carga y Limpieza ---

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

            # Actualizar cabecera
            name = metadata.get("filename", Path(file_path).name)
            enc = metadata.get("encoding", "")
            sep = metadata.get("delimiter", "")
            info_str = f"Archivo: {name}"
            if enc:
                info_str += f" | {enc.upper()}"
            if sep:
                info_str += f" | Sep: '{sep}'"
            self.lbl_file_info.setText(info_str)

            # Manejar hojas si es Excel
            if "sheets" in metadata and len(metadata["sheets"]) > 1:
                self.cmb_sheet.blockSignals(True)
                self.cmb_sheet.clear()
                self.cmb_sheet.addItems(metadata["sheets"])
                self.cmb_sheet.setCurrentText(metadata["active_sheet"])
                self.cmb_sheet.setVisible(True)
                self.cmb_sheet.blockSignals(False)
            else:
                self.cmb_sheet.setVisible(False)

            # Cargar datos en tabla original y reiniciar tabla limpia
            self.model_original.set_data(self.original_df)
            self.model_cleaned.set_data(pd.DataFrame())

            # Poblar lista de columnas en el panel lateral
            self._populate_columns_list(self.original_df)
            self._update_metrics(self.original_df)

            # Deshabilitar botones de exportación hasta que se limpie
            self.btn_export_csv.setEnabled(False)
            self.btn_export_excel.setEnabled(False)

            self.tabs.setCurrentIndex(0)
            self.statusBar().showMessage(f"Archivo cargado correctamente: {len(df)} filas, {len(df.columns)} columnas.")

        except Exception as e:
            QMessageBox.critical(self, "Error al cargar archivo", f"No se pudo abrir el archivo seleccionado:\n{str(e)}")
            self.statusBar().showMessage("Error al cargar el archivo.")

    def _on_sheet_changed(self, index: int):
        """Maneja el cambio de hoja activa en libros de Excel."""
        if not self.current_filepath or index < 0:
            return
        sheet = self.cmb_sheet.currentText()
        try:
            df, _ = FileHandler.load_excel(self.current_filepath, sheet_name=sheet)
            self.original_df = df
            self.cleaned_df = None
            self.last_report = None
            self.model_original.set_data(self.original_df)
            self.model_cleaned.set_data(pd.DataFrame())
            self._populate_columns_list(self.original_df)
            self._update_metrics(self.original_df)
            self.btn_export_csv.setEnabled(False)
            self.btn_export_excel.setEnabled(False)
            self.statusBar().showMessage(f"Hoja '{sheet}' cargada ({len(df)} filas).")
        except Exception as e:
            QMessageBox.critical(self, "Error al cambiar de hoja", str(e))

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
        """Ejecuta las operaciones de limpieza configuradas."""
        if self.original_df is None:
            return

        selected_cols = self._get_selected_columns()
        if not selected_cols:
            QMessageBox.warning(self, "Aviso", "Debe seleccionar al menos una columna para conservar.")
            return

        options = CleaningOptions(
            selected_columns=selected_cols,
            remove_duplicates=self.chk_duplicates.isChecked(),
            drop_empty_rows=self.chk_empty_rows.isChecked(),
            drop_empty_cols=self.chk_empty_cols.isChecked(),
            trim_whitespace=self.chk_trim.isChecked(),
            clean_headers=self.chk_headers.isChecked(),
            header_case=self.cmb_case.currentText(),
            handle_missing=self.cmb_missing.currentData(),
            missing_fill_value=self.txt_fill_value.text().strip(),
            strip_accents=self.chk_strip_accents.isChecked()
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
        Exporta el archivo limpio (CSV o Excel) y automáticamente genera
        el archivo .txt con el registro de cambios en la carpeta de Descargas (o ruta elegida).
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

        self.list_columns.clear()
        self.lbl_cols_count.setText("0 seleccionadas")
        self.lbl_file_info.setText("Ningún archivo cargado")
        self.cmb_sheet.setVisible(False)

        self._update_metrics(None)
        self.btn_clean.setEnabled(False)
        self.btn_export_csv.setEnabled(False)
        self.btn_export_excel.setEnabled(False)

        self.tabs.setCurrentIndex(0)
        self.statusBar().showMessage("Listo para cargar un nuevo archivo.")
