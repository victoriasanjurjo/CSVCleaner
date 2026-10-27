"""
Pruebas unitarias para el módulo DataAnalytics (gráficos y reportes ejecutivos con gráficos).
"""
import unittest
import os
import tempfile
import pandas as pd
import numpy as np

from src.core.analytics import DataAnalytics


class TestDataAnalytics(unittest.TestCase):
    """Pruebas de generación de gráficos y compilación de PDF analítico."""

    def setUp(self):
        self.df = pd.DataFrame({
            "Edad": [25, 30, 35, 40, 28, 32, 50, 22],
            "Salario": [1500, 2200, 3100, 4000, 1800, 2500, 6000, 1200],
            "Departamento": ["Ventas", "IT", "Ventas", "IT", "RRHH", "IT", "Ventas", "RRHH"]
        })

    def test_distribution_plot(self):
        fig = DataAnalytics.plot_distribution(self.df, "Edad")
        self.assertIsNotNone(fig)
        self.assertGreater(len(fig.axes), 0)

    def test_categorical_bars_plot(self):
        fig = DataAnalytics.plot_categorical_bars(self.df, "Departamento")
        self.assertIsNotNone(fig)
        self.assertGreater(len(fig.axes), 0)

    def test_scatter_plot(self):
        fig = DataAnalytics.plot_scatter(self.df, "Edad", "Salario")
        self.assertIsNotNone(fig)
        self.assertGreater(len(fig.axes), 0)

    def test_correlation_matrix_plot(self):
        fig = DataAnalytics.plot_correlation_matrix(self.df)
        self.assertIsNotNone(fig)
        self.assertGreater(len(fig.axes), 0)

    def test_box_plot(self):
        fig = DataAnalytics.plot_box(self.df, "Salario")
        self.assertIsNotNone(fig)
        self.assertGreater(len(fig.axes), 0)

    def test_full_analytical_pdf(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_pdf = tmp.name

        try:
            out_path = DataAnalytics.generate_full_analytical_pdf(
                df=self.df,
                dataset_name="TestDataset",
                output_pdf_path=tmp_pdf
            )
            self.assertTrue(os.path.exists(out_path))
            self.assertGreater(os.path.getsize(out_path), 5000)
        finally:
            if os.path.exists(tmp_pdf):
                os.remove(tmp_pdf)


if __name__ == "__main__":
    unittest.main()
