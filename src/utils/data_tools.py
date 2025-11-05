import pandas as pd
import numpy as np

# FUNCION DE LIMPIEZA 1

def rellenar_na(df: pd.DataFrame, estrategia: str = 'media', columnas: list = None, valor=None):
    """
    Rellena los valores faltantes según la estrategia.
    """
    columnas = columnas or df.columns
    for col in columnas:
        if estrategia == 'media' and pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].mean())

        elif estrategia == 'mediana' and pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].median())
        elif estrategia == 'constante':
            df[col] = df[col].fillna(valor)
    return df



# FUNCION DE LIMPIEZA 2

def quitar_outliers(df: pd.DataFrame, columnas: list, metodo='zscore', umbral=3):
    """
    Elimina outliers de las columnas numéricas.
    """
    if metodo == 'zscore':
        from scipy.stats import zscore
        for col in columnas:
            if pd.api.types.is_numeric_dtype(df[col]):
                df = df[(np.abs(zscore(df[col])) < umbral)]
    elif metodo == 'percentil':
        for col in columnas:
            if pd.api.types.is_numeric_dtype(df[col]):
                q_low = df[col].quantile(0.01)
                q_high = df[col].quantile(0.99)
                df = df[(df[col] >= q_low) & (df[col] <= q_high)]
    return df


# FUNCION DE LIMPIEZA 3

def homogeneizar_fechas(df: pd.DataFrame, columnas: list, formato: str = None):
    """
    Convierte columnas a datetime.
    """
    for col in columnas:
        df[col] = pd.to_datetime(df[col], format=formato, errors='coerce')
    return df


# FUNCION DE LIMPIEZA 4

def validar_df(df: pd.DataFrame, columnas_unicas: list = None, permitir_negativos: list = None):
    """
    Realiza validaciones básicas.
    """
    errores = {}
    permitir_negativos = permitir_negativos or []
    
    # Duplicados generales
    dup = df.duplicated()
    if dup.any():
        errores['duplicados'] = df[dup]
    
    # Negativos no permitidos
    for col in df.select_dtypes(include=[np.number]).columns:
        if col not in permitir_negativos:
            if (df[col] < 0).any():
                errores[f'negativos_en_{col}'] = df[df[col] < 0]
    
    # Columnas únicas (solo si existen)
    if columnas_unicas:
        for col in columnas_unicas:
            if col in df.columns:
                if df[col].duplicated().any():
                    errores[f'duplicados_en_{col}'] = df[df[col].duplicated(keep=False)]
    
    return errores



# FUNCION DE LIMPIEZA 5


def sincronizar_fechas(df: pd.DataFrame, columna_fecha: str = "date", columna_ticker: str = "ticker") -> pd.DataFrame:
    """
    Sincroniza el rango temporal entre todos los activos (tickers) de un DataFrame.
    Mantiene solo las fechas comunes a todos los tickers.

    Parámetros:
        df: DataFrame con columnas 'ticker' y 'date'
        columna_fecha: nombre de la columna de fechas
        columna_ticker: nombre de la columna de tickers

    Retorna:
        DataFrame filtrado con el rango temporal común.
    """
    if df.empty:
        print("⚠️ DataFrame vacío, no se puede sincronizar.")
        return df

    try:
        print("📅 Sincronizando fechas entre los activos...")

        fechas_por_ticker = df.groupby(columna_ticker)[columna_fecha].agg(["min", "max"])
        fecha_inicio_comun = fechas_por_ticker["min"].max()
        fecha_fin_comun = fechas_por_ticker["max"].min()

        # Filtrar solo el rango común
        df_filtrado = df[
            (df[columna_fecha] >= fecha_inicio_comun) &
            (df[columna_fecha] <= fecha_fin_comun)
        ].copy()

        n_descartadas = len(df) - len(df_filtrado)
        if n_descartadas > 0:
            print(f"⚠️ Se eliminaron {n_descartadas} registros fuera del rango común "
                  f"({fecha_inicio_comun.date()}–{fecha_fin_comun.date()}).")

        print("✅ Fechas sincronizadas correctamente.\n")
        return df_filtrado.reset_index(drop=True)

    except Exception as e:
        print(f"⚠️ Error al sincronizar fechas: {e}")
        return df
