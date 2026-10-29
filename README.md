# CSVCleaner

**CSVCleaner** es una aplicación de escritorio moderna, minimalista y de alto rendimiento desarrollada con **Python** y **PySide6 (Qt)**, diseñada para la inspección, filtrado de columnas, limpieza, normalización y exportación no destructiva de archivos tabulares (**CSV** y **Excel**).

Cuenta con una **estética monocromática de alto contraste (blanco y negro)** orientada a la máxima claridad visual, velocidad operativa y productividad del analista de datos.

---

## Características Principales

- **Carga Simple y Rápida (1 archivo a la vez):**
  * Soporte de arrastrar y soltar (**Drag and Drop**) de archivos `.csv`, `.xlsx`, `.xls` y `.txt`.
  * Diálogo de apertura configurado por defecto en la carpeta de **Descargas** del usuario.
  * Autodetección de delimitadores (`,`, `;`, `\t`, `|`) mediante `csv.Sniffer`.
  * Fallback automático de codificaciones de caracteres (`utf-8`, `utf-8-sig`, `latin-1`, `cp1252`).
  * Selector de hojas de cálculo para libros Excel multichoja.

- **Panel Lateral de Transformación y Limpieza (Sidebar):**
  * **Selección y descarte de columnas:** Casillas interactivas de verificación, buscador en tiempo real y botones de acción rápida (*Todas*, *Ninguna*, *Invertir*). Solo las columnas seleccionadas se conservan en la exportación.
  * **Normalización de cabeceras:** Conversión a `snake_case`, `lowercase`, `uppercase` o `title`, con eliminación opcional de acentos y tildes (Unicode NFKD).
  * **Eliminación de duplicados:** Detección y descarte de filas duplicadas con contabilización exacta.
  * **Descarte de vacíos:** Eliminación de filas y columnas enteramente compuestas por valores `NaN` / nulos.
  * **Trimming textual:** Recorte de espacios iniciales, finales y reducción de espacios intermedios múltiples en campos de texto.
  * **Tratamiento de nulos configurable:** Conservar, eliminar filas con nulos, rellenar con valor fijo o propagar (`ffill` / `bfill`).

- **Previsualización de Datos en Tiempo Real:**
  * Tarjetas de métricas instantáneas (Total de Filas, Columnas, Duplicados, Celdas Nulas).
  * Pestañas comparativas directas:
    * **Datos Originales:** Vista previa intacta del archivo cargado.
    * **Datos Limpios:** Vista previa inmediata de los resultados tras aplicar las reglas de limpieza.
  * Renderizado virtualizado con `QAbstractTableModel` para garantizar fluidez a 60 FPS sin bloqueos.

- **Exportación Dual y Preservación del Original:**
  * **No destructivo:** El archivo original **nunca se modifica**. Todas las operaciones se realizan sobre una copia en memoria.
  * **Destino predeterminado:** Carpeta de **Descargas** del usuario (`Downloads`).
  * **Entrega de 2 archivos por proceso:**
    1. **Archivo limpio:** Guardado como CSV (`.csv`) o Excel (`.xlsx`) según la elección del usuario.
    2. **Registro de cambios (`.txt`):** Archivo de texto plano generado automáticamente junto al archivo limpio, explicando de forma simple las métricas de antes/después y cada una de las operaciones ejecutadas.

---

## Arquitectura y Estructura del Proyecto

```text
CSVCleaner/
├── .venv/               # Entorno virtual de Python
├── assets/              # Recursos visuales e íconos de la aplicación (.png, .ico)
├── config/              # Parámetros y configuración por defecto (default_config.json)
├── docs/                # Documentación técnica y decisiones de diseño (ADRs)
│   ├── architecture.md
│   └── decisions.md
├── src/                 # Código fuente modular
│   ├── __init__.py
│   ├── core/            # Capa de negocio e I/O de archivos
│   │   ├── __init__.py
│   │   ├── cleaner.py       # Motor de limpieza y transformaciones
│   │   └── file_handler.py  # Gestor de lectura/escritura (CSV, Excel y TXT)
│   └── ui/              # Capa de presentación gráfica (PySide6)
│       ├── __init__.py
│       ├── main_window.py   # Ventana principal e interacción Drag & Drop
│       ├── styles.py        # Hoja de estilos QSS monocromática
│       └── table_model.py   # Modelo tabular virtualizado optimizado
├── tests/               # Pruebas unitarias automatizadas
│   ├── __init__.py
│   └── test_cleaner.py      # Pruebas de limpieza y exportación
├── .gitignore           # Exclusiones para control de versiones
├── requirements.txt     # Dependencias instaladas
├── LICENSE.txt          # Licencia MIT de código abierto
├── main.py              # Punto de entrada de la aplicación
└── README.md            # Documentación general y guía de ejecución
```

---

## Requisitos del Sistema

* **Python:** 3.10 o superior (compatible con 3.12 y 3.13+).
* **Sistema Operativo:** Windows 10/11, macOS o Linux.

---

## Instrucciones de Instalación y Ejecución

### 1. Activar el entorno virtual

En Windows (PowerShell):
```powershell
.venv\Scripts\Activate.ps1
```

En Linux/macOS:
```bash
source .venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación

```bash
python main.py
```

### 4. Ejecutar las pruebas unitarias

```bash
python -m unittest discover tests
```

### 5. Compilación del ejecutable (.exe independiente)

Para compilar un archivo ejecutable directo sin necesidad de instalador:

```bash
pyinstaller CSVCleaner.spec --noconfirm --clean
```

El ejecutable resultante estará disponible en [dist/CSVCleaner.exe](file:///d:/Proyectos/Repos/CSVCleaner/dist/CSVCleaner.exe).

---

## Licencia

Distribuido bajo la Licencia MIT. Consulte [LICENSE.txt](file:///d:/Proyectos/Repos/CSVCleaner/LICENSE.txt) para más información.
