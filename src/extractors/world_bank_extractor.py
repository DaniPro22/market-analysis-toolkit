import pandas as pd
import wbgapi as wb


class ExtractorWorldBank:
    """
    Extractor de datos macroeconómicos desde la API del Banco Mundial (World Bank).
    Permite obtener indicadores como PIB, Inflación y Desempleo
    filtrando por país y rango de años.
    """

    def __init__(self):
        # Mapeo de tus indicadores a los códigos del Banco Mundial
        self.indicador_map = {
            "GDP": "NY.GDP.MKTP.KD.ZG",        # Crecimiento del PIB (% anual)
            "INFLATION": "FP.CPI.TOTL.ZG",     # Inflación (IPC, % anual)
            "CPI": "FP.CPI.TOTL.ZG",           # Igual que inflación general
            "UNEMPLOYMENT": "SL.UEM.TOTL.ZS"   # Tasa de desempleo total (%)
        }

    # =========================================================
    # MÉTODO PRINCIPAL
    # =========================================================
    def obtener_datos_macro(
        self,
        indicador: str,
        pais: str = "USA",
        start_year: int = 2010,
        end_year: int = 2025
    ) -> pd.DataFrame:
        """
        Descarga datos macroeconómicos anuales desde el Banco Mundial
        filtrando por código de país (ISO 3) y rango de años.
        """

        indicador_key = indicador.upper()

        if indicador_key not in self.indicador_map:
            raise ValueError(
                f"Indicador '{indicador_key}' no soportado. Usa: {', '.join(self.indicador_map.keys())}."
            )

        indicador_code = self.indicador_map[indicador_key]

        # Validamos código de país
        pais = pais.upper()
        if len(pais) != 3:
            print(f"⚠️ Aviso: El Banco Mundial usa códigos ISO-3 (ej. ESP). Usando '{pais}' igualmente.")

        print(f"🔗 Conectando con el Banco Mundial ({indicador_key}, código: {indicador_code})...")

        try:
            df_data = wb.data.fetch(
                indicador_code,
                pais,
                time=range(start_year, end_year + 1),
                skipBlanks=True,
                numericTimeKeys=True,
            )
            if not df_data:
                print(f"⚠️ No se encontraron datos para {indicador_key} ({pais})")
                return pd.DataFrame()

            df = pd.DataFrame(df_data)

        except Exception as e:
            print(f"⚠️ Error al descargar datos de {indicador_key}: {e}")
            return pd.DataFrame()

        # =========================================================
        # Normalización
        # =========================================================
        df = df.rename(
            columns={
                "value": "VALOR",
                "time": "AÑO",
                "economy": "PAIS_CODE",
                "series": "SERIES_CODE",
            }
        )

        df["PAIS"] = pais
        df["INDICADOR"] = indicador_key
        df["FUENTE"] = "WORLD_BANK"

        # Limpieza del campo AÑO
        df["AÑO"] = pd.to_numeric(df["AÑO"], errors="coerce").astype("Int64")

        columnas_principales = [
            "PAIS",
            "AÑO",
            "VALOR",
            "INDICADOR",
            "FUENTE",
            "PAIS_CODE",
            "SERIES_CODE",
        ]
        df = df[[c for c in columnas_principales if c in df.columns]].reset_index(drop=True)
        df = df.sort_values("AÑO")

        print(f"✅ Datos World Bank - {indicador_key}: {len(df)} registros para {pais} ({start_year}-{end_year})")
        return df

    # =========================================================
    # REPORTE RESUMIDO
    # =========================================================
    def generar_reporte(self, data: pd.DataFrame) -> str:
        """Genera un resumen en formato texto de los indicadores obtenidos."""
        if data.empty:
            return "⚠️ No se encontraron datos para generar el reporte."

        lines = ["## 🌐 Reporte Macroeconómico - World Bank\n"]
        for indicador in data["INDICADOR"].unique():
            subset = data[data["INDICADOR"] == indicador]
            pais = subset["PAIS"].iloc[0] if "PAIS" in subset.columns else "N/A"
            start = subset["AÑO"].min()
            end = subset["AÑO"].max()
            valor_medio = subset["VALOR"].mean()
            lines.append(
                f"**{indicador} ({pais}, {start}-{end})** → Valor medio: {valor_medio:.2f}"
            )

        return "\n".join(lines)

