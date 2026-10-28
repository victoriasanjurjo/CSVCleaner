"""
Asistente de Instalación Gráfico para CSVCleaner.
Construido con PySide6 y empaquetado como instalador autónomo.
Incluye validación obligatoria de Términos y Condiciones, selección de directorio
(por defecto en Documentos) y creación de acceso directo en el Escritorio.
"""
import sys
import os
import shutil
import zipfile
import subprocess
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QLineEdit, QFileDialog,
    QProgressBar, QStackedWidget, QTextEdit, QTabWidget, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon, QFont


def get_resource_path(relative_path: str) -> Path:
    """Obtiene la ruta a un recurso empaquetado (PyInstaller _MEIPASS) o local."""
    base_path = getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)
    return Path(base_path) / relative_path


def load_text_resource(filename: str) -> str:
    """Lee un archivo de texto empaquetado con fallback de codificación."""
    path = get_resource_path(filename)
    if not path.exists():
        path = Path(__file__).resolve().parent / filename
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            try:
                with open(path, "r", encoding="latin-1", errors="replace") as f:
                    return f.read()
            except Exception:
                pass
    return f"No se pudo cargar el documento: {filename}"


def create_windows_shortcut(target_exe: Path, shortcut_path: Path, icon_path: Optional[Path] = None):
    """Crea un acceso directo .lnk en Windows utilizando PowerShell de forma nativa."""
    try:
        icon_line = f'$Shortcut.IconLocation = "{icon_path}";' if icon_path and icon_path.exists() else ''
        ps_script = f'''
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
        $Shortcut.TargetPath = "{target_exe}"
        $Shortcut.WorkingDirectory = "{target_exe.parent}"
        {icon_line}
        $Shortcut.Save()
        '''
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        )
    except Exception as e:
        print(f"No se pudo crear el acceso directo: {e}")


class InstallWorker(QThread):
    """Hilo secundario para la extracción y configuración no bloqueante de archivos."""
    progress_updated = Signal(int, str)
    finished_signal = Signal(bool, str)

    def __init__(self, target_dir: Path, create_desktop_icon: bool):
        super().__init__()
        self.target_dir = target_dir
        self.create_desktop_icon = create_desktop_icon

    def run(self):
        try:
            self.progress_updated.emit(5, "Creando carpeta de destino...")
            self.target_dir.mkdir(parents=True, exist_ok=True)

            payload_zip = get_resource_path("app_payload.zip")
            if not payload_zip.exists():
                payload_zip = Path(__file__).resolve().parent / "app_payload.zip"

            if payload_zip.exists():
                self.progress_updated.emit(15, "Extrayendo archivos de la aplicación...")
                with zipfile.ZipFile(payload_zip, 'r') as zf:
                    members = zf.infolist()
                    total = len(members)
                    for i, member in enumerate(members, start=1):
                        zf.extract(member, self.target_dir)
                        pct = 15 + int((i / total) * 70)
                        self.progress_updated.emit(pct, f"Copiando: {member.filename}")
            else:
                dist_dir = Path(__file__).resolve().parent / "dist" / "CSVCleaner"
                if dist_dir.exists():
                    self.progress_updated.emit(15, "Copiando binarios del sistema...")
                    files = [f for f in dist_dir.rglob("*") if f.is_file()]
                    total = len(files)
                    for i, f in enumerate(files, start=1):
                        rel = f.relative_to(dist_dir)
                        dest = self.target_dir / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(f, dest)
                        pct = 15 + int((i / total) * 70)
                        self.progress_updated.emit(pct, f"Copiando: {rel}")
                else:
                    raise FileNotFoundError("No se encontró el paquete de instalación (app_payload.zip).")

            # Copiar acuerdos legales y notas
            self.progress_updated.emit(88, "Instalando términos, licencias y notas...")
            terms_src = get_resource_path("TERMINOS_Y_CONDICIONES.txt")
            if terms_src.exists():
                shutil.copy2(terms_src, self.target_dir / "TERMINOS_Y_CONDICIONES.txt")
            license_src = get_resource_path("LICENSE.txt")
            if license_src.exists():
                shutil.copy2(license_src, self.target_dir / "LICENSE.txt")
            readme_src = get_resource_path("LEEME_PRIMERO.txt")
            if readme_src.exists():
                shutil.copy2(readme_src, self.target_dir / "LEEME_PRIMERO.txt")

            # Crear acceso directo en el Escritorio
            if self.create_desktop_icon:
                self.progress_updated.emit(94, "Generando acceso directo en el Escritorio...")
                desktop = Path.home() / "Desktop"
                target_exe = self.target_dir / "CSVCleaner.exe"
                icon_path = self.target_dir / "assets" / "icon.ico"
                if not icon_path.exists():
                    icon_path = self.target_dir / "_internal" / "assets" / "icon.ico"
                if target_exe.exists():
                    create_windows_shortcut(target_exe, desktop / "CSVCleaner.lnk", icon_path)

            self.progress_updated.emit(100, "Instalación completada exitosamente.")
            self.finished_signal.emit(True, "Éxito")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class InstallerWindow(QMainWindow):
    """Ventana del Asistente de Instalación."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asistente de Instalación de CSVCleaner")
        self.resize(680, 520)
        self.setMinimumSize(640, 480)

        icon_path = get_resource_path("assets/icon.png")
        if not icon_path.exists():
            icon_path = Path(__file__).resolve().parent / "assets" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.worker: Optional[InstallWorker] = None
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Contenedor apilado (Paso a paso)
        self.stack = QStackedWidget()

        # Paso 0: Términos y Condiciones + Licencia
        self.page_license = self._create_license_page()
        self.stack.addWidget(self.page_license)

        # Paso 1: Selección de Carpeta y Acceso Directo
        self.page_directory = self._create_directory_page()
        self.stack.addWidget(self.page_directory)

        # Paso 2: Progreso de Instalación
        self.page_progress = self._create_progress_page()
        self.stack.addWidget(self.page_progress)

        # Paso 3: Instalación Finalizada
        self.page_finish = self._create_finish_page()
        self.stack.addWidget(self.page_finish)

        main_layout.addWidget(self.stack)

    # --- PÁGINA 1: TÉRMINOS Y CONDICIONES ---
    def _create_license_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        lbl_title = QLabel("Acuerdo de Licencia y Términos de Servicio")
        lbl_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #27272A;")
        lbl_sub = QLabel("Revise detenidamente los términos y la licencia antes de continuar. Debe aceptarlos para instalar el software.")
        lbl_sub.setStyleSheet("font-size: 12px; color: #71717A;")
        lbl_sub.setWordWrap(True)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_sub)

        # Pestañas con los dos textos legales
        tabs_legal = QTabWidget()

        # Tab Términos y Condiciones
        txt_terms = QTextEdit()
        txt_terms.setReadOnly(True)
        txt_terms.setText(load_text_resource("TERMINOS_Y_CONDICIONES.txt"))
        tabs_legal.addTab(txt_terms, "Términos y Condiciones")

        # Tab Licencia MIT
        txt_license = QTextEdit()
        txt_license.setReadOnly(True)
        txt_license.setText(load_text_resource("LICENSE.txt"))
        tabs_legal.addTab(txt_license, "Licencia de Software (LICENSE.txt)")

        layout.addWidget(tabs_legal, 1)

        # Casilla de Aceptación obligatoria
        self.chk_accept = QCheckBox("He leído y acepto los Términos y Condiciones y la Licencia")
        self.chk_accept.setStyleSheet("font-weight: 600; color: #27272A; font-size: 11pt;")
        self.chk_accept.toggled.connect(self._on_accept_toggled)
        layout.addWidget(self.chk_accept)

        # Barra de botones inferior
        btn_bar = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.close)
        btn_bar.addWidget(btn_cancel)

        btn_bar.addStretch()

        self.btn_next_step1 = QPushButton("Siguiente >")
        self.btn_next_step1.setObjectName("primary_button")
        self.btn_next_step1.setEnabled(False)  # Bloqueado hasta aceptar
        self.btn_next_step1.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        btn_bar.addWidget(self.btn_next_step1)

        layout.addLayout(btn_bar)
        return page

    def _on_accept_toggled(self, checked: bool):
        self.btn_next_step1.setEnabled(checked)

    # --- PÁGINA 2: SELECCIÓN DE CARPETA Y OPCIONES ---
    def _create_directory_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        lbl_title = QLabel("Ubicación de Instalación")
        lbl_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #27272A;")
        lbl_sub = QLabel("El programa se instalará por defecto en la carpeta Documentos de su equipo. Puede modificar la ruta si lo desea.")
        lbl_sub.setStyleSheet("font-size: 12px; color: #71717A;")
        lbl_sub.setWordWrap(True)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_sub)

        # Tarjeta de ruta
        card_dir = QFrame()
        card_dir.setObjectName("card")
        card_layout = QVBoxLayout(card_dir)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(10)

        lbl_path = QLabel("Carpeta de destino:")
        lbl_path.setStyleSheet("font-weight: 600; font-size: 12px; color: #3F3F46;")
        card_layout.addWidget(lbl_path)

        path_box = QHBoxLayout()
        default_install_dir = Path.home() / "Documents" / "CSVCleaner"
        self.txt_install_path = QLineEdit(str(default_install_dir))
        self.txt_install_path.setReadOnly(False)
        path_box.addWidget(self.txt_install_path)

        btn_browse = QPushButton("Examinar...")
        btn_browse.clicked.connect(self._browse_directory)
        path_box.addWidget(btn_browse)
        card_layout.addLayout(path_box)

        layout.addWidget(card_dir)

        # Opciones de accesos directos
        card_opts = QFrame()
        card_opts.setObjectName("card")
        opts_layout = QVBoxLayout(card_opts)
        opts_layout.setContentsMargins(14, 14, 14, 14)
        opts_layout.setSpacing(8)

        lbl_opts = QLabel("Accesos directos:")
        lbl_opts.setStyleSheet("font-weight: 600; font-size: 12px; color: #3F3F46;")
        opts_layout.addWidget(lbl_opts)

        self.chk_desktop = QCheckBox("Crear un ícono de acceso directo en el Escritorio")
        self.chk_desktop.setChecked(True)
        opts_layout.addWidget(self.chk_desktop)

        layout.addWidget(card_opts)
        layout.addStretch()

        # Barra de botones inferior
        btn_bar = QHBoxLayout()
        btn_back = QPushButton("< Atrás")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_bar.addWidget(btn_back)

        btn_bar.addStretch()

        btn_install = QPushButton("Instalar")
        btn_install.setObjectName("primary_button")
        btn_install.clicked.connect(self._start_installation)
        btn_bar.addWidget(btn_install)

        layout.addLayout(btn_bar)
        return page

    def _browse_directory(self):
        chosen = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Carpeta de Instalación",
            str(Path.home() / "Documents")
        )
        if chosen:
            # Apuntar a subcarpeta CSVCleaner dentro de la ruta elegida si no la tiene
            target = Path(chosen)
            if target.name.lower() != "csvcleaner":
                target = target / "CSVCleaner"
            self.txt_install_path.setText(str(target))

    # --- PÁGINA 3: PROGRESO ---
    def _create_progress_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        lbl_title = QLabel("Instalando CSVCleaner...")
        lbl_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #27272A;")
        layout.addWidget(lbl_title)

        self.lbl_status = QLabel("Iniciando copia de archivos...")
        self.lbl_status.setStyleSheet("font-size: 12px; color: #71717A;")
        layout.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #E4E4E7;
                border: 1px solid #D4D4D8;
                border-radius: 6px;
                height: 20px;
                text-align: center;
                color: #27272A;
                font-weight: 600;
            }
            QProgressBar::chunk {
                background-color: #4CA154;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)

        layout.addStretch()
        return page

    def _start_installation(self):
        target_str = self.txt_install_path.text().strip()
        if not target_str:
            QMessageBox.warning(self, "Aviso", "Por favor seleccione una ruta de instalación válida.")
            return

        target_dir = Path(target_str)
        self.stack.setCurrentIndex(2)

        self.worker = InstallWorker(target_dir, self.chk_desktop.isChecked())
        self.worker.progress_updated.connect(self._on_install_progress)
        self.worker.finished_signal.connect(self._on_install_finished)
        self.worker.start()

    def _on_install_progress(self, percent: int, msg: str):
        self.progress_bar.setValue(percent)
        self.lbl_status.setText(msg)

    def _on_install_finished(self, success: bool, message: str):
        if success:
            self.lbl_finish_path.setText(f"Instalado en: {self.txt_install_path.text()}")
            self.stack.setCurrentIndex(3)
        else:
            QMessageBox.critical(self, "Error de Instalación", f"No se pudo completar la instalación:\n{message}")
            self.stack.setCurrentIndex(1)

    # --- PÁGINA 4: FINALIZACIÓN ---
    def _create_finish_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        lbl_title = QLabel("¡Instalación Finalizada con Éxito!")
        lbl_title.setStyleSheet("font-size: 19px; font-weight: 700; color: #2E7D32;")
        layout.addWidget(lbl_title)

        lbl_msg = QLabel("CSVCleaner se ha instalado correctamente en su equipo y está listo para ser utilizado.")
        lbl_msg.setStyleSheet("font-size: 13px; color: #3F3F46;")
        lbl_msg.setWordWrap(True)
        layout.addWidget(lbl_msg)

        card_info = QFrame()
        card_info.setObjectName("card")
        c_layout = QVBoxLayout(card_info)
        c_layout.setContentsMargins(14, 12, 14, 12)
        c_layout.setSpacing(6)

        self.lbl_finish_path = QLabel("Instalado en: ")
        self.lbl_finish_path.setStyleSheet("font-size: 12px; color: #52525B;")
        self.lbl_finish_path.setWordWrap(True)
        c_layout.addWidget(self.lbl_finish_path)

        lbl_terms_note = QLabel("✓ Términos y Condiciones y Licencia registrados en el directorio.")
        lbl_terms_note.setStyleSheet("font-size: 11px; color: #71717A;")
        c_layout.addWidget(lbl_terms_note)

        layout.addWidget(card_info)

        self.chk_launch = QCheckBox("Ejecutar CSVCleaner ahora")
        self.chk_launch.setChecked(True)
        self.chk_launch.setStyleSheet("font-weight: 600; color: #27272A; font-size: 12px;")
        layout.addWidget(self.chk_launch)

        layout.addStretch()

        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        btn_finish = QPushButton("Finalizar")
        btn_finish.setObjectName("primary_button")
        btn_finish.clicked.connect(self._finish_and_exit)
        btn_bar.addWidget(btn_finish)

        layout.addLayout(btn_bar)
        return page

    def _finish_and_exit(self):
        if self.chk_launch.isChecked():
            exe_path = Path(self.txt_install_path.text()) / "CSVCleaner.exe"
            if exe_path.exists():
                try:
                    subprocess.Popen([str(exe_path)], cwd=str(exe_path.parent))
                except Exception as e:
                    print(f"No se pudo iniciar la aplicación: {e}")
        self.close()


def main():
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("CSVCleaner Installer")

    # Hoja de estilos compartida coherente en Modo Claro de Bajo Contraste
    installer_style = """
    QMainWindow, QWidget {
        background-color: #F4F4F5;
        color: #3F3F46;
        font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-size: 10pt;
    }
    QFrame#card {
        background-color: #FFFFFF;
        border: 1px solid #E4E4E7;
        border-radius: 8px;
    }
    QPushButton {
        background-color: #FFFFFF;
        color: #3F3F46;
        border: 1px solid #E4E4E7;
        border-radius: 6px;
        padding: 7px 16px;
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
    QPushButton#primary_button {
        background-color: #4CA154;
        color: #FFFFFF;
        border: 1px solid #3F8A46;
        border-radius: 6px;
        padding: 8px 20px;
        font-weight: 600;
    }
    QPushButton#primary_button:hover {
        background-color: #55B05D;
    }
    QPushButton#primary_button:disabled {
        background-color: #E4E4E7;
        color: #A1A1AA;
        border-color: #E4E4E7;
    }
    QTextEdit {
        background-color: #FFFFFF;
        color: #27272A;
        border: 1px solid #E4E4E7;
        border-radius: 6px;
        padding: 8px;
        font-family: Consolas, monospace;
        font-size: 9.5pt;
    }
    QLineEdit {
        background-color: #FFFFFF;
        color: #27272A;
        border: 1px solid #E4E4E7;
        border-radius: 6px;
        padding: 6px 10px;
    }
    QCheckBox {
        color: #3F3F46;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border: 1.5px solid #D4D4D8;
        border-radius: 3px;
        background-color: #FFFFFF;
    }
    QCheckBox::indicator:hover {
        border-color: #4CA154;
    }
    QCheckBox::indicator:checked {
        background-color: #4CA154;
        border-color: #3F8A46;
    }
    QTabWidget::pane {
        border: 1px solid #E4E4E7;
        background-color: #FFFFFF;
        border-radius: 6px;
    }
    QTabBar::tab {
        background-color: #F4F4F5;
        color: #71717A;
        border: 1px solid #E4E4E7;
        border-bottom: none;
        padding: 6px 14px;
        font-weight: 500;
        margin-right: 2px;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
    }
    QTabBar::tab:selected {
        background-color: #FFFFFF;
        color: #27272A;
        border-top: 2px solid #4CA154;
        font-weight: 600;
    }
    """
    app.setStyleSheet(installer_style)

    window = InstallerWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
