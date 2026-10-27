"""
Hoja de estilos QSS monocromática y minimalista (blanco, negro y grises neutros).
Diseño sobrio, contemporáneo y de alto contraste.
"""

MONOCHROME_STYLE = """
/* Ventana principal y contenedores base */
QMainWindow, QWidget {
    background-color: #FAFAFA;
    color: #09090B;
    font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt;
}

/* Paneles y tarjetas */
QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #E4E4E7;
    border-radius: 8px;
    padding: 12px;
}

QFrame#drop_zone {
    background-color: #FFFFFF;
    border: 2px dashed #A1A1AA;
    border-radius: 10px;
    padding: 20px;
}

QFrame#drop_zone:hover {
    border-color: #09090B;
    background-color: #F4F4F5;
}

/* Títulos y etiquetas */
QLabel#title {
    font-size: 18px;
    font-weight: 700;
    color: #09090B;
    letter-spacing: -0.5px;
}

QLabel#subtitle {
    font-size: 12px;
    color: #71717A;
}

QLabel#section_heading {
    font-size: 13px;
    font-weight: 600;
    color: #18181B;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel#metric_value {
    font-size: 20px;
    font-weight: 700;
    color: #09090B;
}

QLabel#metric_label {
    font-size: 11px;
    color: #71717A;
    text-transform: uppercase;
}

/* Botones principales y secundarios */
QPushButton {
    background-color: #FFFFFF;
    color: #09090B;
    border: 1px solid #E4E4E7;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #F4F4F5;
    border-color: #D4D4D8;
}

QPushButton:pressed {
    background-color: #E4E4E7;
}

QPushButton:disabled {
    background-color: #F4F4F5;
    color: #A1A1AA;
    border-color: #E4E4E7;
}

/* Botón de acción primordial (Negro absoluto) */
QPushButton#primary_button {
    background-color: #09090B;
    color: #FFFFFF;
    border: 1px solid #09090B;
    font-weight: 600;
}

QPushButton#primary_button:hover {
    background-color: #27272A;
    border-color: #27272A;
}

QPushButton#primary_button:pressed {
    background-color: #000000;
}

QPushButton#primary_button:disabled {
    background-color: #71717A;
    border-color: #71717A;
    color: #E4E4E7;
}

/* Tablas de visualización */
QTableView {
    background-color: #FFFFFF;
    border: 1px solid #E4E4E7;
    border-radius: 6px;
    gridline-color: #F4F4F5;
    selection-background-color: #18181B;
    selection-color: #FFFFFF;
    outline: none;
    font-size: 12px;
}

QTableView::item {
    padding: 6px 10px;
    border-bottom: 1px solid #F4F4F5;
}

QTableView::item:selected {
    background-color: #18181B;
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #F4F4F5;
    color: #09090B;
    font-weight: 600;
    font-size: 11px;
    padding: 8px 10px;
    border: none;
    border-right: 1px solid #E4E4E7;
    border-bottom: 1px solid #E4E4E7;
}

/* Pestañas (Tabs) */
QTabWidget::pane {
    border: 1px solid #E4E4E7;
    border-radius: 6px;
    background-color: #FFFFFF;
    top: -1px;
}

QTabBar::tab {
    background-color: #FAFAFA;
    color: #71717A;
    padding: 8px 16px;
    border: 1px solid #E4E4E7;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #09090B;
    border-bottom: 1px solid #FFFFFF;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background-color: #F4F4F5;
    color: #09090B;
}

/* Casillas de verificación (CheckBoxes) */
QCheckBox {
    spacing: 8px;
    color: #18181B;
    font-size: 13px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #D4D4D8;
    background-color: #FFFFFF;
}

QCheckBox::indicator:hover {
    border-color: #09090B;
}

QCheckBox::indicator:checked {
    background-color: #09090B;
    border-color: #09090B;
    image: none;
}

/* Desplegables (ComboBoxes) y entradas de texto */
QComboBox, QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #E4E4E7;
    border-radius: 6px;
    padding: 6px 12px;
    color: #09090B;
    min-height: 20px;
}

QComboBox:focus, QLineEdit:focus {
    border-color: #09090B;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #E4E4E7;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E4E4E7;
    selection-background-color: #18181B;
    selection-color: #FFFFFF;
    outline: none;
    padding: 4px;
}

/* Lista de columnas y áreas de scroll */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #E4E4E7;
    border-radius: 6px;
    padding: 4px;
    outline: none;
    font-size: 12px;
}

QListWidget::item {
    padding: 5px 8px;
    border-radius: 4px;
    color: #18181B;
}

QListWidget::item:hover {
    background-color: #F4F4F5;
}

QListWidget::item:selected {
    background-color: #E4E4E7;
    color: #09090B;
}

QPushButton#compact_btn {
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 500;
}

/* Barras de desplazamiento (Scrollbars) */
QScrollBar:vertical {
    border: none;
    background-color: #FAFAFA;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #D4D4D8;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #A1A1AA;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background-color: #FAFAFA;
    height: 8px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #D4D4D8;
    min-width: 20px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #A1A1AA;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Barra de estado */
QStatusBar {
    background-color: #FFFFFF;
    border-top: 1px solid #E4E4E7;
    color: #71717A;
    font-size: 12px;
    padding: 4px 12px;
}
"""
