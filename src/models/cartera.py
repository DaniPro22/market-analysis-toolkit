# src/models/cartera.py

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from src.models.series_precios import SeriePrecios


@dataclass
class Cartera:
    nombre: str
    series: list = field(default_factory=list)
    pesos: dict = field(default_factory=dict)
    risk_free_rate: float = 0.02  # 2% anual por defecto

    # ==========================================================
    # Gestión de series
    # ==========================================================
    def agregar_serie(self, serie: SeriePrecios, peso: float = None):
        """Agrega una SeriePrecios a la cartera."""
        self.series.append(serie)

        # Si no se especifica peso, se actualizan automáticamente por volatilidad inversa
        if peso is not None:
            self.pesos[serie.ticker] = peso
        else:
            self.ajustar_pesos_por_volatilidad()

    def ajustar_pesos_por_volatilidad(self):
        """Calcula pesos proporcionales a la volatilidad inversa de cada activo."""
        if not self.series:
            return

        vols = {}
        for s in self.series:
            try:
                # Calcular la volatilidad de cada activo a partir de su columna 'close'
                df_rets = s.datos["close"].pct_change().dropna()
                vols[s.ticker] = df_rets.std() if not df_rets.empty else np.nan
            except Exception as e:
                print(f"⚠️ No se pudo calcular la volatilidad de {s.ticker}: {e}")
                vols[s.ticker] = np.nan

        # Si alguna volatilidad es NaN o cero → pesos iguales
        if any(v is None or np.isnan(v) or v == 0 for v in vols.values()):
            n = len(self.series)
            self.pesos = {s.ticker: 1 / n for s in self.series}
        else:
            inv_vols = {t: 1 / v for t, v in vols.items()}
            total = sum(inv_vols.values())
            self.pesos = {t: w / total for t, w in inv_vols.items()}


    # ==========================================================
    # Cálculos de rentabilidad y riesgo
    # ==========================================================
    def calcular_retornos(self, metodo_union: str = "inner") -> pd.DataFrame:
        """
        Concatena los retornos de todas las series en un único DataFrame.
        Alinea temporalmente los datos y evita huecos.
        """
        if not self.series:
            raise ValueError("No hay series en la cartera.")

        dfs = []
        for s in self.series:
            if not s.returns.empty:
                dfs.append(s.returns.rename(s.ticker))

        if not dfs:
            print("⚠️ No hay retornos válidos en las series.")
            return pd.DataFrame()

        # 🔹 Alineación temporal estricta (solo fechas comunes)
        df_rets = pd.concat(dfs, axis=1, join=metodo_union).dropna()
        df_rets = df_rets.sort_index()

        return df_rets

    def calcular_metricas_globales(self) -> dict:
        """Calcula retorno, volatilidad, Sharpe, VaR y CVaR de la cartera."""
        df_rets = self.calcular_retornos()

        if df_rets.empty:
            print("⚠️ No hay datos coincidentes entre las series para calcular métricas.")
            return {
                "ret_anualizado": np.nan,
                "vol_anualizada": np.nan,
                "sharpe": np.nan,
                "var_95": np.nan,
                "cvar_95": np.nan,
                "pesos": {}
            }

        tickers = df_rets.columns
        pesos = np.array([self.pesos.get(t, 1 / len(tickers)) for t in tickers])
        pesos = pesos / pesos.sum()

        mean_returns = df_rets.mean().values
        cov_matrix = df_rets.cov().values
        
        ret_anual = np.dot(pesos, mean_returns) * 252
        vol_anual = np.sqrt(np.dot(pesos.T, np.dot(cov_matrix * 252, pesos)))

        sharpe = (ret_anual - self.risk_free_rate) / vol_anual if vol_anual > 0 else np.nan

        try:
            var_95 = self.calcular_var(df_rets, pesos, alpha=0.05)
            cvar_95 = self.calcular_cvar(df_rets, pesos, alpha=0.05)
        except Exception:
            var_95, cvar_95 = np.nan, np.nan

        return {
            "ret_anualizado": ret_anual,
            "vol_anualizada": vol_anual,
            "sharpe": sharpe,
            "var_95": var_95,
            "cvar_95": cvar_95,
            "pesos": dict(zip(tickers, pesos))
        }

    def calcular_var(self, df_rets, pesos, alpha=0.05):
        """Calcula VaR histórico de la cartera (por defecto al 95%)."""
        port_rets = df_rets.dot(pesos)
        return np.quantile(port_rets, alpha) * 100

    def calcular_cvar(self, df_rets, pesos, alpha=0.05):
        """Calcula CVaR (Expected Shortfall) al nivel alpha."""
        port_rets = df_rets.dot(pesos)
        var = np.quantile(port_rets, alpha)
        cvar = port_rets[port_rets <= var].mean() * 100
        return cvar

    # ==========================================================
    # Diversificación y correlaciones
    # ==========================================================
    def calcular_diversificacion(self):
        """Evalúa el grado de diversificación mediante correlación media."""
        df_rets = self.calcular_retornos()
        if df_rets.empty or len(df_rets.columns) < 2:
            return np.nan

        corr = df_rets.corr()
        # Excluye la diagonal para evitar autocorrelaciones
        corr_mean = corr.where(~np.eye(corr.shape[0], dtype=bool)).mean().mean()
        return corr_mean

    def calcular_correlaciones(self):
        """Devuelve la matriz de correlación entre activos."""
        df_rets = self.calcular_retornos()
        return df_rets.corr()

    # ==========================================================
    # Reporte legible y ejecutivo
    # ==========================================================
    def report(self) -> str:
        """
        Genera un reporte ejecutivo de la cartera con control de errores.
        """
        if not self.series:
            return f"⚠️ La cartera '{self.nombre}' no contiene activos.\n"

        metrics = self.calcular_metricas_globales()

        if not metrics["pesos"]:
            return (
                f"⚠️ No se pudieron calcular métricas para la cartera '{self.nombre}'.\n"
                f"Revisa los tickers o el rango temporal.\n"
            )

        corr_mean = self.calcular_diversificacion()

        lines = [
            f"## 💼 Reporte Ejecutivo - Cartera: {self.nombre}",
            "",
            f"**📊 Métricas Globales:**",
            f"- Retorno anualizado: {metrics['ret_anualizado']*100:.2f}%",
            f"- Volatilidad anualizada: {metrics['vol_anualizada']*100:.2f}%",
            f"- Sharpe Ratio: {metrics['sharpe']:.2f}",
            f"- VaR (95%): {metrics['var_95']:.2f}%",
            f"- CVaR (95%): {metrics['cvar_95']:.2f}%",
            "",
            f"**⚖️ Composición de la cartera:**"
        ]

        for t, w in metrics["pesos"].items():
            lines.append(f"- {t}: {w*100:.2f}%")

        lines += [
            "",
            f"**🔗 Diversificación:**",
            f"- Correlación media entre activos: {corr_mean:.2f}",
            f"- Número de activos: {len(self.series)}",
            "",
            f"---",
            f"📈 *Análisis agregado sobre {len(self.calcular_retornos())} observaciones de precios.*",
            ""
        ]

        return "\n".join(lines)

    # ==========================================================
    # Simulación Monte Carlo
    # ==========================================================
    def simulate_montecarlo(self, num_days=252, num_simulations=500):
        """Simula la evolución de la cartera a futuro mediante Monte Carlo (GBM)."""
        df_rets = self.calcular_retornos()
        tickers = df_rets.columns
        pesos = np.array([self.pesos.get(t, 1 / len(tickers)) for t in tickers])
        pesos = pesos / pesos.sum()

        mean_returns = df_rets.mean().values
        cov_matrix = df_rets.cov().values
        precios_ini = [float(s.datos["close"].iloc[-1]) for s in self.series]

        sim_paths = np.zeros((num_days, num_simulations))
        port_returns = np.dot(mean_returns, pesos)
        port_vol = np.sqrt(np.dot(pesos.T, np.dot(cov_matrix, pesos)))

        for i in range(num_simulations):
            prices = [np.dot(precios_ini, pesos)]
            for _ in range(1, num_days):
                rand = np.random.normal(0, 1)
                price = prices[-1] * np.exp((port_returns - 0.5 * port_vol ** 2) + port_vol * rand)
                prices.append(price)
            sim_paths[:, i] = prices

        sim_df = pd.DataFrame(sim_paths)
        self._last_simulation = sim_df
        return sim_df

    def plot_last_portfolio_simulation(self, n_plot=50):
        """Plotea las simulaciones si existen."""
        if not hasattr(self, "_last_simulation"):
            raise ValueError("No hay simulación guardada.")

        import matplotlib.pyplot as plt
        sim_df = self._last_simulation
        sim_df.iloc[:, :n_plot].plot(legend=False, alpha=0.6)
        plt.title(f"Simulación Monte Carlo - {self.nombre}")
        plt.xlabel("Días")
        plt.ylabel("Valor simulado")
        plt.tight_layout()
        plt.savefig("simulaciones.png")
        plt.show()



