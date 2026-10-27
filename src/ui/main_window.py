"""
Ventana principal de CSVCleaner construida con PySide6.
Proporciona carga por arrastrar y soltar, previsualización en tiempo real,
configuración de transformaciones de datos y exportación a múltiples formatos.
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
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent

import pandas as pd

from ..core.cleaner import DataCleaner, CleaningOptions, CleaningReport
from ..core.file_handler import FileHandler
from ..core.voice_listener import VoiceListenerWorker
from ..core.voice_commands import VoiceCommandParser
from ..core.analytics import DataAnalytics
from .table_model import PandasTableModel
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


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
    """Área interactiva para arrastrar y soltar archivos o abrir explorador."""

    def __init__(self, on_file_selected):
        super().__init__()
        self.on_file_selected = on_file_selected
        self.setObjectName("drop_zone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(6)

        self.lbl_main = QLabel("Arrastra y suelta tu archivo CSV o Excel aquí")
        self.lbl_main.setStyleSheet("font-weight: 600; font-size: 14px; color: #18181B;")
        self.lbl_main.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_sub = QLabel("O haz clic para buscar en tu equipo (.csv, .xlsx, .xls)")
        self.lbl_sub.setObjectName("subtitle")
        self.lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.lbl_main)
        layout.addWidget(self.lbl_sub)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar archivo CSV o Excel",
                "",
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
        self.resize(1180, 780)
        self.setMinimumSize(900, 600)

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

        # Módulo de escucha de voz offline
        self.voice_worker = VoiceListenerWorker(self)
        self.voice_worker.command_detected.connect(self._on_voice_command)
        self.voice_worker.partial_detected.connect(self._on_voice_partial)
        self.voice_worker.listening_state_changed.connect(self._on_voice_state_changed)
        self.voice_worker.status_message.connect(self._on_voice_status)

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

        # 1.1. Barra de Control por Voz (Reconocimiento Offline)
        voice_card = QFrame()
        voice_card.setObjectName("card")
        voice_card_layout = QHBoxLayout(voice_card)
        voice_card_layout.setContentsMargins(12, 8, 12, 8)
        voice_card_layout.setSpacing(12)

        self.btn_voice_toggle = QPushButton("🎙️ Activar Escucha Continua")
        self.btn_voice_toggle.setObjectName("primary_button")
        self.btn_voice_toggle.setToolTip("Activar o pausar el reconocimiento de comandos de voz offline")
        self.btn_voice_toggle.clicked.connect(self._toggle_voice_listening)
        voice_card_layout.addWidget(self.btn_voice_toggle)

        self.lbl_voice_status = QLabel("⚪ Escucha por voz inactiva")
        self.lbl_voice_status.setStyleSheet("color: #71717A; font-weight: 500; font-size: 12px;")
        voice_card_layout.addWidget(self.lbl_voice_status, 1)

        self.lbl_voice_hints = QLabel("💡 Dicta: 'eliminar duplicados', 'quitar columna edad', 'limpiar datos'")
        self.lbl_voice_hints.setStyleSheet("color: #A1A1AA; font-size: 11px; font-style: italic;")
        voice_card_layout.addWidget(self.lbl_voice_hints)

        main_layout.addWidget(voice_card)

        # 2. Zona de carga (Drag and Drop)
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

        # 1. Sección Selección de Columnas
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
        self.list_columns.setMinimumHeight(130)
        self.list_columns.setMaximumHeight(190)
        self.list_columns.itemChanged.connect(self._on_column_item_changed)
        options_layout.addWidget(self.list_columns)

        # Separador visual
        sep_cols = QFrame()
        sep_cols.setFrameShape(QFrame.Shape.HLine)
        sep_cols.setStyleSheet("background-color: #E4E4E7; margin: 4px 0px;")
        options_layout.addWidget(sep_cols)

        # 2. Sección Reglas de Limpieza
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

        # Envolver en ScrollArea para garantizar accesibilidad en cualquier resolución
        scroll_options = QScrollArea()
        scroll_options.setWidgetResizable(True)
        scroll_options.setWidget(options_card)
        scroll_options.setMaximumWidth(330)
        scroll_options.setMinimumWidth(270)

        splitter.addWidget(scroll_options)

        # Panel derecho: Pestañas de previsualización
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

        # Tab 3: Calidad de Columnas
        self.table_stats = QTableView()
        self.table_stats.horizontalHeader().setStretchLastSection(True)
        self.model_stats = PandasTableModel()
        self.table_stats.setModel(self.model_stats)
        self.tabs.addTab(self.table_stats, "Diagnóstico de Columnas")

        # Tab 4: Bitácora de Transformación
        self.list_log = QListWidget()
        self.list_log.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E4E7; border-radius: 6px; padding: 8px;")
        self.tabs.addTab(self.list_log, "Bitácora de Acciones")

        # Tab 5: Gráficos y Visualización Profesional
        tab_analytics = QWidget()
        analytics_layout = QVBoxLayout(tab_analytics)
        analytics_layout.setContentsMargins(10, 10, 10, 10)
        analytics_layout.setSpacing(10)

        # Barra de controles de gráficos
        plot_toolbar_layout = QHBoxLayout()
        plot_toolbar_layout.setSpacing(8)

        lbl_tipo = QLabel("Tipo:")
        lbl_tipo.setStyleSheet("font-weight: 600; font-size: 12px; color: #18181B;")
        plot_toolbar_layout.addWidget(lbl_tipo)

        self.cmb_plot_type = QComboBox()
        self.cmb_plot_type.addItem("Distribución / Histograma", "distribution")
        self.cmb_plot_type.addItem("Barras Categóricas (Top N)", "bar")
        self.cmb_plot_type.addItem("Dispersión (Scatter X vs Y)", "scatter")
        self.cmb_plot_type.addItem("Diagrama de Caja (Boxplot)", "box")
        self.cmb_plot_type.addItem("Matriz de Correlación (Heatmap)", "correlation")
        self.cmb_plot_type.currentIndexChanged.connect(self._on_plot_type_changed)
        plot_toolbar_layout.addWidget(self.cmb_plot_type)

        self.lbl_col_x = QLabel("Columna X:")
        self.lbl_col_x.setStyleSheet("font-weight: 500; font-size: 12px; color: #52525B;")
        plot_toolbar_layout.addWidget(self.lbl_col_x)

        self.cmb_plot_x = QComboBox()
        plot_toolbar_layout.addWidget(self.cmb_plot_x)

        self.lbl_col_y = QLabel("Columna Y:")
        self.lbl_col_y.setStyleSheet("font-weight: 500; font-size: 12px; color: #52525B;")
        self.lbl_col_y.setVisible(False)
        plot_toolbar_layout.addWidget(self.lbl_col_y)

        self.cmb_plot_y = QComboBox()
        self.cmb_plot_y.setVisible(False)
        plot_toolbar_layout.addWidget(self.cmb_plot_y)

        self.btn_generate_plot = QPushButton("Generar Gráfico")
        self.btn_generate_plot.setObjectName("primary_button")
        self.btn_generate_plot.clicked.connect(self.render_selected_plot)
        plot_toolbar_layout.addWidget(self.btn_generate_plot)

        self.btn_save_plot = QPushButton("Exportar PNG")
        self.btn_save_plot.clicked.connect(self.save_current_plot)
        plot_toolbar_layout.addWidget(self.btn_save_plot)

        plot_toolbar_layout.addStretch()

        self.btn_full_report_pdf = QPushButton("📊 Reporte con Gráficos (PDF)")
        self.btn_full_report_pdf.setObjectName("primary_button")
        self.btn_full_report_pdf.clicked.connect(self.export_full_analytical_pdf)
        plot_toolbar_layout.addWidget(self.btn_full_report_pdf)

        analytics_layout.addLayout(plot_toolbar_layout)

        # Canvas interactivo embebido
        self.plot_figure = Figure(figsize=(8, 4.5), dpi=100)
        self.plot_canvas = FigureCanvas(self.plot_figure)
        self.plot_canvas.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E4E7; border-radius: 6px;")

        self.plot_nav_toolbar = NavigationToolbar(self.plot_canvas, tab_analytics)
        self.plot_nav_toolbar.setStyleSheet("background-color: #FAFAFA; border: none; padding: 2px;")
        analytics_layout.addWidget(self.plot_nav_toolbar)
        analytics_layout.addWidget(self.plot_canvas, 1)

        self.tabs.addTab(tab_analytics, "Gráficos y Visualización")

        splitter.addWidget(self.tabs)
        splitter.setSizes([280, 860])
        main_layout.addWidget(splitter, 1)

        # 5. Barra inferior de acciones (Exportar y Reset)
        bottom_layout = QHBoxLayout()
        self.btn_reset = QPushButton("Cargar Nuevo Archivo")
        self.btn_reset.clicked.connect(self.reset_all)
        bottom_layout.addWidget(self.btn_reset)

        bottom_layout.addStretch()

        self.btn_export_pdf = QPushButton("Generar Reporte PDF")
        self.btn_export_pdf.setEnabled(False)
        self.btn_export_pdf.clicked.connect(self.export_pdf_report)
        bottom_layout.addWidget(self.btn_export_pdf)

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
                new_state = (
                    Qt.CheckState.Unchecked
                    if item.checkState() == Qt.CheckState.Checked
                    else Qt.CheckState.Checked
                )
                item.setCheckState(new_state)
        self.list_columns.blockSignals(False)
        self._update_column_selection_state()

    def _filter_column_list(self, query: str):
        """Filtra los elementos de la lista de columnas en tiempo real según la búsqueda."""
        clean_q = query.strip().lower()
        for i in range(self.list_columns.count()):
            item = self.list_columns.item(i)
            item.setHidden(clean_q not in item.text().lower())

    def _on_column_item_changed(self, item: QListWidgetItem):
        """Disparado cuando el usuario marca o desmarca una columna individual."""
        self._update_column_selection_state()

    def _update_column_selection_state(self):
        """Actualiza el contador, la tabla de diagnóstico y la validez del botón de limpieza."""
        selected = self._get_selected_columns()
        total = self.list_columns.count()
        self.lbl_cols_count.setText(f"{len(selected)} de {total} seleccionadas")

        if self.original_df is not None:
            self.btn_clean.setEnabled(len(selected) > 0)
            stats = DataCleaner.get_column_stats(self.original_df, selected)
            self.model_stats.set_data(pd.DataFrame(stats))

    def load_file(self, file_path: str):
        """Carga el archivo seleccionado y actualiza la vista."""
        try:
            self.statusBar().showMessage(f"Cargando {Path(file_path).name}...")
            df, metadata = FileHandler.load_file(file_path)
            self.current_filepath = file_path
            self.file_metadata = metadata
            self.original_df = df
            self.cleaned_df = None
            self.last_report = None

            # Actualizar selector de hojas para Excel
            if "sheets" in metadata and len(metadata["sheets"]) > 1:
                self.cmb_sheet.blockSignals(True)
                self.cmb_sheet.clear()
                self.cmb_sheet.addItems(metadata["sheets"])
                self.cmb_sheet.setCurrentText(metadata.get("active_sheet", metadata["sheets"][0]))
                self.cmb_sheet.blockSignals(False)
                self.cmb_sheet.setVisible(True)
            else:
                self.cmb_sheet.setVisible(False)

            # Actualizar tablas y modelos
            self.model_original.set_data(self.original_df)
            self.model_cleaned.set_data(pd.DataFrame())

            # Cargar y sincronizar selector de columnas
            self._populate_columns_list(self.original_df)
            self._populate_plot_column_selectors(self.original_df)

            # Actualizar métricas iniciales
            self._update_metrics(self.original_df)

            # Información del archivo en la cabecera
            name = Path(file_path).name
            size_kb = os.path.getsize(file_path) / 1024
            enc = metadata.get("encoding", "")
            sep = metadata.get("delimiter", "")
            extra_info = f" ({enc}, sep='{sep}')" if enc else ""
            self.lbl_file_info.setText(f"{name} [{size_kb:.1f} KB]{extra_info}")

            # Activar botones
            self.btn_clean.setEnabled(True)
            self.btn_export_csv.setEnabled(False)
            self.btn_export_excel.setEnabled(False)
            self.btn_export_pdf.setEnabled(False)
            self.list_log.clear()

            self.tabs.setCurrentIndex(0)
            self.statusBar().showMessage(f"Archivo cargado: {len(self.original_df)} filas y {len(self.original_df.columns)} columnas.")

        except Exception as e:
            QMessageBox.critical(self, "Error al cargar archivo", f"No fue posible abrir el archivo:\n{str(e)}")
            self.statusBar().showMessage("Error al cargar archivo.")

    def _on_sheet_changed(self):
        """Maneja el cambio de hoja en archivos Excel multipágina."""
        if not self.current_filepath:
            return
        sheet = self.cmb_sheet.currentText()
        if not sheet:
            return
        try:
            df, _ = FileHandler.load_excel(self.current_filepath, sheet_name=sheet)
            self.original_df = df
            self.cleaned_df = None
            self.model_original.set_data(self.original_df)
            self.model_cleaned.set_data(pd.DataFrame())
            self._populate_columns_list(self.original_df)
            self._populate_plot_column_selectors(self.original_df)
            self._update_metrics(self.original_df)
            self.btn_export_csv.setEnabled(False)
            self.btn_export_excel.setEnabled(False)
            self.btn_export_pdf.setEnabled(False)
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

            # Refrescar bitácora
            self.list_log.clear()
            for item in report.operations_log:
                self.list_log.addItem(f"✓ {item}")

            # Refrescar métricas con el dataset limpio
            self._update_metrics(self.cleaned_df)
            self._populate_plot_column_selectors(self.cleaned_df)

            # Habilitar exportaciones
            self.btn_export_csv.setEnabled(True)
            self.btn_export_excel.setEnabled(True)
            self.btn_export_pdf.setEnabled(True)

            # Cambiar a la pestaña de datos limpios
            self.tabs.setCurrentIndex(1)

            diff_rows = report.rows_before - report.rows_after
            self.statusBar().showMessage(
                f"Limpieza completada: {report.rows_after} filas y {len(cleaned_df.columns)} columnas conservadas."
            )

        except Exception as e:
            QMessageBox.critical(self, "Error durante la limpieza", f"Ocurrió un error inesperado:\n{str(e)}")

    def export_data(self, file_format: str):
        """Permite guardar los datos limpios en CSV o Excel."""
        if self.cleaned_df is None:
            QMessageBox.warning(self, "Aviso", "Primero debe ejecutar la limpieza de datos.")
            return

        stem = Path(self.current_filepath).stem if self.current_filepath else "data"
        default_name = f"{stem}_cleaned"

        if file_format == "csv":
            path, _ = QFileDialog.getSaveFileName(
                self, "Exportar CSV Limpio", f"{default_name}.csv", "Archivo CSV (*.csv)"
            )
            if path:
                FileHandler.export_csv(self.cleaned_df, path)
                QMessageBox.information(self, "Exportación Exitosa", f"Archivo guardado en:\n{path}")
                self.statusBar().showMessage(f"CSV exportado exitosamente a {Path(path).name}")

        elif file_format == "excel":
            path, _ = QFileDialog.getSaveFileName(
                self, "Exportar Excel Limpio", f"{default_name}.xlsx", "Libro de Excel (*.xlsx)"
            )
            if path:
                FileHandler.export_excel(self.cleaned_df, path)
                QMessageBox.information(self, "Exportación Exitosa", f"Archivo guardado en:\n{path}")
                self.statusBar().showMessage(f"Excel exportado exitosamente a {Path(path).name}")

    def export_pdf_report(self):
        """Genera el reporte ejecutivo en PDF y lo almacena en outputs/."""
        if not self.last_report:
            QMessageBox.warning(self, "Aviso", "Primero debe ejecutar la limpieza de datos para generar el reporte.")
            return

        stem = Path(self.current_filepath).stem if self.current_filepath else "data"
        default_dir = Path(__file__).resolve().parent.parent.parent / "outputs"
        default_pdf = default_dir / f"{stem}_reporte_limpieza.pdf"

        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Reporte de Limpieza (PDF)", str(default_pdf), "Documentos PDF (*.pdf)"
        )
        if path:
            try:
                FileHandler.generate_pdf_report(
                    self.last_report,
                    source_name=Path(self.current_filepath).name if self.current_filepath else "archivo_desconocido",
                    output_pdf_path=path
                )
                QMessageBox.information(self, "Reporte Generado", f"El reporte de auditoría ha sido guardado en:\n{path}")
                self.statusBar().showMessage(f"Reporte PDF creado en {Path(path).name}")
            except Exception as e:
                QMessageBox.critical(self, "Error al generar PDF", f"No se pudo crear el PDF:\n{str(e)}")

    def reset_all(self):
        """Restablece la interfaz a su estado inicial."""
        self.current_filepath = None
        self.original_df = None
        self.cleaned_df = None
        self.last_report = None
        self.model_original.set_data(pd.DataFrame())
        self.model_cleaned.set_data(pd.DataFrame())
        self.model_stats.set_data(pd.DataFrame())
        self.list_log.clear()
        self.list_columns.blockSignals(True)
        self.list_columns.clear()
        self.list_columns.blockSignals(False)
        self.lbl_cols_count.setText("0 seleccionadas")
        self.txt_filter_cols.clear()
        self.lbl_file_info.setText("Ningún archivo cargado")
        self.cmb_sheet.setVisible(False)
        self.btn_clean.setEnabled(False)
        self.btn_export_csv.setEnabled(False)
        self.btn_export_excel.setEnabled(False)
        self.btn_export_pdf.setEnabled(False)
        self._update_metrics(None)
        self.plot_figure.clf()
        self.plot_canvas.draw()
        self.cmb_plot_x.clear()
        self.cmb_plot_y.clear()
        self.tabs.setCurrentIndex(0)
        self.statusBar().showMessage("Listo para cargar un nuevo archivo.")

    # --- Módulo de Gráficos y Visualización Profesional ---

    def _on_plot_type_changed(self):
        """Ajusta los controles de selección según el tipo de gráfico."""
        plot_type = self.cmb_plot_type.currentData()
        if plot_type == "scatter":
            self.lbl_col_x.setText("Columna X:")
            self.lbl_col_x.setVisible(True)
            self.cmb_plot_x.setVisible(True)
            self.lbl_col_y.setVisible(True)
            self.cmb_plot_y.setVisible(True)
        elif plot_type == "correlation":
            self.lbl_col_x.setVisible(False)
            self.cmb_plot_x.setVisible(False)
            self.lbl_col_y.setVisible(False)
            self.cmb_plot_y.setVisible(False)
        else:
            self.lbl_col_x.setText("Columna:")
            self.lbl_col_x.setVisible(True)
            self.cmb_plot_x.setVisible(True)
            self.lbl_col_y.setVisible(False)
            self.cmb_plot_y.setVisible(False)

    def _populate_plot_column_selectors(self, df: pd.DataFrame):
        """Actualiza los selectores de columnas para el módulo de gráficos."""
        if df is None or df.empty:
            return
        current_x = self.cmb_plot_x.currentText()
        current_y = self.cmb_plot_y.currentText()

        self.cmb_plot_x.blockSignals(True)
        self.cmb_plot_y.blockSignals(True)
        self.cmb_plot_x.clear()
        self.cmb_plot_y.clear()

        cols = [str(c) for c in df.columns]
        self.cmb_plot_x.addItems(cols)
        self.cmb_plot_y.addItems(cols)

        if current_x in cols:
            self.cmb_plot_x.setCurrentText(current_x)
        if current_y in cols and len(cols) > 1:
            self.cmb_plot_y.setCurrentText(current_y)
        elif len(cols) > 1:
            self.cmb_plot_y.setCurrentIndex(1)

        self.cmb_plot_x.blockSignals(False)
        self.cmb_plot_y.blockSignals(False)

    def _get_active_dataset(self) -> Optional[pd.DataFrame]:
        """Retorna el DataFrame limpio si existe, o el original si aún no se limpió."""
        if self.cleaned_df is not None and not self.cleaned_df.empty:
            return self.cleaned_df
        return self.original_df

    def render_selected_plot(self):
        """Genera y renderiza el gráfico seleccionado en el lienzo interactivo."""
        df = self._get_active_dataset()
        if df is None or df.empty:
            QMessageBox.warning(self, "Aviso", "Primero debe cargar un archivo con datos.")
            return

        plot_type = self.cmb_plot_type.currentData()
        col_x = self.cmb_plot_x.currentText()
        col_y = self.cmb_plot_y.currentText()

        try:
            self.plot_figure.clf()

            if plot_type == "distribution":
                if not col_x:
                    QMessageBox.warning(self, "Aviso", "Seleccione una columna para graficar.")
                    return
                fig = DataAnalytics.plot_distribution(df, col_x)
            elif plot_type == "bar":
                if not col_x:
                    QMessageBox.warning(self, "Aviso", "Seleccione una columna para graficar.")
                    return
                fig = DataAnalytics.plot_categorical_bars(df, col_x)
            elif plot_type == "scatter":
                if not col_x or not col_y:
                    QMessageBox.warning(self, "Aviso", "Seleccione las columnas X e Y.")
                    return
                fig = DataAnalytics.plot_scatter(df, col_x, col_y)
            elif plot_type == "box":
                if not col_x:
                    QMessageBox.warning(self, "Aviso", "Seleccione una columna para graficar.")
                    return
                fig = DataAnalytics.plot_box(df, col_x)
            elif plot_type == "correlation":
                fig = DataAnalytics.plot_correlation_matrix(df)
            else:
                return

            # Reasignar ejes a la figura del canvas interactivo
            for ax in fig.axes:
                ax.remove()
                self.plot_figure.add_axes(ax)

            self.plot_figure.tight_layout()
            self.plot_canvas.draw()
            self.statusBar().showMessage(f"Gráfico '{self.cmb_plot_type.currentText()}' renderizado.")

        except Exception as e:
            QMessageBox.critical(self, "Error al graficar", f"No se pudo generar el gráfico:\n{str(e)}")

    def save_current_plot(self):
        """Permite guardar el gráfico actual en alta resolución."""
        if not self.plot_figure.axes:
            QMessageBox.warning(self, "Aviso", "Aún no se ha generado ningún gráfico.")
            return

        stem = Path(self.current_filepath).stem if self.current_filepath else "grafico"
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Gráfico", f"{stem}_grafico.png", "Imágenes PNG (*.png);;Vectores SVG (*.svg)"
        )
        if path:
            try:
                self.plot_figure.savefig(path, dpi=300, bbox_inches="tight")
                QMessageBox.information(self, "Gráfico Guardado", f"Archivo guardado exitosamente en:\n{path}")
                self.statusBar().showMessage(f"Gráfico exportado a {Path(path).name}")
            except Exception as e:
                QMessageBox.critical(self, "Error al exportar gráfico", str(e))

    def export_full_analytical_pdf(self):
        """Genera el reporte ejecutivo completo con tablas y gráficos profesionales embebidos."""
        df = self._get_active_dataset()
        if df is None or df.empty:
            QMessageBox.warning(self, "Aviso", "Primero debe cargar un archivo con datos.")
            return

        stem = Path(self.current_filepath).stem if self.current_filepath else "data"
        default_dir = Path(__file__).resolve().parent.parent.parent / "outputs"
        default_pdf = default_dir / f"{stem}_reporte_analitico_profesional.pdf"

        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Reporte Analítico con Gráficos (PDF)", str(default_pdf), "Documentos PDF (*.pdf)"
        )
        if path:
            try:
                self.statusBar().showMessage("Generando reporte analítico con gráficos...")
                DataAnalytics.generate_full_analytical_pdf(
                    df=df,
                    dataset_name=Path(self.current_filepath).name if self.current_filepath else "dataset",
                    output_pdf_path=path
                )
                QMessageBox.information(
                    self, "Reporte Generado",
                    f"El reporte analítico formal con gráficos se ha guardado en:\n{path}"
                )
                self.statusBar().showMessage(f"Reporte con gráficos generado en {Path(path).name}")
            except Exception as e:
                QMessageBox.critical(self, "Error al generar reporte", f"Ocurrió un error:\n{str(e)}")

    # --- Control por Voz (Reconocimiento Continuo Offline) ---

    def _toggle_voice_listening(self):
        """Alterna el estado de escucha continua del micrófono."""
        if self.voice_worker.is_listening():
            self.voice_worker.stop_listening()
        else:
            self.voice_worker.start_listening()

    def _on_voice_state_changed(self, is_listening: bool):
        """Actualiza el botón y la etiqueta visual de estado del micrófono."""
        if is_listening:
            self.btn_voice_toggle.setText("⏹️ Detener Escucha")
            self.btn_voice_toggle.setStyleSheet("background-color: #18181B; color: #FFFFFF;")
            self.lbl_voice_status.setText("🟢 Escuchando... (hable libremente)")
            self.lbl_voice_status.setStyleSheet("color: #09090B; font-weight: 600; font-size: 12px;")
        else:
            self.btn_voice_toggle.setText("🎙️ Activar Escucha Continua")
            self.btn_voice_toggle.setStyleSheet("")
            self.lbl_voice_status.setText("⚪ Escucha por voz inactiva")
            self.lbl_voice_status.setStyleSheet("color: #71717A; font-weight: 500; font-size: 12px;")

    def _on_voice_partial(self, partial_text: str):
        """Muestra la transcripción parcial en tiempo real."""
        if partial_text:
            self.lbl_voice_status.setText(f"🟢 Escuchando: \"{partial_text}...\"")

    def _on_voice_status(self, msg: str):
        """Muestra mensajes informativos o de inicialización del modelo."""
        self.statusBar().showMessage(msg, 4000)

    def _on_voice_command(self, full_text: str):
        """Procesa una frase reconocida y ejecuta las acciones correspondientes."""
        self.lbl_voice_status.setText(f"🗣️ Reconocido: \"{full_text}\"")
        self.statusBar().showMessage(f"Comando de voz recibido: \"{full_text}\"", 5000)

        # Obtener columnas disponibles si hay un dataset cargado
        avail_cols = list(self.original_df.columns) if self.original_df is not None else []
        actions = VoiceCommandParser.parse(full_text, available_columns=avail_cols)

        if not actions:
            self.lbl_voice_status.setText(f"❓ No se identificó acción en: \"{full_text}\"")
            return

        applied_descs = []
        for action, param in actions:
            desc = self._apply_voice_action(action, param)
            if desc:
                applied_descs.append(desc)

        if applied_descs:
            summary = ", ".join(applied_descs)
            self.lbl_voice_status.setText(f"✓ Ejecutado: {summary}")
            self.statusBar().showMessage(f"Voz aplicada: {summary}", 5000)

    def _apply_voice_action(self, action: str, param: Any) -> Optional[str]:
        """Aplica una acción individual proveniente de la voz sobre la interfaz."""
        if action == "set_duplicates":
            self.chk_duplicates.setChecked(param)
            return "Eliminar duplicados" if param else "Conservar duplicados"

        elif action == "set_empty_rows":
            self.chk_empty_rows.setChecked(param)
            return "Descartar filas vacías" if param else "Conservar filas vacías"

        elif action == "set_empty_cols":
            self.chk_empty_cols.setChecked(param)
            return "Descartar columnas vacías" if param else "Conservar columnas vacías"

        elif action == "set_trim":
            self.chk_trim.setChecked(param)
            return "Recortar espacios" if param else "No recortar espacios"

        elif action == "set_clean_headers":
            self.chk_headers.setChecked(param)
            return "Normalizar cabeceras" if param else "No normalizar cabeceras"

        elif action == "set_header_case":
            self.cmb_case.setCurrentText(param)
            return f"Cabeceras a {param}"

        elif action == "set_strip_accents":
            self.chk_strip_accents.setChecked(param)
            return "Quitar acentos" if param else "Conservar acentos"

        elif action == "set_missing_strategy":
            idx = self.cmb_missing.findData(param)
            if idx >= 0:
                self.cmb_missing.setCurrentIndex(idx)
                return f"Nulos: {self.cmb_missing.currentText()}"

        elif action == "set_missing_fill":
            idx = self.cmb_missing.findData("fill_value")
            if idx >= 0:
                self.cmb_missing.setCurrentIndex(idx)
            self.txt_fill_value.setText(str(param))
            return f"Rellenar nulos con '{param}'"

        elif action == "select_all_columns":
            self._select_all_columns()
            return "Todas las columnas seleccionadas"

        elif action == "select_none_columns":
            self._select_none_columns()
            return "Todas las columnas desmarcadas"

        elif action == "invert_columns":
            self._invert_columns()
            return "Selección invertida"

        elif action == "select_column":
            for i in range(self.list_columns.count()):
                item = self.list_columns.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == param or item.text() == str(param):
                    item.setCheckState(Qt.CheckState.Checked)
                    return f"Conservar columna '{param}'"

        elif action == "deselect_column":
            for i in range(self.list_columns.count()):
                item = self.list_columns.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == param or item.text() == str(param):
                    item.setCheckState(Qt.CheckState.Unchecked)
                    return f"Descartar columna '{param}'"

        elif action == "action_clean":
            if self.btn_clean.isEnabled():
                self.process_cleaning()
                return "Limpieza ejecutada"
            return "Limpieza no disponible (cargue un archivo primero)"

        elif action == "action_export_csv":
            if self.btn_export_csv.isEnabled():
                self.export_data("csv")
                return "Exportar CSV"

        elif action == "action_export_excel":
            if self.btn_export_excel.isEnabled():
                self.export_data("excel")
                return "Exportar Excel"

        elif action == "action_export_pdf":
            if self.btn_export_pdf.isEnabled():
                self.export_pdf_report()
                return "Generar PDF"

        elif action == "action_plot":
            plot_spec = param if isinstance(param, dict) else {}
            plot_type = plot_spec.get("type", "distribution")
            col = plot_spec.get("col")
            idx = self.cmb_plot_type.findData(plot_type)
            if idx >= 0:
                self.cmb_plot_type.setCurrentIndex(idx)
            if col:
                col_idx = self.cmb_plot_x.findText(col)
                if col_idx >= 0:
                    self.cmb_plot_x.setCurrentIndex(col_idx)
            self.tabs.setCurrentIndex(4)  # Cambiar a pestaña de gráficos
            self.render_selected_plot()
            return f"Gráfico {plot_type} generado"

        elif action == "action_advanced_report":
            self.export_full_analytical_pdf()
            return "Reporte analítico completo generado"

        elif action == "action_reset":
            self.reset_all()
            return "Aplicación reiniciada"

        return None

    def closeEvent(self, event):
        """Asegura el apagado correcto del hilo de escucha al cerrar la ventana."""
        if hasattr(self, 'voice_worker') and self.voice_worker.is_listening():
            self.voice_worker.stop_listening()
        event.accept()
