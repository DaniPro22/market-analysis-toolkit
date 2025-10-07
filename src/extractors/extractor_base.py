from abc import ABC, abstractmethod
import pandas as pd

class ExtractorBase(ABC):
    @abstractmethod
    def obtener_datos(self, tickers: list, fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
        """
        RETORNO OBLIGATORIO: DataFrame con columnas:
        ['date', 'open', 'high', 'low', 'close', 'volume', 'ticker']
        """
        pass
