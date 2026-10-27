"""
Módulo de interpretación semántica de comandos por voz en español para CSVCleaner.
Analiza instrucciones orales y las traduce a acciones estructuradas de configuración y ejecución.
"""
import re
import unicodedata
from typing import List, Tuple, Any, Optional


def _clean_text(text: str) -> str:
    """Normaliza texto eliminando acentos, puntuación y dobles espacios."""
    nfkd = unicodedata.normalize('NFKD', text.lower())
    without_accents = "".join([c for c in nfkd if not unicodedata.combining(c)])
    clean = re.sub(r'[^a-z0-9\s]', ' ', without_accents)
    return re.sub(r'\s+', ' ', clean).strip()


class VoiceCommandParser:
    """
    Intérprete de lenguaje natural orientado a comandos de control de la app.
    """

    @classmethod
    def parse(cls, raw_transcript: str, available_columns: Optional[List[str]] = None) -> List[Tuple[str, Any]]:
        """
        Analiza la transcripción de voz y extrae una lista ordenada de acciones a ejecutar.

        :param raw_transcript: Texto reconocido por el motor de voz.
        :param available_columns: Lista de columnas disponibles en el dataset activo (opcional).
        :return: Lista de tuplas (accion, parametro).
        """
        text = _clean_text(raw_transcript)
        actions = []

        if not text:
            return actions

        # 1. Acciones globales / inmediatas
        if any(w in text for w in ["reiniciar", "restablecer", "limpiar todo", "nuevo archivo"]):
            actions.append(("action_reset", None))
            return actions

        # 2. Selección masiva de columnas
        if any(w in text for w in ["desmarcar todas", "deseleccionar todas", "quitar todas", "ninguna columna"]):
            actions.append(("select_none_columns", None))
        elif any(w in text for w in ["todas las columnas", "seleccionar todas", "elegir todas"]) or re.search(r'\bmarcar todas\b', text):
            actions.append(("select_all_columns", None))
        elif any(w in text for w in ["invertir columnas", "invertir seleccion"]):
            actions.append(("invert_columns", None))

        # 3. Selección / Descarte de columnas específicas
        if available_columns:
            # Buscar patrones de exclusión
            deselect_match = re.search(
                r'(?:descartar|quitar|eliminar|sacar|desmarcar|deseleccionar|excluir)\s+(?:la\s+columna\s+|columna\s+)?([a-z0-9_\s]+)',
                text
            )
            if deselect_match:
                col_candidate = deselect_match.group(1).strip()
                best_col = cls._match_column_name(col_candidate, available_columns)
                if best_col:
                    actions.append(("deselect_column", best_col))

            # Buscar patrones de inclusión
            select_match = re.search(
                r'(?:conservar|marcar|seleccionar|elegir|incluir|dejar|mantener)\s+(?:la\s+columna\s+|columna\s+)?([a-z0-9_\s]+)',
                text
            )
            if select_match:
                col_candidate = select_match.group(1).strip()
                best_col = cls._match_column_name(col_candidate, available_columns)
                if best_col:
                    actions.append(("select_column", best_col))

        # 4. Duplicados
        if any(w in text for w in ["no eliminar duplicados", "conservar duplicados", "mantener duplicados", "dejar duplicados"]):
            actions.append(("set_duplicates", False))
        elif any(w in text for w in ["eliminar duplicados", "quitar duplicados", "borrar duplicados", "descartar duplicados", "sin duplicados"]):
            actions.append(("set_duplicates", True))

        # 5. Filas vacías
        if any(w in text for w in ["no descartar filas vacias", "conservar filas vacias", "mantener filas vacias"]):
            actions.append(("set_empty_rows", False))
        elif any(w in text for w in ["descartar filas vacias", "eliminar filas vacias", "quitar filas vacias", "borrar filas vacias"]):
            actions.append(("set_empty_rows", True))

        # 6. Columnas vacías
        if any(w in text for w in ["no descartar columnas vacias", "conservar columnas vacias", "mantener columnas vacias"]):
            actions.append(("set_empty_cols", False))
        elif any(w in text for w in ["descartar columnas vacias", "eliminar columnas vacias", "quitar columnas vacias", "borrar columnas vacias"]):
            actions.append(("set_empty_cols", True))

        # 7. Espacios en blanco (trim)
        if any(w in text for w in ["no recortar espacios", "conservar espacios"]):
            actions.append(("set_trim", False))
        elif any(w in text for w in ["recortar espacios", "quitar espacios", "limpiar espacios", "trim"]):
            actions.append(("set_trim", True))

        # 8. Normalización de cabeceras
        if any(w in text for w in ["no normalizar cabeceras", "no normalizar nombres", "conservar cabeceras"]):
            actions.append(("set_clean_headers", False))
        elif any(w in text for w in ["normalizar cabeceras", "limpiar cabeceras", "normalizar nombres"]):
            actions.append(("set_clean_headers", True))

        # Estilo de capitalización de cabeceras
        if any(w in text for w in ["snake case", "guion bajo", "guiones bajos"]):
            actions.append(("set_header_case", "snake_case"))
        elif any(w in text for w in ["en minusculas", "a minusculas", "todo minusculas"]):
            actions.append(("set_header_case", "lowercase"))
        elif any(w in text for w in ["en mayusculas", "a mayusculas", "todo mayusculas"]):
            actions.append(("set_header_case", "uppercase"))
        elif any(w in text for w in ["tipo titulo", "en titulo", "capitalizado"]):
            actions.append(("set_header_case", "title"))

        # Acentos
        if any(w in text for w in ["quitar acentos", "eliminar tildes", "sin acentos", "sin tildes"]):
            actions.append(("set_strip_accents", True))
        elif any(w in text for w in ["conservar acentos", "mantener tildes", "con acentos"]):
            actions.append(("set_strip_accents", False))

        # 9. Tratamiento de nulos
        if any(w in text for w in ["eliminar filas con nulos", "descartar filas con nulos", "quitar filas con nulos"]):
            actions.append(("set_missing_strategy", "drop_any"))
        elif any(w in text for w in ["conservar nulos", "no modificar nulos", "dejar nulos"]):
            actions.append(("set_missing_strategy", "none"))
        elif any(w in text for w in ["propagar hacia adelante", "ffill", "valor anterior"]):
            actions.append(("set_missing_strategy", "ffill"))
        elif any(w in text for w in ["propagar hacia atras", "bfill", "valor siguiente"]):
            actions.append(("set_missing_strategy", "bfill"))
        else:
            fill_match = re.search(r'rellenar\s+(?:nulos|vacios)\s+con\s+([a-z0-9_\-]+)', text)
            if fill_match:
                actions.append(("set_missing_fill", fill_match.group(1).strip()))

        # 10. Acciones de Gráficos y Visualización
        if any(w in text for w in ["graficar correlacion", "mapa de calor", "heatmap", "matriz de correlacion"]):
            actions.append(("action_plot", {"type": "correlation"}))
        elif any(w in text for w in ["graficar distribucion", "histograma"]):
            col_match = re.search(r'(?:distribucion|histograma)\s+(?:de\s+|para\s+)?([a-z0-9_\s]+)', text)
            col_name = None
            if col_match and available_columns:
                col_name = cls._match_column_name(col_match.group(1).strip(), available_columns)
            actions.append(("action_plot", {"type": "distribution", "col": col_name}))
        elif any(w in text for w in ["graficar barras", "grafico de barras", "frecuencia de"]):
            col_match = re.search(r'(?:barras|frecuencia)\s+(?:de\s+|para\s+)?([a-z0-9_\s]+)', text)
            col_name = None
            if col_match and available_columns:
                col_name = cls._match_column_name(col_match.group(1).strip(), available_columns)
            actions.append(("action_plot", {"type": "bar", "col": col_name}))
        elif any(w in text for w in ["graficar boxplot", "diagrama de caja", "grafico de caja", "outliers"]):
            col_match = re.search(r'(?:boxplot|caja|outliers)\s+(?:de\s+|para\s+)?([a-z0-9_\s]+)', text)
            col_name = None
            if col_match and available_columns:
                col_name = cls._match_column_name(col_match.group(1).strip(), available_columns)
            actions.append(("action_plot", {"type": "box", "col": col_name}))
        elif any(w in text for w in ["graficar dispersion", "grafico de dispersion"]):
            actions.append(("action_plot", {"type": "scatter"}))

        # 11. Acciones de ejecución y reportes
        if any(w in text for w in ["reporte avanzado", "reporte con graficos", "reporte estadistico", "analisis completo"]):
            actions.append(("action_advanced_report", None))
        elif any(w in text for w in ["generar reporte", "reporte pdf", "exportar pdf", "crear reporte"]):
            actions.append(("action_export_pdf", None))

        if any(w in text for w in ["limpiar datos", "ejecutar limpieza", "procesar datos", "limpiar ahora", "procesar"]):
            actions.append(("action_clean", None))

        if any(w in text for w in ["exportar csv", "guardar csv", "descargar csv"]):
            actions.append(("action_export_csv", None))
        elif any(w in text for w in ["exportar excel", "guardar excel", "descargar excel"]):
            actions.append(("action_export_excel", None))

        return actions

    @staticmethod
    def _match_column_name(candidate: str, available_columns: List[str]) -> Optional[str]:
        """Busca la columna existente que mejor coincide con el nombre dictado."""
        cand_clean = _clean_text(candidate)
        if not cand_clean:
            return None

        # 1. Coincidencia exacta limpia
        for col in available_columns:
            if _clean_text(str(col)) == cand_clean:
                return col

        # 2. Coincidencia por contención
        for col in available_columns:
            norm_col = _clean_text(str(col))
            if cand_clean in norm_col or norm_col in cand_clean:
                return col

        return None
