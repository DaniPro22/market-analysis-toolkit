import pandas as pd
import yfinance as yf
from src.extractors.extractor_base import ExtractorBase

class ExtractorYahooFinance(ExtractorBase):
    def __init__(self):
        print("-> ExtractorYahooFinance listo.")

    def obtener_datos(self, tickers: list, fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
        if isinstance(tickers, str):
            tickers = [tickers]

        raw = yf.download(
            tickers,
            start=fecha_inicio,
            end=fecha_fin,
            group_by='column',
            threads=True
        )
        raw.dropna(how='all', inplace=True)

        dfs = []
        for ticker in tickers:
            # si la descarga tiene MultiIndex (varios tickers)
            if isinstance(raw.columns, pd.MultiIndex):
                try:
                    df_t = raw.xs(ticker, axis=1, level=1).copy()
                except KeyError:
                    print(f"⚠️ Ticker {ticker} no encontrado en la descarga.")
                    continue
            else:
                df_t = raw.copy()

            df_t = df_t.reset_index()
            # normalizar nombres: 'Adj Close' -> 'adj_close', 'Open' -> 'open', etc.
            df_t.columns = [c.lower().replace(' ', '_') if isinstance(c, str) else c for c in df_t.columns]

            # si solo hay adj_close y no close, rellenamos close
            if 'adj_close' in df_t.columns and 'close' not in df_t.columns:
                df_t['close'] = df_t['adj_close']

            # asegurar presencia de columnas estándar (si falta, rellenar con NaN)
            for col in ['date', 'open', 'high', 'low', 'close', 'volume']:
                if col not in df_t.columns:
                    df_t[col] = pd.NA

            df_std = df_t[['date', 'open', 'high', 'low', 'close', 'volume']].copy()
            df_std['ticker'] = ticker
            dfs.append(df_std)

        if dfs:
            return pd.concat(dfs, ignore_index=True)
        else:
            # devolvemos siempre las columnas estándar, aunque vacío
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume', 'ticker'])