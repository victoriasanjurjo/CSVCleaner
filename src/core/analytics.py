"""
Módulo de análisis estadístico, generación de gráficos profesionales y reportes ejecutivos en PDF.
Utiliza matplotlib, seaborn y reportlab para producir visualizaciones de alta calidad acordes
a la estética sobria, moderna y de alto contraste de CSVCleaner.
"""
import os
import tempfile
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('Agg')  # Modo headless para renderizado thread-safe y exportación
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import seaborn as sns

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable


# Paleta monocromática / neutral profesional
CHART_STYLE = {
    "primary_color": "#18181B",    # Negro suave / Zinc 900
    "secondary_color": "#71717A",  # Gris neutro / Zinc 500
    "accent_color": "#27272A",     # Zinc 800
    "grid_color": "#E4E4E7",       # Zinc 200
    "bg_color": "#FFFFFF",         # Blanco puro
    "font_family": "sans-serif"
}


class DataAnalytics:
    """
    Motor de generación de gráficos profesionales y reportes analíticos para conjuntos de datos.
    """

    @classmethod
    def setup_style(cls):
        """Configura los parámetros estéticos globales de matplotlib y seaborn."""
        sns.set_theme(style="whitegrid", font=CHART_STYLE["font_family"])
        plt.rcParams.update({
            "figure.facecolor": CHART_STYLE["bg_color"],
            "axes.facecolor": CHART_STYLE["bg_color"],
            "axes.edgecolor": CHART_STYLE["primary_color"],
            "axes.labelcolor": CHART_STYLE["primary_color"],
            "xtick.color": CHART_STYLE["primary_color"],
            "ytick.color": CHART_STYLE["primary_color"],
            "grid.color": CHART_STYLE["grid_color"],
            "grid.linestyle": "--",
            "grid.alpha": 0.7,
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.labelweight": "normal"
        })

    @classmethod
    def plot_distribution(cls, df: pd.DataFrame, column: str, bins: int = 20) -> Figure:
        """
        Genera un histograma con curva de densidad (KDE) para una variable numérica.
        """
        cls.setup_style()
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)

        series = pd.to_numeric(df[column], errors='coerce').dropna()
        if series.empty:
            ax.text(0.5, 0.5, f"La columna '{column}' no contiene valores numéricos válidos",
                    ha='center', va='center', transform=ax.transAxes, color=CHART_STYLE["secondary_color"])
            fig.tight_layout()
            return fig

        sns.histplot(series, bins=bins, kde=True, color=CHART_STYLE["primary_color"],
                     edgecolor=CHART_STYLE["bg_color"], linewidth=1, ax=ax)

        ax.set_title(f"Distribución Estadística: {column}", pad=12)
        ax.set_xlabel(column)
        ax.set_ylabel("Frecuencia")

        # Añadir línea de media y mediana
        mean_val = series.mean()
        median_val = series.median()
        ax.axvline(mean_val, color="#000000", linestyle="--", linewidth=1.5, label=f"Media: {mean_val:.2f}")
        ax.axvline(median_val, color=CHART_STYLE["secondary_color"], linestyle=":", linewidth=1.5, label=f"Mediana: {median_val:.2f}")
        ax.legend(frameon=True, facecolor=CHART_STYLE["bg_color"], edgecolor=CHART_STYLE["grid_color"])

        fig.tight_layout()
        return fig

    @classmethod
    def plot_categorical_bars(cls, df: pd.DataFrame, column: str, top_n: int = 10) -> Figure:
        """
        Genera un gráfico de barras horizontales de las categorías más frecuentes.
        """
        cls.setup_style()
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)

        counts = df[column].dropna().astype(str).value_counts().head(top_n)
        if counts.empty:
            ax.text(0.5, 0.5, f"No hay datos para la columna '{column}'",
                    ha='center', va='center', transform=ax.transAxes, color=CHART_STYLE["secondary_color"])
            fig.tight_layout()
            return fig

        y_pos = np.arange(len(counts))
        bars = ax.barh(y_pos, counts.values, color=CHART_STYLE["primary_color"], edgecolor=CHART_STYLE["accent_color"], height=0.6)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(counts.index)
        ax.invert_yaxis()  # La categoría más frecuente arriba

        # Etiquetas con el valor en la punta de cada barra
        for bar in bars:
            w = bar.get_width()
            ax.text(w + (max(counts.values) * 0.01), bar.get_y() + bar.get_height() / 2,
                    f"{int(w):,}", va='center', ha='left', fontsize=9, color=CHART_STYLE["primary_color"], fontweight="bold")

        ax.set_title(f"Frecuencia por Categoría (Top {len(counts)}): {column}", pad=12)
        ax.set_xlabel("Cantidad de Registros")
        ax.set_ylabel("Categoría")
        fig.tight_layout()
        return fig

    @classmethod
    def plot_scatter(cls, df: pd.DataFrame, col_x: str, col_y: str) -> Figure:
        """
        Genera un gráfico de dispersión (Scatter Plot) entre dos variables cuantitativas con línea de tendencia.
        """
        cls.setup_style()
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)

        temp_df = df[[col_x, col_y]].dropna()
        temp_df[col_x] = pd.to_numeric(temp_df[col_x], errors='coerce')
        temp_df[col_y] = pd.to_numeric(temp_df[col_y], errors='coerce')
        temp_df = temp_df.dropna()

        if len(temp_df) < 2:
            ax.text(0.5, 0.5, f"No hay suficientes datos numéricos entre '{col_x}' y '{col_y}'",
                    ha='center', va='center', transform=ax.transAxes, color=CHART_STYLE["secondary_color"])
            fig.tight_layout()
            return fig

        sns.regplot(data=temp_df, x=col_x, y=col_y, ax=ax,
                    scatter_kws={"color": CHART_STYLE["primary_color"], "alpha": 0.6, "s": 35},
                    line_kws={"color": "#000000", "linewidth": 2})

        corr = temp_df[col_x].corr(temp_df[col_y])
        ax.set_title(f"Relación: {col_x} vs {col_y} (Correlación r = {corr:.2f})", pad=12)
        ax.set_xlabel(col_x)
        ax.set_ylabel(col_y)
        fig.tight_layout()
        return fig

    @classmethod
    def plot_correlation_matrix(cls, df: pd.DataFrame) -> Figure:
        """
        Genera un mapa de calor (Heatmap) de correlación de Pearson entre todas las variables numéricas.
        """
        cls.setup_style()
        fig, ax = plt.subplots(figsize=(8, 5.5), dpi=100)

        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] < 2:
            ax.text(0.5, 0.5, "Se requieren al menos 2 columnas numéricas para calcular la correlación",
                    ha='center', va='center', transform=ax.transAxes, color=CHART_STYLE["secondary_color"])
            fig.tight_layout()
            return fig

        corr_matrix = numeric_df.corr()
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))

        # Colormap monocromático de grises y negros elegantes
        cmap = sns.diverging_palette(0, 0, l=15, s=0, as_cmap=True)
        sns.heatmap(corr_matrix, mask=mask, cmap="Greys", vmin=-1, vmax=1, annot=True,
                    fmt=".2f", square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}, ax=ax)

        ax.set_title("Matriz de Correlación Numérica (Pearson)", pad=12)
        fig.tight_layout()
        return fig

    @classmethod
    def plot_box(cls, df: pd.DataFrame, column: str) -> Figure:
        """
        Genera un diagrama de caja (Boxplot) para detección de valores atípicos (outliers).
        """
        cls.setup_style()
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)

        series = pd.to_numeric(df[column], errors='coerce').dropna()
        if series.empty:
            ax.text(0.5, 0.5, f"La columna '{column}' no contiene valores numéricos válidos",
                    ha='center', va='center', transform=ax.transAxes, color=CHART_STYLE["secondary_color"])
            fig.tight_layout()
            return fig

        sns.boxplot(x=series, color="#F4F4F5", boxprops=dict(edgecolor=CHART_STYLE["primary_color"], linewidth=1.5),
                    whiskerprops=dict(color=CHART_STYLE["primary_color"], linewidth=1.5),
                    medianprops=dict(color="#000000", linewidth=2),
                    capprops=dict(color=CHART_STYLE["primary_color"], linewidth=1.5),
                    flierprops=dict(marker="o", markerfacecolor=CHART_STYLE["secondary_color"], markersize=5),
                    ax=ax)

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        outliers = series[(series < (q1 - 1.5 * iqr)) | (series > (q3 + 1.5 * iqr))]

        ax.set_title(f"Diagrama de Caja y Outliers: {column} ({len(outliers)} atípicos detectados)", pad=12)
        ax.set_xlabel(column)
        fig.tight_layout()
        return fig

    @classmethod
    def generate_full_analytical_pdf(cls, df: pd.DataFrame, dataset_name: str, output_pdf_path: str) -> str:
        """
        Genera un reporte analítico exhaustivo y profesional en PDF con tablas y gráficos embebidos.
        Cumple estrictamente con las directrices de presentación formal y estética monocromática.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)
        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#09090B'),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#52525B'),
            spaceAfter=12
        )
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#18181B'),
            spaceBefore=12,
            spaceAfter=8
        )
        cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#27272A')
        )
        cell_header_style = ParagraphStyle(
            'TableHeadCell',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#FFFFFF')
        )

        elements = []

        # 1. Cabecera formal
        elements.append(Paragraph("Reporte de Análisis Estadístico y Calidad de Datos", title_style))
        elements.append(Paragraph(f"Dataset analizado: <b>{dataset_name}</b> | Registros: <b>{len(df):,}</b> | Columnas: <b>{len(df.columns)}</b>", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E4E4E7'), spaceBefore=2, spaceAfter=10))

        # 2. Resumen Descriptivo de Columnas Numéricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            elements.append(Paragraph("1. Métricas Descriptivas de Variables Numéricas", section_style))
            desc_df = df[numeric_cols].describe().T.reset_index()

            headers = ["Variable", "Recuento", "Media", "Desv. Est.", "Mín.", "25%", "Mediana", "75%", "Máx."]
            table_rows = [[Paragraph(h, cell_header_style) for h in headers]]

            for _, row in desc_df.iterrows():
                table_rows.append([
                    Paragraph(str(row["index"]), cell_style),
                    Paragraph(f"{int(row['count']):,}", cell_style),
                    Paragraph(f"{row['mean']:.2f}", cell_style),
                    Paragraph(f"{row['std']:.2f}" if pd.notna(row['std']) else "-", cell_style),
                    Paragraph(f"{row['min']:.2f}", cell_style),
                    Paragraph(f"{row['25%']:.2f}", cell_style),
                    Paragraph(f"{row['50%']:.2f}", cell_style),
                    Paragraph(f"{row['75%']:.2f}", cell_style),
                    Paragraph(f"{row['max']:.2f}", cell_style),
                ])

            desc_table = Table(table_rows, colWidths=[90, 50, 55, 55, 50, 50, 50, 50, 50])
            desc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#18181B')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E4E4E7')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F4F4F5')]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(desc_table)
            elements.append(Spacer(1, 12))

        # 3. Gráficos Embebidos
        temp_img_files = []
        try:
            elements.append(Paragraph("2. Visualizaciones Analíticas Profesionales", section_style))

            # Gráfico 1: Distribución de la variable numérica principal
            if numeric_cols:
                main_num = numeric_cols[0]
                fig_dist = cls.plot_distribution(df, main_num)
                fd, path_dist = tempfile.mkstemp(suffix=".png")
                os.close(fd)
                fig_dist.savefig(path_dist, format="png", dpi=180, bbox_inches="tight")
                plt.close(fig_dist)
                temp_img_files.append(path_dist)

                elements.append(Image(path_dist, width=7.2 * 72, height=3.6 * 72))
                elements.append(Spacer(1, 10))

            # Gráfico 2: Matriz de correlación si hay 2+ numéricas
            if len(numeric_cols) >= 2:
                fig_corr = cls.plot_correlation_matrix(df)
                fd, path_corr = tempfile.mkstemp(suffix=".png")
                os.close(fd)
                fig_corr.savefig(path_corr, format="png", dpi=180, bbox_inches="tight")
                plt.close(fig_corr)
                temp_img_files.append(path_corr)

                elements.append(Image(path_corr, width=7.2 * 72, height=4.2 * 72))
                elements.append(Spacer(1, 10))

            # Gráfico 3: Categorías principales si hay columnas categóricas
            cat_cols = df.select_dtypes(include=['object', 'string', 'category']).columns.tolist()
            if cat_cols:
                main_cat = cat_cols[0]
                fig_bar = cls.plot_categorical_bars(df, main_cat, top_n=8)
                fd, path_bar = tempfile.mkstemp(suffix=".png")
                os.close(fd)
                fig_bar.savefig(path_bar, format="png", dpi=180, bbox_inches="tight")
                plt.close(fig_bar)
                temp_img_files.append(path_bar)

                elements.append(Image(path_bar, width=7.2 * 72, height=3.6 * 72))
                elements.append(Spacer(1, 10))

            doc.build(elements)

        finally:
            # Limpiar archivos temporales de imagen
            for temp_f in temp_img_files:
                if os.path.exists(temp_f):
                    try:
                        os.remove(temp_f)
                    except Exception:
                        pass

        return output_pdf_path
