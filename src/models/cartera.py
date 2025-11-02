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
        if peso is not None:
            self.pesos[serie.ticker] = peso
        else:
            n = len(self.series)
            self.pesos = {s.ticker: 1 / n for s in self.series}

    # ==========================================================
    # Cálculos de rentabilidad y riesgo
    # ==========================================================
    def calcular_retornos(self):
        """Concatena los retornos de todas las series en un único DataFrame."""
        if not self.series:
            raise ValueError("No hay series en la cartera.")
        df_rets = pd.concat(
            [s.returns.rename(s.ticker) for s in self.series if not s.returns.empty],
            axis=1
        ).dropna()
        return df_rets

    def calcular_metricas_globales(self):
        """Calcula retorno, volatilidad, Sharpe, VaR y CVaR de la cartera."""
        df_rets = self.calcular_retornos()
        tickers = df_rets.columns
        pesos = np.array([self.pesos.get(t, 1 / len(tickers)) for t in tickers])
        pesos = pesos / pesos.sum()

        mean_returns = df_rets.mean().values
        cov_matrix = df_rets.cov().values

        # Retorno y volatilidad anualizados
        ret_anual = np.dot(pesos, mean_returns) * 252
        vol_anual = np.sqrt(np.dot(pesos.T, np.dot(cov_matrix * 252, pesos)))

        sharpe = (ret_anual - self.risk_free_rate) / vol_anual if vol_anual > 0 else np.nan
        var_95 = self.calcular_var(df_rets, pesos, alpha=0.05)
        cvar_95 = self.calcular_cvar(df_rets, pesos, alpha=0.05)

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

    def calcular_diversificacion(self):
        """Evalúa el grado de diversificación mediante correlación media."""
        df_rets = self.calcular_retornos()
        corr = df_rets.corr()
        corr_mean = corr.where(~np.eye(corr.shape[0], dtype=bool)).mean().mean()
        return corr_mean

    def calcular_correlaciones(self):
        """Devuelve la matriz de correlación entre activos."""
        return self.calcular_retornos().corr()

    # ==========================================================
    # Reporte legible y ejecutivo
    # ==========================================================
    def report(self):
        """Genera un reporte ejecutivo de la cartera."""
        if not self.series:
            return f"⚠️ La cartera '{self.nombre}' no contiene activos.\n"

        metrics = self.calcular_metricas_globales()
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



