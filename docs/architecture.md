# Arquitectura del Sistema - CSVCleaner

## 1. Visión General
**CSVCleaner** es una aplicación de escritorio diseñada bajo el patrón de arquitectura desacoplada y orientada a capas, optimizada para la inspección, limpieza, transformación y exportación no destructiva de datos en formatos CSV y Excel (.xlsx, .xls).

Se rige por el principio de máxima simplicidad, rapidez operativa y claridad:
- Carga de 1 archivo a la vez mediante arrastrar y soltar (Drag and Drop) o explorador de archivos.
- Previsualización inmediata en 2 pestañas: **Datos Originales** y **Datos Limpios**.
- Menú lateral (Sidebar) con opciones de columnas a conservar y reglas de limpieza.
- Carpeta de destino por defecto: **Descargas** (`Downloads`).
- Exportación dual automática: **Archivo limpio** (`.csv` o `.xlsx`) + **Archivo de registro** (`_registro_cambios.txt`). El original nunca es modificado.

## 2. Diagrama de Capas

```text
┌────────────────────────────────────────────────────────┐
│                   Capa de Presentación                 │
│      PySide6 (Qt) - MainWindow / PandasTableModel      │
│          Estilos QSS Monocromáticos (styles.py)        │
│          Panel Lateral de Configuración y Filtros      │
│        Previsualización: Datos Originales y Limpios    │
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
│  Lector Excel (openpyxl) & Exportación TXT / CSV / XLSX│
│       Destino por defecto: Directorio de Descargas     │
└────────────────────────────────────────────────────────┘
```

## 3. Componentes Principales

### 3.1. Núcleo (`src/core/`)
- **`DataCleaner`**: Implementa transformaciones funcionales no destructivas sobre `pandas.DataFrame`.
  - **Selección y descarte de columnas**: Filtrado declarativo de columnas previo a la limpieza, garantizando que solo los campos elegidos formen parte del dataset procesado.
  - Normalización de cabeceras (`snake_case`, `lowercase`, `uppercase`, `title`) con remoción de caracteres no alfanuméricos y acentos vía descomposición Unicode NFKD.
  - Desduplicación con recuento exacto de registros colapsados.
  - Purgado de filas y columnas enteramente vacías.
  - Saneamiento y recorte de espacios múltiples en campos textuales.
  - Estrategias de imputación de valores faltantes (eliminación, valor fijo, ffill, bfill).
  - Cálculo de métricas y metadatos de antes/después estructurados en `CleaningReport`.
- **`FileHandler`**: Abstracción para el manejo de I/O.
  - Muestreo con `csv.Sniffer` para detectar delimitadores (`,`, `;`, `\t`, `|`).
  - Fallback resiliente de codificación de caracteres (`utf-8`, `utf-8-sig`, `latin-1`, `cp1252`).
  - Detección de hojas de cálculo de libros Excel mediante `openpyxl`.
  - Exportación de archivos limpios a CSV y Excel en el directorio `Downloads`.
  - Generación automática del archivo `.txt` con la bitácora simple y estructurada de todas las acciones de limpieza ejecutadas.

### 3.2. Interfaz de Usuario (`src/ui/`)
- **`MainWindow`**: Coordinador principal de eventos. Soporta carga de 1 archivo mediante Drag & Drop (arrastrar y soltar) o diálogo nativo del sistema operativo.
- **`PandasTableModel`**: Subclase de `QAbstractTableModel` que permite renderizar miles de filas sin congelar el hilo principal de la interfaz, con alineación dinámica según el tipo de dato.
- **`styles.py`**: Hoja de estilos monocromática minimalista de alto contraste.
