# main.py

import os
import pandas as pd
import numpy as np
from src.extractors.interface.cli import (
    seleccionar_tipo_datos,
    seleccionar_extractor,
    pedir_tickers_y_fechas,
    pedir_indicador_macro
)
from src.models.series_precios import SeriePrecios
from src.models.cartera import Cartera
from src.utils.data_tools import quitar_outliers, rellenar_na, validar_df
from src.utils.export_tools import exportar_a_excel


# =========================================================
# 1. Flujo principal
# =========================================================
def main():
    print("\n" + "=" * 60)
    print("ANÁLISIS DE DATOS BURSÁTILES")
    print("=" * 60)

    # Paso 1: Tipo de datos
    tipo_datos = seleccionar_tipo_datos()

    # Paso 2: Elegir extractor compatible
    extractor = seleccionar_extractor(tipo_datos)

    # Paso 3: Inputs según tipo
    if tipo_datos in ["1", "2"]:
        tickers, fecha_inicio, fecha_fin = pedir_tickers_y_fechas()
    else:
        indicador = pedir_indicador_macro()

    # Paso 4: Extracción de datos
    df = pd.DataFrame()

    if tipo_datos == "1":
        print(f"\nDescargando precios de {len(tickers)} activos...")
        df = extractor.obtener_datos(tickers, fecha_inicio, fecha_fin)

    elif tipo_datos == "2":
        print("\nDescargando datos fundamentales...")
        dfs = []
        for t in tickers:
            if hasattr(extractor, "obtener_datos_fundamentales"):
                df_fund = extractor.obtener_datos_fundamentales(t)
                if not df_fund.empty:
                    dfs.append(df_fund)
        if dfs:
            df = pd.concat(dfs, ignore_index=True)
        else:
            print("No se obtuvieron datos fundamentales.")

    elif tipo_datos == "3":
        print(f"\nDescargando indicador macroeconómico '{indicador}'...")
        df = extractor.obtener_datos_macro(indicador)
        if df.empty:
            print("No se obtuvieron datos macroeconómicos.")

    # Paso 5: Validación inicial
    if df.empty:
        print("\nNo se obtuvieron datos válidos. Ejecución finalizada.")
        return

    # --- Mostrar resultados según tipo de datos ---
    if tipo_datos == "1":  # precios
        print("\nDatos obtenidos correctamente. Vista previa:")
        print(df.head())

    elif tipo_datos == "2":  # fundamentales
        print("\nDatos fundamentales obtenidos correctamente.\n")
        if hasattr(extractor, "report_fundamentales"):
            reporte = extractor.report_fundamentales(df)
            print(reporte)

            os.makedirs("reports", exist_ok=True)
            with open("reports/reporte_fundamentales.md", "w", encoding="utf-8") as f:
                f.write(reporte)
            print("📝 Reporte guardado en 'reports/reporte_fundamentales.md'")
        return  # fin del flujo fundamentales

    elif tipo_datos == "3":  # macro
        print("\nDatos macroeconómicos obtenidos correctamente. Vista previa:")
        print(df.head())
        return  # fin del flujo macroeconómico

    # --- Limpieza avanzada opcional ---
    usar_limpieza = input("\n¿Desea aplicar limpieza avanzada (detección de outliers y NaNs)? [s/n]: ").lower()
    if usar_limpieza == "s":
        print("\nAplicando limpieza avanzada de datos...")
        errores = validar_df(df, columnas_unicas=["date", "ticker"], permitir_negativos=["returns"])
        if errores:
            print(f"⚠️ Se detectaron posibles incidencias en los datos ({len(errores)} tipos).")
        df = quitar_outliers(df, columnas=["close"], metodo="percentil")
        df = rellenar_na(df, estrategia="media")
        print("Limpieza avanzada completada.\n")

    # =========================================================
    # 6. Análisis interactivo (solo precios)
    # =========================================================
    def menu_analisis():
        print("\nSeleccione el tipo de análisis:")
        print("1️⃣  Serie individual")
        print("2️⃣  Cartera")
        print("3️⃣  Simulación Monte Carlo")
        print("4️⃣  Volver al menú principal")
        print("5️⃣  Salir")
        return input("Opción [1-5]: ").strip()

    # Crear estructuras (solo una vez)
    series = {t: SeriePrecios(t, df[df["ticker"] == t].copy()) for t in tickers}
    cartera = Cartera(nombre="Mi Cartera")
    for s in series.values():
        cartera.agregar_serie(s)

    while True:
        opcion_analisis = menu_analisis()

        # --- Serie individual ---
        if opcion_analisis == "1":
            print("\n=== 📈 Análisis de Serie Individual ===")
            for serie in series.values():
                reporte = serie.report()
                print(reporte)
                with open(f"reports/reporte_{serie.ticker}.md", "w", encoding="utf-8") as f:
                    f.write(reporte)

        # --- Cartera ---
        elif opcion_analisis == "2":
            print("\n=== 💼 Análisis de Cartera ===")
            reporte_cartera = cartera.report()
            print(reporte_cartera)
            with open(f"reports/reporte_{cartera.nombre.replace(' ', '_')}.md", "w", encoding="utf-8") as f:
                f.write(reporte_cartera)

        # --- Simulación Monte Carlo ---
        elif opcion_analisis == "3":
            print("\n=== 🎲 Simulación Monte Carlo ===")
            try:
                num_days = int(input("Nº de días (default 252): ") or 252)
                num_simulations = int(input("Nº de simulaciones (default 500): ") or 500)
            except ValueError:
                print("⚠️ Valores inválidos, usando parámetros por defecto.")
                num_days, num_simulations = 252, 500

            sim = cartera.simulate_montecarlo(num_days=num_days, num_simulations=num_simulations)
            cartera.plot_last_portfolio_simulation(n_plot=50)

            final_prices = sim.iloc[-1]
            resumen_simulacion = pd.DataFrame({
                "Media precio final": [final_prices.mean()],
                "Desviación": [final_prices.std()],
                "P5": [final_prices.quantile(0.05)],
                "P50 (mediana)": [final_prices.quantile(0.50)],
                "P95": [final_prices.quantile(0.95)]
            })

            print("\n📊 Resumen de la simulación:")
            print(resumen_simulacion.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))

            # Exportar resultados completos
            os.makedirs("outputs", exist_ok=True)
            ruta_excel = f"outputs/analisis_{'_'.join(tickers)}_{fecha_inicio[:4]}.xlsx"
            datos_para_exportar = {
                "Datos Crudos": df,
                "Series Individuales": "\n".join([s.report() for s in series.values()]),
                "Cartera": cartera.report(),
                "Simulación Monte Carlo": resumen_simulacion
            }
            exportar_a_excel(ruta_excel, datos_para_exportar)
            print(f"\n📁 Resultados exportados a: {ruta_excel}")

        # --- Reiniciar flujo ---
        elif opcion_analisis == "4":
            print("\n↩️ Volviendo al menú principal...\n")
            return main()  # reinicio controlado del programa

        # --- Salida limpia ---
        elif opcion_analisis == "5":
            print("\n👋 Gracias por usar el Análisis Bursátil. ¡Hasta pronto!\n")
            break

        else:
            print("⚠️ Opción inválida. Inténtelo de nuevo.")

        input("\nPresiona ENTER para continuar...")


if __name__ == "__main__":
    main()



