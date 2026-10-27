# CSVCleaner

**CSVCleaner** es una aplicación de escritorio moderna, minimalista y de alto rendimiento desarrollada con **Python** y **PySide6 (Qt)**, diseñada para la inspección, diagnóstico, limpieza, normalización y exportación de archivos tabulares heterogéneos (**CSV** y **Excel**).

Cuenta con una **estética monocromática de alto contraste (blanco y negro)** orientada a la máxima claridad visual, velocidad operativa y productividad del analista de datos.

---

## Características Principales

- **Carga Flexible y Rápida:**
  - Soporte de arrastrar y soltar (**Drag and Drop**) de archivos `.csv`, `.xlsx`, `.xls` y `.txt`.
  - Autodetección automática de delimitadores (`,`, `;`, `\t`, `|`) mediante `csv.Sniffer`.
  - Detección y fallback de codificaciones de caracteres (`utf-8`, `utf-8-sig`, `latin-1`, `cp1252`).
  - Navegación entre hojas de cálculo múltiples en archivos Excel.

- **Visualización Estadística y Gráficos Profesionales:**
  - Pestaña interactiva **"Gráficos y Visualización"** con lienzo embebido de Matplotlib (`FigureCanvasQTAgg`) y barra de herramientas de navegación (zoom, paneo y ajuste).
  - Tipos de gráficos soportados:
    - **Distribución / Histograma:** Con curva de densidad (KDE) y líneas de media y mediana.
    - **Barras Categóricas (Top N):** Frecuencias absolutas ordenadas con etiquetas cuantitativas.
    - **Dispersión (Scatter Plot):** Correlación de Pearson y recta de regresión lineal.
    - **Diagrama de Caja (Boxplot):** Detección visual de valores atípicos (*outliers*).
    - **Matriz de Correlación (Heatmap):** Mapa de calor en escala de grises con coeficientes numéricos.
  - Exportación de gráficos a imagen en alta resolución (`.png` / `.svg`).
  - **Generación de Reporte Ejecutivo Multi-Página en PDF:** Documento formal con resumen ejecutivo, tabla de estadísticas descriptivas (`describe()`) y gráficos analíticos embebidos en `outputs/`.
  - **Escucha continua no bloqueante**: Implementado en segundo plano con `sounddevice` y `Vosk` (modelo ligero offline en español, 100% privado y sin conexión a internet).
  - **Intérprete en lenguaje natural**: Control total de la interfaz dictando instrucciones como:
    - *"eliminar duplicados y descartar filas vacías"*
    - *"quitar la columna salario y conservar columna edad"*
    - *"seleccionar todas las columnas"* / *"desmarcar todas"*
    - *"normalizar cabeceras a snake case y quitar acentos"*
    - *"eliminar filas con nulos"* o *"rellenar nulos con desconocido"*
    - *"limpiar datos"*, *"exportar csv"*, *"exportar excel"*, *"generar reporte"* o *"reiniciar"*

- **Pipeline de Transformación y Limpieza:**
  - **Selección y descarte interactivo de columnas:** Selección granular con casillas de verificación, buscador dinámico en tiempo real y acciones rápidas (*Todas*, *Ninguna*, *Invertir*). Solo las columnas seleccionadas se conservan en la previsualización y exportación.
  - **Normalización de cabeceras:** Conversión a `snake_case`, `lowercase`, `uppercase` o `title`, con eliminación automática de espacios, puntuación y acentos diacríticos (Unicode NFKD).
  - **Deduplicación:** Detección y eliminación de filas duplicadas con registro cuantitativo de registros colapsados.
  - **Descarte de vacíos:** Eliminación de filas y columnas enteramente compuestas por valores `NaN` / nulos.
  - **Trimming textual:** Recorte de espacios iniciales, finales y reducción de espacios intermedios múltiples en campos de texto.
  - **Tratamiento de nulos configurable:** Eliminación de filas con nulos, imputación por valor fijo, o propagación de valores (`ffill` / `bfill`).

- **Diagnóstico y Visualización en Tiempo Real:**
  - Tarjetas de métricas instantáneas (Total de Filas, Columnas, Filas Duplicadas, Celdas Nulas).
  - Pestañas comparativas: Datos Originales, Datos Limpios, Diagnóstico por Columna (tipo de dato, celdas nulas, porcentaje, valores únicos) y Bitácora Cronológica de Acciones.
  - Renderizado virtualizado mediante `QAbstractTableModel` para garantizar 60 FPS sin bloqueos de interfaz.

- **Exportación y Auditoría:**
  - Exportación de datasets saneados a **CSV** (delimitador configurable) o **Excel (.xlsx)**.
  - Generación automática de **Reporte Ejecutivo de Auditoría en PDF** (maquetado con ReportLab) en la carpeta `outputs/`.

---

## Arquitectura y Estructura del Proyecto

El proyecto sigue una arquitectura desacoplada por capas:

```text
CSVCleaner/
├── .venv/               # Entorno virtual de Python
├── assets/              # Recursos visuales e íconos de la aplicación (.png, .ico)
├── config/              # Parámetros y configuración por defecto (default_config.json)
├── docs/                # Documentación técnica y decisiones de diseño (ADRs)
│   ├── architecture.md
│   └── decisions.md
├── outputs/             # Directorio de salida para reportes generados y exports
├── src/                 # Código fuente modular
│   ├── __init__.py
│   ├── core/            # Capa de negocio e I/O de archivos
│   │   ├── __init__.py
│   │   ├── cleaner.py       # Motor de limpieza y transformaciones
│   │   └── file_handler.py  # Gestor de CSV, Excel y generador de reportes PDF
│   └── ui/              # Capa de presentación gráfica (PySide6)
│       ├── __init__.py
│       ├── main_window.py   # Ventana principal e interacción Drag & Drop
│       ├── styles.py        # Hoja de estilos QSS monocromática
│       └── table_model.py   # Modelo tabular optimizado
├── tests/               # Pruebas unitarias automatizadas
│   ├── __init__.py
│   └── test_cleaner.py
├── .gitignore           # Exclusiones para control de versiones
├── LICENSE.txt          # Licencia MIT de código abierto
├── main.py              # Punto de entrada de la aplicación
├── requirements.txt     # Dependencias instaladas con versiones fijadas
└── README.md            # Documentación exhaustiva del proyecto
```

---

## Requisitos del Sistema

- **Python:** 3.10 o superior (compatible con 3.12+).
- **Sistema Operativo:** Windows 10/11, macOS o Linux.

---

## Instrucciones de Instalación y Ejecución

### 1. Clonar o acceder al directorio del proyecto
```powershell
cd d:\Proyectos\CSVCleaner
```

### 2. Activar el entorno virtual
En Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```

*(O en CMD: `.\.venv\Scripts\activate.bat`)*

### 3. Instalar dependencias (si inicializa en otro entorno)
```powershell
pip install -r requirements.txt
```

## Ejecución desde la Terminal

La forma principal y recomendada de ejecutar la aplicación es directamente desde la terminal con Python:

### 1. Ejecución estándar
```powershell
python main.py
```

### 2. Ejecución directa pasando un archivo como argumento
Puedes abrir la interfaz cargando automáticamente un archivo CSV o Excel pasándole la ruta desde la terminal:
```powershell
python main.py outputs/sample_dirty_data.csv
```
o con rutas absolutas:
```powershell
python main.py "C:\ruta\hacia\tu_archivo.xlsx"
```

---

## Compilación a Ejecutable Autónomo (PyInstaller)

Para empaquetar la aplicación como un ejecutable independiente para Windows sin consola:

```powershell
pyinstaller --noconfirm --onedir --windowed --icon "assets/icon.ico" --add-data "assets;assets" --name "CSVCleaner" main.py
```

El ejecutable final se genera en la carpeta `dist/CSVCleaner/CSVCleaner.exe`.

---

## Licencia

Este proyecto está distribuido bajo la licencia MIT. Consulte el archivo [LICENSE.txt](LICENSE.txt) para más detalles.
