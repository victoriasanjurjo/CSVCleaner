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

## ADR-004: Inclusión de ReportLab para Auditoría en PDF
- **Contexto**: Las normas del entorno exigen generar reportes ejecutivos en PDF dentro de `outputs/` en aplicaciones de datos.
- **Decisión**: Integrar un generador de reportes en `FileHandler` que compila un documento PDF monocromático con la tabla de diferencias antes/después y el listado cronológico de operaciones.
- **Justificación**: Permite a los usuarios adjuntar un registro formal de trazabilidad a sus pipelines de datos o entregables.

## ADR-005: Autodetección de Delimitadores y Codificaciones en CSV
- **Contexto**: Los archivos CSV reales provienen de múltiples fuentes (Excel en español que exporta con punto y coma `;`, sistemas Unix con comas `,`, o tabulaciones `\t`), con codificaciones diversas (UTF-8, Latin-1, CP1252).
- **Decisión**: Usar `csv.Sniffer` sobre una muestra inicial del archivo y un mecanismo de reintento secuencial de codificaciones.
- **Justificación**: Elimina fallos comunes de carga sin requerir que el usuario configure manualmente parámetros crípticos.

## ADR-006: Selección Interactiva y Filtrado Previo de Columnas
- **Contexto**: El analista no siempre necesita todas las columnas del dataset original; requiere seleccionar qué campos conservar o descartar antes de aplicar la limpieza para extraer únicamente los datos relevantes.
- **Decisión**: Incorporar un componente de lista de verificación (`QListWidget` con casillas interactivas, acciones masivas `Todas`/`Ninguna`/`Invertir` y buscador en tiempo real) en el panel lateral, sincronizado con la tabla de diagnóstico. El motor `DataCleaner` aplica este filtrado como primera fase del pipeline antes de la desduplicación y normalización.
- **Justificación**: Proporciona control total sobre la dimensionalidad de los datos resultantes, optimizando la memoria y evitando procesar o exportar información innecesaria.

## ADR-007: Reconocimiento Continuo de Voz Offline (Vosk + sounddevice)
- **Contexto**: El usuario solicitó la funcionalidad de dictar instrucciones por voz en modo continuo y con modelo offline local.
- **Decisión**: Integrar `vosk` con el modelo ligero en español `vosk-model-small-es-0.42` (~38 MB) y captura continua mediante `sounddevice` en un hilo desacoplado (`QThread`), parseado mediante `VoiceCommandParser`.
- **Justificación**:
  1. **Compatibilidad total con Python 3.15**: A diferencia de paquetes antiguos basados en PyAV/torch que fallan en la compilación de C/Cython sobre 3.15, Vosk dispone de binarios limpios precompilados.
  2. **100% Offline**: Privacidad absoluta sin enviar audio a APIs externas.
  3. **No bloqueante**: La captura en `QThread` no impacta los 60 FPS de la interfaz PySide6.
  4. **Escucha Continua**: Permite hablar de corrido mientras se interactúa con el teclado o el ratón.

## ADR-008: Gráficos Profesionales Embebidos (Matplotlib/Seaborn) y Reporte Ejecutivo Multi-Página
- **Contexto**: Se requiere permitir la generación visual de gráficos estadísticos sobre las variables indicadas por el usuario (vía interfaz o voz) y la compilación de reportes ejecutivos en PDF de máxima calidad visual.
- **Decisión**: Embeber `FigureCanvasQTAgg` y `NavigationToolbar2QT` en una pestaña dedicada de visualización, estructurando la generación mediante `DataAnalytics` y una paleta monocromática elegante (Zinc/Greys). La compilación a PDF se apoya en `ReportLab` integrando tablas `describe()` completas e imágenes renderizadas a 300 DPI.
- **Justificación**: Brinda capacidad analítica de nivel profesional sin abandonar la aplicación, permitiendo zoom, navegación y exportación inmediata a SVG/PNG y PDF formal listo para presentaciones o auditorías.
