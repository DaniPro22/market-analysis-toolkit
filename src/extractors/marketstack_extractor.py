# src/extractors/marketstack_extractor.py
import pandas as pd
import requests
from src.extractors.extractor_base import ExtractorBase
from src.utils.data_cleaning import limpiar_dataframe

class ExtractorMarketstack(ExtractorBase):
    def __init__(self, api_key: str):
        self.api_key = api_key
        print("-> ExtractorMarketstack listo.")

    def obtener_datos(self, tickers: list, fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
        dfs = []
        base_url = "http://api.marketstack.com/v1/eod"
        for ticker in tickers:
            params = {
                "access_key": self.api_key,
                "symbols": ticker,
                "date_from": fecha_inicio,
                "date_to": fecha_fin,
                "limit": 1000
            }
            r = requests.get(base_url, params=params, timeout=30)
            data = r.json()
            if "data" not in data:
                print(f"⚠️ Marketstack no devolvió datos para {ticker}")
                continue

            df_t = pd.DataFrame(data["data"])
            if df_t.empty:
                continue
            df_t['date'] = pd.to_datetime(df_t['date']).dt.date
            df_t = df_t.rename(columns={
                'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'
            })
            df_t = df_t[['date','open','high','low','close','volume']]
            df_t['ticker'] = ticker
            dfs.append(df_t)

        if dfs:
            df_final = pd.concat(dfs, ignore_index=True)
            df_limpio = limpiar_dataframe(df_final)
            return df_limpio
        else:
            return pd.DataFrame(columns=['date','open','high','low','close','volume','ticker'])

    # Fundamentales: Marketstack no tiene esta info
    def obtener_datos_fundamentales(self, ticker: str) -> pd.DataFrame:
        print(f"⚠️ Marketstack no soporta métricas fundamentales para {ticker}")
        return pd.DataFrame()

    # Macro: Marketstack no soporta indicadores macro
    def obtener_datos_macro(self, indicador: str) -> pd.DataFrame:
        print(f"⚠️ Marketstack no soporta indicadores macro {indicador}")
        return pd.DataFrame()
