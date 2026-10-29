"""
Punto de entrada principal para CSVCleaner.
Inicializa la aplicación Qt con estilos monocromáticos y lanza la ventana principal.
"""
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from src.ui.main_window import MainWindow
from src.ui.styles import MONOCHROME_STYLE


def main():
    """Función principal de ejecución del sistema."""
    # Soporte para pantallas de alta densidad de píxeles (HiDPI)
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("CSVCleaner")
    app.setOrganizationName("CSVCleaner")

    # Cargar ícono de aplicación
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    icon_path = base_dir / "assets" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Aplicar diseño y estilos monocromáticos
    app.setStyleSheet(MONOCHROME_STYLE)

    # Capturar archivo pasado como argumento en la terminal si existe
    initial_file = sys.argv[1] if len(sys.argv) > 1 and os.path.exists(sys.argv[1]) else None

    window = MainWindow(initial_file=initial_file)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
