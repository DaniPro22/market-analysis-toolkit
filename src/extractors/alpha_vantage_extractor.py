import pandas as pd
import requests
from src.extractors.extractor_base import ExtractorBase

class ExtractorAlphaVantage(ExtractorBase):
    def __init__(self, api_key: str):
        self.api_key = api_key
        print("-> ExtractorAlphaVantage listo.")

    def obtener_datos(self, tickers: list, fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
        dfs = []
        for ticker in tickers:
            url = "https://www.alphavantage.co/query"
            params = {"function": "TIME_SERIES_DAILY_ADJUSTED",
                      "symbol": ticker, "outputsize": "full", "apikey": self.api_key}
            r = requests.get(url, params=params, timeout=30)
            data = r.json().get("Time Series (Daily)", {})
            if not data:
                print(f"⚠️ AlphaVantage no devolvió datos para {ticker}")
                continue

            df_t = pd.DataFrame(data).T
            df_t.index = pd.to_datetime(df_t.index)
            df_t = df_t.rename(columns={
                '1. open': 'open', '2. high': 'high', '3. low': 'low',
                '4. close': 'close', '6. volume': 'volume'
            })
            df_t = df_t.reset_index().rename(columns={'index': 'date'})
            df_t.columns = [c.lower().replace(' ', '_') for c in df_t.columns]
            # asegurar columnas estándar
            for col in ['open','high','low','close','volume']:
                if col not in df_t.columns:
                    df_t[col] = pd.NA
            df_t['ticker'] = ticker
            dfs.append(df_t[['date','open','high','low','close','volume','ticker']])

        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame(columns=['date','open','high','low','close','volume','ticker'])