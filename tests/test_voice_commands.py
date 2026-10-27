"""
Pruebas unitarias para el intérprete de comandos por voz VoiceCommandParser.
"""
import unittest
from src.core.voice_commands import VoiceCommandParser


class TestVoiceCommandParser(unittest.TestCase):
    """Verificación de patrones de lenguaje natural en comandos de voz."""

    def setUp(self):
        self.columns = ["Nombre", "Edad", "Ciudad", "Salario_USD", "Notas"]

    def test_deduplication_commands(self):
        actions_on = VoiceCommandParser.parse("por favor eliminar duplicados")
        self.assertIn(("set_duplicates", True), actions_on)

        actions_off = VoiceCommandParser.parse("conservar duplicados")
        self.assertIn(("set_duplicates", False), actions_off)

    def test_empty_rows_and_cols(self):
        actions = VoiceCommandParser.parse("descartar filas vacias y descartar columnas vacias")
        self.assertIn(("set_empty_rows", True), actions)
        self.assertIn(("set_empty_cols", True), actions)

    def test_column_selection_mass(self):
        actions_all = VoiceCommandParser.parse("seleccionar todas las columnas")
        self.assertIn(("select_all_columns", None), actions_all)

        actions_none = VoiceCommandParser.parse("desmarcar todas")
        self.assertIn(("select_none_columns", None), actions_none)

        actions_inv = VoiceCommandParser.parse("invertir columnas")
        self.assertIn(("invert_columns", None), actions_inv)

    def test_column_selection_specific(self):
        actions = VoiceCommandParser.parse("quitar la columna salario", available_columns=self.columns)
        self.assertIn(("deselect_column", "Salario_USD"), actions)

        actions_sel = VoiceCommandParser.parse("conservar columna edad", available_columns=self.columns)
        self.assertIn(("select_column", "Edad"), actions_sel)

    def test_header_casing_and_accents(self):
        actions = VoiceCommandParser.parse("normalizar cabeceras a snake case y quitar acentos")
        self.assertIn(("set_clean_headers", True), actions)
        self.assertIn(("set_header_case", "snake_case"), actions)
        self.assertIn(("set_strip_accents", True), actions)

    def test_missing_values(self):
        actions_drop = VoiceCommandParser.parse("eliminar filas con nulos")
        self.assertIn(("set_missing_strategy", "drop_any"), actions_drop)

        actions_fill = VoiceCommandParser.parse("rellenar nulos con desconocido")
        self.assertIn(("set_missing_fill", "desconocido"), actions_fill)

    def test_execution_commands(self):
        actions = VoiceCommandParser.parse("limpiar datos y exportar csv")
        self.assertIn(("action_clean", None), actions)
        self.assertIn(("action_export_csv", None), actions)


if __name__ == "__main__":
    unittest.main()
