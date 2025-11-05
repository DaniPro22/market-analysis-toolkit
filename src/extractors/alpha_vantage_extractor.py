import os
import pandas as pd
import requests
from src.extractors.extractor_base import ExtractorBase
from src.utils.data_cleaning import limpiar_dataframe


class ExtractorAlphaVantage(ExtractorBase):
    """
    Extractor para datos de AlphaVantage:
    - Precios históricos
    - Datos fundamentales
    - Indicadores macroeconómicos
    """

    def __init__(self, api_key=None):
        self.api_key = "0SIZNMC3TR9BZFF6"
        self.base_url = "https://www.alphavantage.co/query"

    # ==========================
    # 🔹 Precios históricos
    # ==========================
    def obtener_datos(self, tickers, fecha_inicio, fecha_fin):
        """
        Descarga precios históricos de múltiples tickers desde AlphaVantage.
        Se adapta automáticamente al tipo de cuenta (gratuita/premium).
        """
        import time
        datos_completos = []

        for ticker in tickers:
            print(f"📈 Descargando {ticker} desde AlphaVantage...")

            # --- Intento 1: endpoint ajustado ---
            params = {
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": ticker,
                "outputsize": "full",
                "apikey": self.api_key,
            }

            response = requests.get(self.base_url, params=params)
            data_json = response.json()

            # --- Manejo de mensajes de error o premium ---
            if "Information" in data_json or "Note" in data_json:
                print(f"⚠️ Endpoint premium detectado o límite alcanzado. "
                    f"Cambiando a versión gratuita (TIME_SERIES_DAILY)...")
                # Esperar un poco para evitar rate limit
                time.sleep(15)
                params["function"] = "TIME_SERIES_DAILY"
                response = requests.get(self.base_url, params=params)
                data_json = response.json()

            if "Error Message" in data_json:
                print(f"❌ Error en la solicitud para {ticker}: {data_json['Error Message']}")
                continue

            # --- Validar datos ---
            data = data_json.get("Time Series (Daily)")
            if not data:
                print(f"⚠️ No se pudieron obtener datos para {ticker}. Claves devueltas: {list(data_json.keys())}")
                continue

            # --- Construcción del DataFrame ---
            df = pd.DataFrame.from_dict(data, orient="index").reset_index()

            # Detectar si es versión ajustada o simple
            if len(df.columns) >= 8:
                df.columns = [
                    "date", "open", "high", "low", "close",
                    "adjusted_close", "volume", "dividend_amount", "split_coefficient"
                ]
            else:
                df.columns = ["date", "open", "high", "low", "close", "volume"]

            df["ticker"] = ticker
            df["date"] = pd.to_datetime(df["date"])
            df = df[(df["date"] >= fecha_inicio) & (df["date"] <= fecha_fin)]
            datos_completos.append(df)

            # Esperar 15 segundos para no exceder el límite gratuito (5 llamadas/min)
            time.sleep(15)

        if datos_completos:
            df_total = pd.concat(datos_completos, ignore_index=True)
            return limpiar_dataframe(df_total)
        else:
            return pd.DataFrame()


    # ==========================
    # 🔹 Datos fundamentales
    # ==========================
    def obtener_datos_fundamentales(self, ticker: str):
        print(f"📊 Descargando datos fundamentales para {ticker}...")
        params = {
            "function": "OVERVIEW",
            "symbol": ticker,
            "apikey": self.api_key,
        }
        response = requests.get(self.base_url, params=params)
        data = response.json()

        if not data or "Symbol" not in data:
            print(f"⚠️ No se encontraron datos fundamentales para {ticker}")
            return pd.DataFrame()

        df = pd.DataFrame([data])
        df["ticker"] = ticker
        return (df)
    
    # ==========================
    # 🔹 Reporte resumen fundamentales
    # ==========================
    def report_fundamentales(self, df: pd.DataFrame) -> str:
        """
        Genera un resumen legible de los datos fundamentales descargados.
        """
        if df.empty:
            return "⚠️ No hay datos fundamentales para mostrar.\n"

        def formatear_valor(valor):
            """Convierte grandes números en formato K, M, B, T."""
            try:
                valor = float(valor)
                if valor >= 1e12:
                    return f"{valor/1e12:.2f}T"
                elif valor >= 1e9:
                    return f"{valor/1e9:.2f}B"
                elif valor >= 1e6:
                    return f"{valor/1e6:.2f}M"
                elif valor >= 1e3:
                    return f"{valor/1e3:.2f}K"
                else:
                    return f"{valor:.2f}"
            except (ValueError, TypeError):
                return "-"

        report_lines = ["\n📊 Reporte de datos fundamentales (AlphaVantage)\n"]

        for _, row in df.iterrows():
            try:
                market_cap = formatear_valor(row.get("MarketCapitalization"))
                ebitda = formatear_valor(row.get("EBITDA"))
                div_yield = row.get("DividendYield", "-")
                if isinstance(div_yield, str):
                    div_yield = div_yield.replace("%", "")
                try:
                    div_yield = float(div_yield) * 100
                except:
                    div_yield = div_yield

                report_lines.append(f"\n{row.get('Symbol', '-')}: {row.get('Name', '-')}")
                report_lines.append(f"  • Sector: {row.get('Sector', '-')}, País: {row.get('Country', '-')}")
                report_lines.append(
                    f"  • PER: {row.get('PERatio', '-')}, P/B: {row.get('PriceToBookRatio', '-')}, "
                    f"Div. Yield: {div_yield}%"
                )
                report_lines.append(
                    f"  • Market Cap: {market_cap} USD, EBITDA: {ebitda} USD"
                )
            except Exception as e:
                report_lines.append(f"\nError generando reporte para {row.get('Symbol', '?')}: {e}")

        return "\n".join(report_lines) + "\n"



    # ==========================
    # 🔹 Datos macroeconómicos
    # ==========================
    def obtener_datos_macro(self, indicador: str, start_year: int, end_year: int, pais: str = None):
        """
        Obtiene datos macroeconómicos (GDP, INFLATION, UNEMPLOYMENT, CPI)
        desde AlphaVantage.

        Parámetros
        ----------
        indicador : str
            Nombre del indicador macroeconómico.
        start_year, end_year : int
            Rango de años a obtener.
        pais : str, opcional
            No usado en AlphaVantage, pero incluido por compatibilidad.
        """
        import time

        indicadores_av = {
            "GDP": "REAL_GDP",
            "INFLATION": "INFLATION",
            "UNEMPLOYMENT": "UNEMPLOYMENT",
            "CPI": "CPI"
        }

        if indicador not in indicadores_av:
            raise ValueError(f"Indicador '{indicador}' no soportado por AlphaVantage.")

        url = f"https://www.alphavantage.co/query?function={indicadores_av[indicador]}&apikey={self.api_key}&datatype=json"
        print(f"🔗 Consultando AlphaVantage ({indicador})...")

        response = requests.get(url)
        if response.status_code != 200:
            print(f"⚠️ Error {response.status_code} al conectar con AlphaVantage")
            return pd.DataFrame()

        data = response.json()
        time.sleep(12)  # evita limit rate

        # --- procesamiento general de AlphaVantage macro ---
        key = next((k for k in data.keys() if "data" in k.lower()), None)
        if not key:
            print(f"⚠️ Estructura inesperada en respuesta para {indicador}")
            return pd.DataFrame()

        df = pd.DataFrame(data[key])
        df.columns = [c.upper() for c in df.columns]

        # Normalizar campos típicos
        if "DATE" in df.columns:
            df["YEAR"] = df["DATE"].str[:4].astype(int)
        else:
            df["YEAR"] = pd.to_datetime(df.iloc[:, 0]).dt.year

        df = df[(df["YEAR"] >= start_year) & (df["YEAR"] <= end_year)]

        df["INDICADOR"] = indicador
        df["FUENTE"] = "AlphaVantage"
        df.reset_index(drop=True, inplace=True)
        return df
