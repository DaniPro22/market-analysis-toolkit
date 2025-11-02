import pandas as pd
from src.extractors.yahoo_finance_extractor import ExtractorYahooFinance
from src.extractors.alpha_vantage_extractor import ExtractorAlphaVantage
from src.extractors.twelvedata_extractor import ExtractorTwelveData

from src.models.series_precios import SeriePrecios
from src.models.cartera import Cartera

# =========================================================
# 🔹 1. Selección de tipo de datos
# =========================================================
def seleccionar_tipo_datos():
    print("\n📊 Seleccione el tipo de datos a extraer:")
    print("1️⃣  Precios históricos (acciones o índices)")
    print("2️⃣  Datos fundamentales (ratios financieros)")
    print("3️⃣  Datos macroeconómicos (indicadores país)")
    opcion = input("Opción [1-3]: ").strip()
    return opcion


# =========================================================
# 🔹 2. Selección dinámica del extractor según tipo de dato
# =========================================================
def seleccionar_extractor(tipo_datos):
    if tipo_datos == "1":
        print("\nSeleccione la API para obtener precios:")
        print("1️⃣  Yahoo Finance")
        print("2️⃣  AlphaVantage")
        print("3️⃣  TwelveData")
        opcion = input("Opción [1-3]: ").strip()

        if opcion == "2":
            return ExtractorAlphaVantage()
        elif opcion == "3":
            return ExtractorTwelveData()
        else:
            return ExtractorYahooFinance()

    elif tipo_datos == "2":
        print("\nSeleccione la API para obtener datos fundamentales:")
        print("1️⃣  Yahoo Finance")
        print("2️⃣  AlphaVantage")
        opcion = input("Opción [1-2]: ").strip()

        if opcion == "2":
            return ExtractorAlphaVantage()
        else:
            return ExtractorYahooFinance()

    elif tipo_datos == "3":
        print("\n🔸 Los datos macroeconómicos solo están disponibles desde AlphaVantage.")
        return ExtractorAlphaVantage()

    else:
        print("⚠️ Opción inválida. Se usará Yahoo Finance por defecto.")
        return ExtractorYahooFinance()


# =========================================================
# 🔹 3. Inputs según tipo de dato
# =========================================================
def pedir_tickers_y_fechas():
    tickers = input("Ingrese los tickers separados por coma (ej: AAPL,MSFT,GOOGL): ")
    tickers = [t.strip().upper() for t in tickers.split(",")]
    fecha_inicio = input("Fecha inicio (YYYY-MM-DD): ").strip()
    fecha_fin = input("Fecha fin (YYYY-MM-DD): ").strip()
    return tickers, fecha_inicio, fecha_fin


def pedir_indicador_macro():
    print("\nSeleccione el indicador macroeconómico:")
    print("1️⃣  GDP (Producto Interior Bruto)")
    print("2️⃣  INFLATION (Inflación general)")
    print("3️⃣  UNEMPLOYMENT (Desempleo)")
    print("4️⃣  CPI (Índice de Precios al Consumidor)")
    opcion = input("Opción [1-4]: ").strip()

    mapping = {
        "1": "REAL_GDP",
        "2": "INFLATION",
        "3": "UNEMPLOYMENT",
        "4": "CPI"
    }

    return mapping.get(opcion, "INFLATION")