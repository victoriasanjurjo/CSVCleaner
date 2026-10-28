"""
Pruebas unitarias para el motor de limpieza de datos y manejo de archivos.
"""
import unittest
import os
import tempfile
import pandas as pd
import numpy as np

from src.core.cleaner import DataCleaner, CleaningOptions, CleaningReport
from src.core.file_handler import FileHandler


class TestDataCleaner(unittest.TestCase):
    """Pruebas unitarias de DataCleaner."""

    def setUp(self):
        self.sample_data = {
            " Nombre Completo ": ["  Juan Pérez  ", "María Gómez", "Juan Pérez  ", None, np.nan],
            "EDAD / AÑOS": [25, 30, 25, None, np.nan],
            "Ciudad": [" Buenos Aires ", "Córdoba", " Buenos Aires ", None, np.nan],
            "ColumnaVacia": [np.nan, np.nan, np.nan, np.nan, np.nan]
        }
        self.df = pd.DataFrame(self.sample_data)

    def test_header_normalization(self):
        """Prueba la normalización forzada a snake_case."""
        norm = DataCleaner.normalize_header(" Nombre Completo ", strip_accents=True)
        self.assertEqual(norm, "nombre_completo")

        norm_accents = DataCleaner.normalize_header("Año de Nacimiento", strip_accents=True)
        self.assertEqual(norm_accents, "ano_de_nacimiento")

    def test_cleaning_pipeline(self):
        """Prueba la secuencia completa de limpieza."""
        options = CleaningOptions(
            remove_duplicates=True,
            drop_empty_rows=True,
            drop_empty_cols=True,
            trim_whitespace=True,
            clean_headers=True,
            strip_accents=True,
            handle_missing="none"
        )
        cleaned, report = DataCleaner.clean(self.df, options)

        # La columna completamente vacía debe haberse eliminado
        self.assertNotIn("columnavacia", cleaned.columns)

        # Cabeceras normalizadas
        self.assertIn("nombre_completo", cleaned.columns)
        self.assertIn("edad_anos", cleaned.columns)

        # Filas vacías eliminadas
        self.assertGreater(report.empty_rows_dropped, 0)

        # Duplicados eliminados ("Juan Pérez")
        self.assertEqual(report.duplicates_removed, 1)

        # Espacios en blanco recortados
        names = cleaned["nombre_completo"].tolist()
        self.assertIn("Juan Pérez", names)
        self.assertIn("María Gómez", names)

    def test_missing_fill_value(self):
        """Prueba el relleno de valores faltantes."""
        options = CleaningOptions(
            remove_duplicates=False,
            drop_empty_rows=False,
            drop_empty_cols=False,
            trim_whitespace=False,
            clean_headers=False,
            handle_missing="fill_value",
            missing_fill_value="DESCONOCIDO"
        )
        cleaned, report = DataCleaner.clean(self.df, options)
        self.assertEqual(cleaned["Ciudad"].iloc[3], "DESCONOCIDO")

    def test_column_selection(self):
        """Prueba que solo se conserven las columnas seleccionadas."""
        options = CleaningOptions(
            selected_columns=[" Nombre Completo ", "Ciudad"],
            clean_headers=True
        )
        cleaned, report = DataCleaner.clean(self.df, options)
        self.assertEqual(len(cleaned.columns), 2)
        self.assertIn("nombre_completo", cleaned.columns)
        self.assertIn("ciudad", cleaned.columns)
        self.assertNotIn("edad_anos", cleaned.columns)
        self.assertNotIn("columnavacia", cleaned.columns)

    def test_column_selection_empty_raises(self):
        """Prueba que seleccionar 0 columnas válidas lance ValueError."""
        options = CleaningOptions(selected_columns=[])
        with self.assertRaises(ValueError):
            DataCleaner.clean(self.df, options)


class TestFileHandler(unittest.TestCase):
    """Pruebas unitarias de importación y exportación de archivos."""

    def test_csv_roundtrip(self):
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "item": ["Alfa", "Beta", "Gamma"]
        })
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            FileHandler.export_csv(df, tmp_path, delimiter=";")
            loaded_df, enc, sep = FileHandler.load_csv(tmp_path)
            self.assertEqual(sep, ";")
            self.assertEqual(len(loaded_df), 3)
            self.assertEqual(list(loaded_df.columns), ["id", "item"])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_excel_roundtrip(self):
        df = pd.DataFrame({
            "col_a": [10, 20],
            "col_b": ["x", "y"]
        })
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            FileHandler.export_excel(df, tmp_path, sheet_name="DatosTest")
            loaded_df, sheet = FileHandler.load_excel(tmp_path)
            self.assertEqual(sheet, "DatosTest")
            self.assertEqual(len(loaded_df), 2)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_export_txt_log(self):
        report = CleaningReport(
            rows_before=100,
            rows_after=95,
            cols_before=5,
            cols_after=4,
            duplicates_removed=3,
            empty_rows_dropped=2,
            empty_cols_dropped=1,
            missing_cells_before=10,
            missing_cells_after=2,
            operations_log=["Eliminación de duplicados", "Trimming de texto"]
        )
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            out_file = FileHandler.export_txt_log(report, "prueba.csv", tmp_path)
            self.assertTrue(os.path.exists(out_file))
            with open(out_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("prueba.csv", content)
            self.assertIn("100 (antes) -> 95 (después)", content)
            self.assertIn("Eliminación de duplicados", content)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
