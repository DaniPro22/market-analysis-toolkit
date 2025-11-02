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
