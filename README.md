# Market Analysis Toolkit

Proyecto del Bloque 1 del Máster en Inteligencia Artificial y Computación Cuántica Aplicada a los Mercados Financieros (BME).

## 🚀 Descripción
Conjunto de herramientas para la extracción, estandarización y análisis de información bursátil.  
El objetivo es aplicar buenas prácticas de programación orientada a objetos, modularidad y simulaciones estadísticas.

## 🧩 Estructura
/src
    /extractors      → APIs para obtener datos bursátiles
    /models          → Clases y dataclasses (series, carteras)
    /utils           → Limpieza y validación de datos
    /simulations     → Monte Carlo y simulaciones estadísticas
    /visualizations  → Gráficos y reportes
/tests               → Pruebas unitarias
/docs                → Documentación y diagramas

## 🧰 Instalación
```bash
git clone https://github.com/DaniPro22/market-analysis-toolkit.git
cd market-analysis-toolkit
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
