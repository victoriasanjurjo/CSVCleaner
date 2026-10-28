# Bitácora de Decisiones de Diseño y Justificación Técnica (ADR)

## ADR-001: Elección de PySide6 para la Interfaz Gráfica
- **Contexto**: Se requiere una GUI de escritorio moderna, robusta y con capacidad de compilarse como binario autónomo para Windows.
- **Decisión**: Utilizar `PySide6` (Qt for Python).
- **Justificación**: Provee integración nativa con el sistema operativo, soporte completo de Drag and Drop, personalización total vía QSS y alto rendimiento en renderizado tabular mediante el modelo `QAbstractTableModel`.

## ADR-002: Estética Monocromática Minimalista (Blanco y Negro)
- **Contexto**: El usuario solicitó explícitamente mantener una estética monocromática en blanco y negro, lo más simple posible.
- **Decisión**: Implementar una paleta basada en contrastes puros `#09090B` y `#FFFFFF` con acentos en escala neutra `#E4E4E7` / `#71717A`.
- **Justificación**: Evita distracciones visuales, permite al analista concentrarse en los datos y asegura un aspecto profesional, sobrio y elegante sin fatiga visual.

## ADR-003: Renderizado Tabular con QAbstractTableModel Virtualizado
- **Contexto**: Cargar DataFrames de decenas de miles de filas en un `QTableWidget` estándar genera latencias inaceptables y bloqueos de interfaz al asignar elementos celda por celda.
- **Decisión**: Extender `QAbstractTableModel` en `PandasTableModel`, limitando la ventana de renderizado activo a un umbral ágil (hasta 5,000 filas en vista previa) manteniendo la integridad completa del DataFrame en memoria para las operaciones.
- **Justificación**: Tiempo de respuesta inmediato e instantáneo en el cambio de pestañas y manipulación de datos.

## ADR-004: Autodetección de Delimitadores y Codificaciones en CSV
- **Contexto**: Los archivos CSV reales provienen de múltiples fuentes (Excel en español que exporta con punto y coma `;`, sistemas Unix con comas `,`, o tabulaciones `\t`), con codificaciones diversas (UTF-8, Latin-1, CP1252).
- **Decisión**: Usar `csv.Sniffer` sobre una muestra inicial del archivo y un mecanismo de reintento secuencial de codificaciones.
- **Justificación**: Elimina fallos comunes de carga sin requerir que el usuario configure manualmente parámetros crípticos.

## ADR-005: Selección Interactiva y Filtrado Previo de Columnas
- **Contexto**: El analista no siempre necesita todas las columnas del dataset original; requiere seleccionar qué campos conservar o descartar antes de aplicar la limpieza para extraer únicamente los datos relevantes.
- **Decisión**: Incorporar un componente de lista de verificación (`QListWidget` con casillas interactivas, acciones masivas `Todas`/`Ninguna`/`Invertir` y buscador en tiempo real) en el panel lateral. El motor `DataCleaner` aplica este filtrado como primera fase del pipeline antes de la desduplicación y normalización.
- **Justificación**: Proporciona control total sobre la dimensionalidad de los datos resultantes, optimizando la memoria y evitando procesar o exportar información innecesaria.

## ADR-006: Simplificación Radical, Eliminación de Módulos Secundarios y Destino en Descargas
- **Contexto**: El usuario solicitó mantener la herramienta lo más simple y rápida posible, eliminando los reportes estadísticos complejos en PDF, los gráficos embebidos (matplotlib/seaborn), el reconocimiento de voz offline (vosk) y las pestañas adicionales de diagnóstico y bitácora en la GUI, así como la carpeta `outputs/`.
- **Decisión**:
  1. Mantener un flujo directo de 1 archivo a la vez con previsualización en 2 pestañas esenciales: **Datos Originales** y **Datos Limpios**.
  2. Sustituir los reportes PDF por un archivo de registro `.txt` estructurado, simple y de texto plano generado automáticamente junto al archivo procesado.
  3. Establecer como carpeta de destino predeterminada el directorio de **Descargas** del sistema (`Downloads`), eliminando por completo el directorio `outputs/`.
  4. Mantener la regla inquebrantable de no modificación del archivo original: se trabaja y exporta siempre sobre una copia.
- **Justificación**: Reduce el peso de dependencias en más del 80%, acelera el tiempo de arranque, simplifica la experiencia de usuario y enfoca la aplicación en su propósito primario: limpiar datos y documentar los cambios de forma clara y directa.
