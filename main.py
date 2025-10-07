# main.py
from src.extractors import ExtractorYahooFinance
import pandas as pd

def main():
    # --- Ejemplo con Yahoo Finance ---
    extractor_yahoo = ExtractorYahooFinance()
    tickers = ["AAPL", "MSFT", "GOOGL"]
    fecha_inicio = "2023-01-01"
    fecha_fin = "2023-03-31"

    df_yahoo = extractor_yahoo.obtener_datos(tickers, fecha_inicio, fecha_fin)
    print("Yahoo Finance:")
    print(df_yahoo.head())

    # --- Alpha Vantage (desactivado por falta de API key) ---
    # from src.extractors import ExtractorAlphaVantage
    # api_key = "TU_API_KEY_DE_ALPHA_VANTAGE"
    # extractor_alpha = ExtractorAlphaVantage(api_key)
    # df_alpha = extractor_alpha.obtener_datos(tickers, fecha_inicio, fecha_fin)
    # print("\nAlpha Vantage:")
    # print(df_alpha.head())

if __name__ == "__main__":
    main()
