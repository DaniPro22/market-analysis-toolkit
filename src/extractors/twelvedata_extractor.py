import os
import pandas as pd
import requests
from src.extractors.extractor_base import ExtractorBase
from src.utils.data_cleaning import limpiar_dataframe


class ExtractorTwelveData(ExtractorBase):
    """
    Extractor para datos de TwelveData.
    Solo soporta datos de precios.
    """

    def __init__(self, api_key=None):
        self.api_key = "ec4022f800244ac291656f7964340a70"
        self.base_url = "https://api.twelvedata.com"

    # ==========================
    # 🔹 Precios históricos
    # ==========================
    def obtener_datos(self, tickers, fecha_inicio, fecha_fin):
        datos_completos = []

        for ticker in tickers:
            print(f"📈 Descargando {ticker} desde TwelveData...")
            params = {
                "symbol": ticker,
                "interval": "1day",
                "apikey": self.api_key,
                "start_date": fecha_inicio,
                "end_date": fecha_fin,
                "format": "JSON",
            }
            response = requests.get(f"{self.base_url}/time_series", params=params)
            data = response.json().get("values", [])

            if not data:
                print(f"⚠️ No se pudieron obtener datos para {ticker}")
                continue

            df = pd.DataFrame(data)
            df["ticker"] = ticker
            df["datetime"] = pd.to_datetime(df["datetime"])
            df.rename(columns={"datetime": "date"}, inplace=True)
            datos_completos.append(df)

        if datos_completos:
            df_total = pd.concat(datos_completos, ignore_index=True)
            return limpiar_dataframe(df_total)
        else:
            return pd.DataFrame()

    # ==========================
    # 🔸 No soporta fundamentales ni macro
    # ==========================
    def obtener_datos_fundamentales(self, ticker: str) -> pd.DataFrame:
        print(f"⚠️ TwelveData no soporta métricas fundamentales para {ticker}")
        return pd.DataFrame()

    def obtener_datos_macro(self, indicador: str) -> pd.DataFrame:
        print(f"⚠️ TwelveData no soporta indicadores macroeconómicos ({indicador})")
        return pd.DataFrame()
