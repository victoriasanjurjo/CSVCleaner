# Arquitectura del Sistema - CSVCleaner

## 1. Visión General
**CSVCleaner** es una aplicación de escritorio diseñada bajo el patrón de arquitectura desacoplada y orientada a capas, optimizada para la inspección, limpieza, transformación y exportación de conjuntos de datos en formatos CSV y Excel (.xlsx, .xls).

La estética visual se adhiere a un diseño monocromático minimalista, priorizando alto contraste, legibilidad, rapidez y simplicidad para el usuario técnico o analista de datos.

## 2. Diagrama de Capas

```
┌────────────────────────────────────────────────────────┐
│                   Capa de Presentación                 │
│      PySide6 (Qt) - MainWindow / PandasTableModel      │
│          Estilos QSS Monocromáticos (styles.py)        │
│          Barra de Control por Voz y Estado en Vivo     │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│              Capa de Reconocimiento de Voz             │
│    VoiceListenerWorker (QThread + sounddevice)         │
│    Vosk (Modelo offline en español)                    │
│    VoiceCommandParser (Intérprete semántico en español)│
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                    Capa de Negocio                     │
│    DataCleaner (cleaner.py) - Pipeline de Limpieza     │
│   CleaningOptions / CleaningReport / Métricas Profiling│
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                 Capa de Datos y Archivos               │
│   FileHandler (file_handler.py) - Autodetección CSV    │
│  Lector Excel (openpyxl) & Reporte Auditoría (ReportLab)│
└────────────────────────────────────────────────────────┘
```

## 3. Componentes Principales

### 3.1. Núcleo (`src/core/`)
- **`DataCleaner`**: Implementa transformaciones funcionales no destructivas sobre `pandas.DataFrame`.
  - **Selección y descarte de columnas**: Filtrado declarativo de columnas previo a la limpieza, garantizando que solo los campos elegidos formen parte del dataset procesado, exportado y reportado.
  - Normalización de cabeceras (`snake_case`, `lowercase`, `uppercase`, `title`) con remoción de caracteres no alfanuméricos y acentos vía descomposición Unicode NFKD.
  - Desduplicación con recuento exacto de registros colapsados.
  - Purgado de filas y columnas enteramente vacías.
  - Saneamiento y recorte de espacios múltiples en campos textuales.
  - Estrategias de imputación de valores faltantes (eliminación, valor fijo, ffill, bfill).
  - Cálculo de métricas y metadatos de antes/después estructurados en `CleaningReport`.
- **`DataAnalytics`**: Motor de análisis exploratorio, cálculo de métricas descriptivas y visualización.
  - Generación de gráficos profesionales en matplotlib/seaborn (histogramas con KDE, barras horizontales de categorías, diagramas de dispersión con línea de regresión, matrices de correlación y boxplots para outliers).
  - Generador de reportes ejecutivos avanzados en PDF estructurados con tablas estadísticas y visualizaciones embebidas en alta resolución.
- **`FileHandler`**: Abstracción para el manejo de I/O.
  - Muestreo con `csv.Sniffer` para detectar delimitadores (`,`, `;`, `\t`, `|`).
  - Fallback resiliente de codificación de caracteres (`utf-8`, `utf-8-sig`, `latin-1`, `cp1252`).
  - Detección de hojas de cálculo de libros Excel mediante `openpyxl`.
  - Generador de reportes de auditoría en formato PDF usando `ReportLab` con diseño monocromático formal.

### 3.2. Interfaz de Usuario (`src/ui/`)
- **`MainWindow`**: Coordinador principal de eventos. Soporta carga de archivos mediante Drag & Drop (arrastrar y soltar) o diálogo nativo del sistema operativo.
- **`PandasTableModel`**: Subclase de `QAbstractTableModel` que permite renderizar miles de filas sin congelar el hilo principal de la interfaz, con alineación dinámica según el tipo de dato.
- **`styles.py`**: Hoja de estilos QSS monocromática (blanco puro `#FFFFFF`, negro `#09090B` y tonos de grises de la escala Zinc).

### 3.3. Configuración (`config/`)
- **`default_config.json`**: Parámetros de inicialización y preferencias por defecto de la aplicación.
