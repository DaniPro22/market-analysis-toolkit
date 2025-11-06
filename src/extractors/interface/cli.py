import pandas as pd
from src.extractors.yahoo_finance_extractor import ExtractorYahooFinance
from src.extractors.alpha_vantage_extractor import ExtractorAlphaVantage
from src.extractors.twelvedata_extractor import ExtractorTwelveData
from src.extractors.world_bank_extractor import ExtractorWorldBank

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
    """
    Devuelve el extractor adecuado según el tipo de datos elegido.
    Muestra opciones solo cuando existen varias APIs posibles.
    """
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
        # Solo AlphaVantage soporta datos fundamentales
        print("\nℹ️ Los datos fundamentales solo están disponibles desde AlphaVantage.")
        print("""
        📘 **Datos Fundamentales – Fuente: Alpha Vantage**
        - Solo disponible para empresas cotizadas en EE. UU.
        - Ejemplos válidos: AAPL, MSFT, TSLA, AMZN, META, JPM
        - Los ratios financieros (PER, ROE, margen neto, etc.) se calculan
        a partir de los informes de la SEC (EE. UU.).
        ⚠️ Empresas fuera de EE. UU. (como AENA, BBVA, etc.) no devolverán resultados.
        """)
        return ExtractorAlphaVantage()

    elif tipo_datos == "3":
        print("\nSeleccione la API para datos macroeconómicos:")
        print("""
        🌍 **Datos Macroeconómicos**
        - Fuentes disponibles:
        1️⃣ Alpha Vantage → indicadores globales (GDP, inflación, desempleo, CPI)
            * Países: principales economías (EE. UU., ESP, FRA, DEU, etc.)
        2️⃣ World Bank → base de datos mundial, cobertura más amplia
            * Países disponibles: casi todos los códigos ISO (ESP, USA, MEX, BRA, etc.)
        - Rango temporal: normalmente 2000–actualidad.
        ⚠️ Si un país o indicador no aparece, puede ser por falta de datos oficiales.
        """)

        print("\n1️⃣  AlphaVantage")
        print("2️⃣  World Bank")
        opcion = input("Opción [1-2]: ").strip()

        if opcion == "2":
            return ExtractorWorldBank()
        else:
            return ExtractorAlphaVantage()
        
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
    indicadores = {
        "1": "GDP",
        "2": "INFLATION",
        "3": "UNEMPLOYMENT",
        "4": "CPI",
        "5": "ALL"
    }

    while True:
        print("\nSeleccione el indicador macroeconómico:")
        print("1️⃣  GDP (Producto Interior Bruto)")
        print("2️⃣  INFLATION (Inflación general)")
        print("3️⃣  UNEMPLOYMENT (Desempleo)")
        print("4️⃣  CPI (Índice de Precios al Consumidor)")
        print("5️⃣  Todas las anteriores")
        opcion = input("Opción [1-5]: ").strip()

        if opcion in indicadores:
            return indicadores[opcion]
        else:
            print("⚠️ Opción inválida. Intente nuevamente.")
