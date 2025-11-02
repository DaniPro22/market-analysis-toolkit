# src/utils/data_cleaning.py
import pandas as pd

def limpiar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Función básica de limpieza y preprocesado para el DF estandarizado."""
    if df.empty:
        return df

    # 1. Asegurar tipos
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    # 2. Eliminar duplicados (por 'date' y 'ticker' si existen)
    subset_cols = [c for c in ['date', 'ticker'] if c in df.columns]
    if subset_cols:
        df = df.drop_duplicates(subset=subset_cols, keep='first')

    # 3. Rellenar/manejar NaNs
    if 'close' in df.columns:
        df.dropna(subset=['close'], inplace=True)

    # 4. Forzar numéricos en columnas conocidas
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df
