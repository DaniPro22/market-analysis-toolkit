📈 MIAX Market Data Toolkit

Análisis Bursátil – Proyecto final (IA y Computación Cuántica BME)
Desarrollado por Daniel Gallego Sánchez

====================================================
🎯 Objetivo

Crear un conjunto de herramientas modulares para la obtención y análisis de información bursátil, capaz de conectarse a múltiples APIs, estandarizar los datos y ofrecer simulaciones financieras como Monte Carlo, reportes automáticos y limpieza avanzada de datos.

🧩 Estructura general
src/
├── extractors/     → conexión con APIs (Yahoo, Alpha Vantage, Twelve Data, World Bank)
├── models/         → DataClasses: SeriePrecios y Cartera
├── simulations/    → módulo de simulaciones Monte Carlo
├── utils/          → limpieza, validación y exportación de datos
main.py             → programa principal (CLI interactivo)

====================================================
⚙️ Instalación
git clone https://github.com/tuusuario/MIAX-Market-Toolkit.git
cd MIAX-Market-Toolkit
pip install -r requirements.txt
====================================================

🚀 Ejecución
python main.py

El programa abrirá un menú interactivo donde podrás elegir:

1️⃣ Descargar precios históricos
2️⃣ Obtener datos fundamentales
3️⃣ Extraer indicadores macroeconómicos
4️⃣ Analizar carteras y simulaciones

====================================================

🧠 Estandarización de datos

Independientemente de la API utilizada, el formato de salida sigue siempre la misma estructura:

date	open	high	low	close	volume	ticker

Esto permite reutilizar el mismo análisis y visualización sin cambios de código.
====================================================

🧮 Principales clases

SeriePrecios

Representa una serie temporal de precios.

Calcula automáticamente: media, desviación, retornos, volatilidad y Sharpe Ratio.

Métodos:

.simulate_montecarlo()

.plot_last_simulation()

.report()

Cartera

Agrupa múltiples SeriePrecios y calcula métricas globales:

Retorno y volatilidad anualizados

Sharpe Ratio

VaR / CVaR

Correlación media entre activos

.simulate_montecarlo() y .plot_last_portfolio_simulation()

🎲 Simulación Monte Carlo

Implementación basada en el Geometric Brownian Motion (GBM)

Permite ajustar:

Días simulados (num_days)

Número de trayectorias (num_simulations)

Semilla aleatoria (random_seed)

Resultados:

Gráficos individuales y de cartera

Exportación automática a Excel con imágenes embebidas

====================================================

🧹 Limpieza y preprocesado

Incluye funciones en utils/data_tools.py:

quitar_outliers() (Z-score o percentil)

rellenar_na() (media, mediana o constante)

validar_df() (duplicados y negativos)

homogeneizar_fechas()

====================================================

📑 Reportes y exportación

El programa genera:

Reportes .md automáticos (serie y cartera)

Archivos .xlsx con múltiples hojas y gráficos integrados

Carpeta /reports y /outputs organizadas automáticamente

====================================================


