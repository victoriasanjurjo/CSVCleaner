"""
Modelo de datos tabular basado en QAbstractTableModel para renderizar DataFrames de pandas.
Optimizado para fluidez y bajo consumo de memoria en la interfaz.
"""
from typing import Any
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
import pandas as pd


class PandasTableModel(QAbstractTableModel):
    """
    Modelo de tabla de solo lectura para visualizar DataFrames de pandas en QTableView.
    """

    def __init__(self, data: pd.DataFrame = None, max_rows: int = 5000):
        super().__init__()
        self._raw_df = data if data is not None else pd.DataFrame()
        self._max_rows = max_rows
        # Limitamos la vista para garantizar 60fps constantes en tablas masivas
        self._df = self._raw_df.iloc[:self._max_rows] if len(self._raw_df) > self._max_rows else self._raw_df

    def set_data(self, data: pd.DataFrame):
        """Actualiza el DataFrame y refresca la vista del modelo."""
        self.beginResetModel()
        self._raw_df = data if data is not None else pd.DataFrame()
        self._df = self._raw_df.iloc[:self._max_rows] if len(self._raw_df) > self._max_rows else self._raw_df
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._df)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._df.columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            val = self._df.iat[index.row(), index.column()]
            if pd.isna(val):
                return ""
            return str(val)

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            # Alinear números a la derecha, texto a la izquierda
            col_type = self._df.dtypes.iloc[index.column()]
            if pd.api.types.is_numeric_dtype(col_type):
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section < len(self._df.columns):
                    return str(self._df.columns[section])
            elif orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        return None

    @property
    def total_rows(self) -> int:
        return len(self._raw_df)

    @property
    def is_truncated(self) -> bool:
        return len(self._raw_df) > self._max_rows
