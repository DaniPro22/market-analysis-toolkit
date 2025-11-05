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
from src.utils.data_tools import quitar_outliers, rellenar_na, validar_df, sincronizar_fechas
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
    # ====================================================
    # Mensaje informativo según extractor seleccionado
    # ====================================================
    if tipo_datos == "1":  # PRECIOS HISTÓRICOS
        print("\n🧭 Guía de uso del extractor seleccionado:")

        if "Yahoo" in str(type(extractor)):
            print("""
    📊 **Yahoo Finance**
    - Cobertura global: acciones, ETFs, índices, criptos y materias primas.
    - Formato de ticker:
    - 🇪🇸 España: AENA.MC, BBVA.MC, IBE.MC
    - 🇩🇪 Alemania: BMW.DE, SAP.DE
    - 🇫🇷 Francia: AIR.PA, MC.PA
    - 🇺🇸 EE.UU.: AAPL, TSLA, JPM
    - 🪙 Criptos: BTC-USD, ETH-USD
    - No requiere API key.
    ⚠️ Usa el sufijo del mercado correcto (.MC, .PA, .DE, etc.) o no se descargarán datos.
    """)

        elif "AlphaVantage" in str(type(extractor)):
            print("""
    📊 **Alpha Vantage**
    - Enfoque principal: acciones y ETFs de EE. UU.
    - También soporta algunos mercados globales (pero cobertura parcial).
    - Ejemplos de tickers válidos:
    - 🇺🇸 AAPL, MSFT, TSLA, JPM, META
    - No garantiza datos para Europa (ej. AENA, BBVA, etc.).
    ⚠️ Requiere API key gratuita y puede limitar llamadas (5 por minuto).
    """)

        elif "TwelveData" in str(type(extractor)):
            print("""
    📊 **Twelve Data**
    - Cobertura global (acciones, índices, ETFs, criptos, forex), pero:
      ⚠️ **El plan gratuito solo incluye acciones y ETFs de EE. UU.**
    - Mercados accesibles sin suscripción:
      • 🇺🇸 NASDAQ → AAPL, MSFT, TSLA:
      • 🇺🇸 NYSE → JPM, KO, DIS
    - Mercados **no disponibles en el plan gratuito**:
      • 🇪🇸 España (BMAD): AENA:BMAD, BBVA:BMAD ❌
      • 🇫🇷 Francia (EURONEXT): AIR:EURONEXT ❌
      • 🇩🇪 Alemania (XETR): BMW:XETR ❌
    - Requiere API key (gratuita con 8 llamadas/minuto).
    - Ideal para: datos diarios o intradía de activos estadounidenses.
    💡 Consejo: Para acciones europeas, usa el extractor de Yahoo Finance.
    """)


    # Paso 3: Inputs según tipo
    if tipo_datos in ["1", "2"]:
        tickers, fecha_inicio, fecha_fin = pedir_tickers_y_fechas()
    else:
        indicador = pedir_indicador_macro()

    # Paso 4: Extracción de datos
    df = pd.DataFrame()

    # ====================================================
    # TIPO 1 - PRECIOS HISTÓRICOS
    # ====================================================
    if tipo_datos == "1":
        print(f"\nDescargando precios de {len(tickers)} activos...")
        df = extractor.obtener_datos(tickers, fecha_inicio, fecha_fin)

    # ====================================================
    # TIPO 2 - DATOS FUNDAMENTALES
    # ====================================================
    elif tipo_datos == "2":

        print("\nDescargando datos fundamentales...")
        dfs = []
        for t in tickers:
            if hasattr(extractor, "obtener_datos_fundamentales"):
                print(f"📊 Descargando datos fundamentales para {t}...")
                df_fund = extractor.obtener_datos_fundamentales(t)
                if not df_fund.empty:
                    dfs.append(df_fund)
        if dfs:
            df = pd.concat(dfs, ignore_index=True)
        else:
            print("⚠️ No se obtuvieron datos fundamentales.")

    # ====================================================
    # TIPO 3 - DATOS MACROECONÓMICOS
    # ====================================================
    elif tipo_datos == "3":
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

        print("\n🌍 Análisis de datos macroeconómicos")

        # === Pedir país y rango temporal ===
        pais = input("Ingrese el país (código ISO o nombre, ej. USA, FRA, ESP): ").strip().upper()
        rango = input("Ingrese el rango de años (ej. 2010-2025): ").strip()
        try:
            anio_inicio, anio_fin = [int(x) for x in rango.split("-")]
        except:
            anio_inicio, anio_fin = (2010, 2025)

        all_data = {}
        continuar = True

        while continuar:
            indicadores = ["GDP", "INFLATION", "UNEMPLOYMENT", "CPI"] if indicador == "ALL" else [indicador]

            for ind in indicadores:
                print(f"\n📊 Descargando indicador '{ind}' para {pais} ({anio_inicio}-{anio_fin})...")
                try:
                    # 🔹 Compatibilidad con extractores (AlphaVantage / WorldBank)
                    if "pais" in extractor.obtener_datos_macro.__code__.co_varnames:
                        df_i = extractor.obtener_datos_macro(ind, pais=pais, start_year=anio_inicio, end_year=anio_fin)
                    else:
                        df_i = extractor.obtener_datos_macro(ind, start_year=anio_inicio, end_year=anio_fin)

                    if not df_i.empty:
                        all_data[ind] = df_i
                        print(f"✅ {ind}: {len(df_i)} registros obtenidos.")
                    else:
                        print(f"⚠️ No se encontraron datos para {ind}.")
                except Exception as e:
                    print(f"⚠️ Error al obtener {ind}: {e}")

            if indicador == "ALL":
                continuar = False
            else:
                seguir = input("\n¿Deseas descargar otro indicador macroeconómico? [s/n]: ").strip().lower()
                if seguir == "s":
                    indicador = pedir_indicador_macro()
                else:
                    continuar = False

        if all_data:
            ruta_excel = f"outputs/macro_{pais}_{anio_inicio}-{anio_fin}.xlsx"
            exportar_a_excel(ruta_excel, all_data)
            print(f"\n📁 Datos macroeconómicos exportados correctamente a: {ruta_excel}")

            print("\nResumen general:")
            for k, v in all_data.items():
                # Detectar la columna de año o fecha de manera flexible
                posibles_columnas = ["AÑO", "TIME_PERIOD", "date", "period", "year", "DATE"]
                col_anio = next((c for c in posibles_columnas if c in v.columns), None)

                if col_anio:
                    try:
                        print(f" - {k}: {len(v)} registros ({v[col_anio].min()}–{v[col_anio].max()})")
                    except Exception:
                        print(f" - {k}: {len(v)} registros (columna temporal '{col_anio}')")
                else:
                    print(f" - {k}: {len(v)} registros (sin columna de año identificable)")

            print("\n¿Deseas volver al menú principal o salir?")
            print("1️⃣  Volver al menú principal")
            print("2️⃣  Salir")
            opcion_fin = input("Opción [1-2]: ").strip()
            if opcion_fin == "1":
                return main()
            else:
                print("\n👋 Gracias por usar el Análisis Bursátil. ¡Hasta pronto!")
                return

        else:
            print("⚠️ No se obtuvieron datos macroeconómicos.")
            return main()

    # ====================================================
    # Validación inicial
    # ====================================================
    if df.empty and tipo_datos != "3":
        print("\n⚠️ No se obtuvieron datos válidos. Ejecución finalizada.")
        return main()

    # ====================================================
    # Resultados según tipo
    # ====================================================
    if tipo_datos == "1":
        print("\n✅ Datos obtenidos correctamente. Vista previa:")
        print(df.head())

    elif tipo_datos == "2":
        print("\n✅ Datos fundamentales obtenidos correctamente.\n")
        if hasattr(extractor, "report_fundamentales"):
            reporte = extractor.report_fundamentales(df)
            print(reporte)

            os.makedirs("reports", exist_ok=True)
            with open("reports/reporte_fundamentales.md", "w", encoding="utf-8") as f:
                f.write(reporte)
            print("📝 Reporte guardado en 'reports/reporte_fundamentales.md'")
            print("\n¿Deseas volver al menú principal o salir?")
            print("1️⃣  Volver al menú principal")
            print("2️⃣  Salir")
            opcion_fin = input("Opción [1-2]: ").strip()
            if opcion_fin == "1":
                return main()
            else:
                print("\n👋 Gracias por usar el Análisis Bursátil. ¡Hasta pronto!")
                return
            

    # ====================================================
    # Limpieza avanzada (solo precios)
    # ====================================================
    if tipo_datos == "1":
        usar_limpieza = input("\n¿Desea aplicar limpieza avanzada (detección de outliers y NaNs)? [s/n]: ").lower()
        if usar_limpieza == "s":
            print("\n🧹 Aplicando limpieza avanzada de datos...")
            errores = validar_df(df, columnas_unicas=["date", "ticker"], permitir_negativos=["returns"])
            if errores:
                print(f"⚠️ Se detectaron posibles incidencias en los datos ({len(errores)} tipos).")

            df = quitar_outliers(df, columnas=["close"], metodo="percentil")
            df = rellenar_na(df, estrategia="media")
            df = sincronizar_fechas(df)  # 👈 nueva función elegante de alineación temporal
            print("✅ Limpieza avanzada completada.\n")

            # === Diagnóstico de sincronización temporal ===
            print("🔎 Verificando solapamiento temporal entre los activos...\n")

            # Mostrar rango temporal individual por ticker
            rangos = df.groupby("ticker")["date"].agg(["min", "max", "count"])
            print(rangos)

            # Calcular intersección de fechas
            fecha_inicio_comun = rangos["min"].max()
            fecha_fin_comun = rangos["max"].min()
            print(f"\n📅 Rango común entre todos los activos: {fecha_inicio_comun.date()} → {fecha_fin_comun.date()}")

            # Comprobar cuántas fechas quedan en común
            fechas_comunes = df[(df["date"] >= fecha_inicio_comun) & (df["date"] <= fecha_fin_comun)]["date"].nunique()
            print(f"📊 Nº de días comunes entre todos los activos: {fechas_comunes}\n")


    # ====================================================
    # Análisis (solo precios)
    # ====================================================
    if tipo_datos == "1":
        while True:
            print("\nSeleccione el tipo de análisis:")
            print("1️⃣  Serie individual")
            print("2️⃣  Cartera")
            print("3️⃣  Simulación Monte Carlo")
            print("4️⃣  Volver al menú principal")
            print("5️⃣  Salir")
            opcion_analisis = input("Opción [1-5]: ").strip()

            if opcion_analisis == "1":
                print("\n=== 📈 Análisis de Serie Individual ===")

                # 🔹 Aseguramos que exista la carpeta reports
                os.makedirs("reports", exist_ok=True)

                for ticker in tickers:
                    datos_ticker = df[df["ticker"] == ticker].copy()
                    serie = SeriePrecios(ticker, datos_ticker)
                    reporte = serie.report()

                    print(reporte)

                    # Guardar el reporte individual en Markdown
                    ruta_reporte = f"reports/reporte_{ticker}.md"
                    with open(ruta_reporte, "w", encoding="utf-8") as f:
                        f.write(reporte)
                    print(f"📝 Reporte guardado en: {ruta_reporte}")

            elif opcion_analisis == "2":
                print("\n=== 💼 Análisis de Cartera ===")

                # 1️⃣ Composición de la cartera
                cartera = Cartera(nombre="Cartera MIAX")
                for ticker in tickers:
                    datos_ticker = df[df["ticker"] == ticker].copy()
                    serie = SeriePrecios(ticker, datos_ticker)
                    cartera.agregar_serie(serie)
                    print(f"➕ Añadido {ticker} a la cartera ({len(datos_ticker)} observaciones).")

                print("\n✅ Cartera compuesta correctamente con los siguientes activos:")
                for t, w in cartera.pesos.items():
                    print(f"   - {t}: {w*100:.2f}%")

                # 2️⃣ Reporte ejecutivo
                print("\n📊 Calculando métricas globales...\n")
                reporte_cartera = cartera.report()
                print(reporte_cartera)

                # Guardar reporte en archivo markdown
                os.makedirs("reports", exist_ok=True)
                with open("reports/reporte_Mi_Cartera.md", "w", encoding="utf-8") as f:
                    f.write(reporte_cartera)
                print("📝 Reporte guardado en 'reports/reporte_Mi_Cartera.md'")

                # 3️⃣ Simulación Monte Carlo de la cartera
                print("\n🎲 Ejecutando simulación Monte Carlo de la cartera completa...\n")
                num_days = input("Nº de días (default 252): ").strip()
                num_sim = input("Nº de simulaciones (default 500): ").strip()
                num_days = int(num_days) if num_days else 252
                num_sim = int(num_sim) if num_sim else 500

                try:
                    sim_cartera = cartera.simulate_montecarlo(num_days=num_days, num_simulations=num_sim)
                    resumen_sim = sim_cartera.describe().T[["mean", "std", "min", "50%", "max"]]
                    print("\n📈 Resumen de la simulación de la cartera:")
                    print(resumen_sim.head())

                    # Gráfico de la simulación
                    print("\n🖼️ Generando gráfico de simulación de cartera...")
                    cartera.plot_last_portfolio_simulation()

                    # 4️⃣ Exportar resultados a Excel
                    ruta_excel = f"outputs/analisis_cartera_{'_'.join(tickers)}_{fecha_inicio[:4]}.xlsx"
                    datos_para_exportar = {
                        "Datos Crudos": df,
                        "Series Individuales": "\n".join(
                            [SeriePrecios(t, df[df['ticker'] == t]).report() for t in tickers]
                        ),
                        "Cartera": reporte_cartera,
                        "Simulación Monte Carlo": resumen_sim
                    }
                    exportar_a_excel(ruta_excel, datos_para_exportar, imagenes=["simulaciones.png"])
                    print(f"\n📁 Resultados exportados correctamente a: {ruta_excel}\n")

                except Exception as e:
                    print(f"⚠️ Error durante la simulación de la cartera: {e}")


            elif opcion_analisis == "3":
                print("\n=== 🎲 Simulación Monte Carlo Individual por Activo ===")

                num_days = input("Nº de días (default 252): ").strip()
                num_sim = input("Nº de simulaciones (default 500): ").strip()
                num_days = int(num_days) if num_days else 252
                num_sim = int(num_sim) if num_sim else 500

                resultados_simulaciones = {}
                print("\n🚀 Ejecutando simulaciones Monte Carlo...\n")

                for ticker in tickers:
                    print(f"📈 Simulando {ticker}...")

                    datos_ticker = df[df["ticker"] == ticker].copy()
                    serie = SeriePrecios(ticker, datos_ticker)

                    try:
                        sim = serie.simulate_montecarlo(
                            num_days=num_days,
                            num_simulations=num_sim,
                            use_historical_params=True
                        )

                        # Guardamos la simulación en el dict
                        resultados_simulaciones[ticker] = sim

                        # Guardamos el gráfico individual
                        grafico_path = f"outputs/Simulacion_MonteCarlo_{ticker}.png"
                        serie.plot_last_simulation(
                            n_plot=50,
                            title=f"Simulación de Montecarlo - {ticker}",
                            savepath=grafico_path
                        )

                        # Mostramos resumen por consola
                        print(f"\n📊 Resumen de la simulación de {ticker}:")
                        print(sim.head())
                        print(f"🖼️ Gráfico guardado en: {grafico_path}\n")

                    except Exception as e:
                        print(f"⚠️ Error en la simulación de {ticker}: {e}\n")

                # Exportar todas las simulaciones a un solo Excel
                if resultados_simulaciones:
                    ruta_excel = f"outputs/simulaciones_individuales_{'_'.join(tickers)}.xlsx"

                    hojas_export = {}
                    for ticker, sim_df in resultados_simulaciones.items():
                        hojas_export[f"Sim_{ticker}"] = sim_df

                    # Construimos lista de imágenes generadas
                    imagenes_paths = [f"outputs/Simulacion_MonteCarlo_{t}.png" for t in tickers if os.path.exists(f"outputs/Simulacion_MonteCarlo_{t}.png")]

                    # Exportamos simulaciones con gráficos incrustados
                    exportar_a_excel(ruta_excel, hojas_export, imagenes=imagenes_paths)
                    print(f"\n📁 Todas las simulaciones exportadas a: {ruta_excel} (con gráficos individuales)")

                else:
                    print("⚠️ No se generaron simulaciones válidas.")

            elif opcion_analisis == "4":
                print("\n↩️ Volviendo al menú principal...\n")
                break  # rompe el while y sale del menú de análisis

            elif opcion_analisis == "5":
                print("\n👋 Gracias por usar el Análisis Bursátil. ¡Hasta pronto!")
                return
            
    return main()

if __name__ == "__main__":
    main()





