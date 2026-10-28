"""
Hoja de estilos QSS en Modo Claro de Bajo Contraste.
Filosofía MVP: Descansado a la vista, minimalista y profesional.
Colores base: Fondos en #F4F4F5, contenedores en #FFFFFF, textos en #3F3F46/#52525B
y acento suave en verde salvia/menta desaturado (#4CA154).
"""

MONOCHROME_STYLE = """
/* Ventana principal y contenedores base */
QMainWindow, QWidget {
    background-color: #F4F4F5;
    color: #3F3F46;
    font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt;
}

/* Tarjetas métricas y paneles */
QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #E4E4E7;
    border-radius: 8px;
    padding: 10px 14px;
}

/* Zona interactiva Drag and Drop */
QFrame#drop_zone {
    background-color: #FFFFFF;
    border: 2px dashed #D4D4D8;
    border-radius: 8px;
    padding: 14px 20px;
}

QFrame#drop_zone:hover {
    border-color: #4CA154;
    background-color: #F9FDF9;
}

/* Tipografía y encabezados */
QLabel#title {
    font-size: 18px;
    font-weight: 700;
    color: #27272A;
    letter-spacing: -0.3px;
}

QLabel#subtitle {
    font-size: 12px;
    color: #71717A;
}

QLabel#metric_label {
    font-size: 11px;
    font-weight: 600;
    color: #71717A;
    letter-spacing: 0.5px;
}

QLabel#metric_value {
    font-size: 18px;
    font-weight: 700;
    color: #27272A;
}

/* Botones estándar */
QPushButton {
    background-color: #FFFFFF;
    color: #3F3F46;
    border: 1px solid #E4E4E7;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #FAFAFA;
    border-color: #D4D4D8;
    color: #27272A;
}

QPushButton:pressed {
    background-color: #F4F4F5;
}

QPushButton:disabled {
    background-color: #FAFAFA;
    color: #A1A1AA;
    border-color: #E4E4E7;
}

/* Botón principal de acción destacado (Limpiar Datos) */
QPushButton#primary_button {
    background-color: #4CA154;
    color: #FFFFFF;
    border: 1px solid #3F8A46;
    border-radius: 7px;
    padding: 9px 22px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#primary_button:hover {
    background-color: #55B05D;
    border-color: #4CA154;
    color: #FFFFFF;
}

QPushButton#primary_button:pressed {
    background-color: #3B7E41;
}

QPushButton#primary_button:disabled {
    background-color: #E4E4E7;
    color: #A1A1AA;
    border-color: #E4E4E7;
}

/* Pestañas de previsualización (TabWidget) */
QTabWidget::pane {
    border: 1px solid #E4E4E7;
    background-color: #FFFFFF;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #F4F4F5;
    color: #71717A;
    border: 1px solid #E4E4E7;
    border-bottom: none;
    padding: 7px 18px;
    font-weight: 500;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #27272A;
    border-top: 2px solid #4CA154;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background-color: #E4E4E7;
    color: #3F3F46;
}

/* Tablas de datos a pantalla completa (TableView) */
QTableView {
    background-color: #FFFFFF;
    alternate-background-color: #FAFAFA;
    color: #3F3F46;
    gridline-color: #F4F4F5;
    border: none;
    border-radius: 6px;
    selection-background-color: #E8F5E9;
    selection-color: #2E7D32;
}

QHeaderView::section {
    background-color: #FAFAFA;
    color: #52525B;
    padding: 7px 10px;
    border: none;
    border-bottom: 1px solid #E4E4E7;
    border-right: 1px solid #F4F4F5;
    font-weight: 600;
    font-size: 11px;
}

/* Barras de desplazamiento sutiles */
QScrollBar:vertical {
    background-color: #F4F4F5;
    width: 7px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #D4D4D8;
    min-height: 20px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background-color: #A1A1AA;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #F4F4F5;
    height: 7px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #D4D4D8;
    min-width: 20px;
    border-radius: 3px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #A1A1AA;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Barra de estado inferior */
QStatusBar {
    background-color: #F4F4F5;
    color: #71717A;
    border-top: 1px solid #E4E4E7;
    font-size: 11px;
}
"""
