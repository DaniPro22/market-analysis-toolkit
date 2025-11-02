from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from src.simulations.montecarlo import montecarlo_simulation, plot_simulations


@dataclass
class SeriePrecios:
    ticker: str
    datos: pd.DataFrame = field(default_factory=pd.DataFrame)
    media: float = field(init=False)
    desviacion: float = field(init=False)
    returns: pd.Series = field(init=False)
    volatility: float = field(init=False)
    cumulative_return: pd.Series = field(init=False)
    sharpe_ratio: float = field(init=False, default=np.nan)
    risk_free_rate = 0.0  # tasa libre de riesgo anual

    def __post_init__(self):
        """Se ejecuta automáticamente tras crear la instancia."""
        if not self.datos.empty:
            # --- Asegurar orden temporal ---
            self.datos = self.datos.sort_values('date')

            # --- Cálculo de métricas básicas ---
            self.media = self.datos['close'].mean()
            self.desviacion = self.datos['close'].std()

            # --- Calcular retornos y derivados ---
            self.compute_returns()
            self.compute_volatility()
            self.compute_cumulative_return()
            self.sharpe_ratio = self.sharpe_calculation()
        else:
            # Si no hay datos, dejamos las métricas como NaN
            self.media = np.nan
            self.desviacion = np.nan
            self.returns = pd.Series(dtype=float)
            self.volatility = np.nan
            self.cumulative_return = pd.Series(dtype=float)
            self.sharpe_ratio = np.nan

    # ==========================================================
    # Métodos de cálculo
    # ==========================================================
    def compute_returns(self):
        """Calcula los retornos logarítmicos diarios."""
        self.returns = np.log(self.datos['close'] / self.datos['close'].shift(1)).replace([np.inf, -np.inf], np.nan)
        self.datos['returns'] = self.returns

    def compute_volatility(self):
        """Calcula la volatilidad anualizada de los retornos."""
        self.volatility = self.returns.std() * np.sqrt(252)

    def compute_cumulative_return(self):
        """Calcula el rendimiento acumulado."""
        self.cumulative_return = (1 + self.returns.fillna(0)).cumprod() - 1
        self.datos['cumulative_return'] = self.cumulative_return

    def sharpe_calculation(self, risk_free_rate: float = None) -> float:
        """
        Calcula el ratio de Sharpe anualizado.

        Sharpe anualizado = (retorno promedio diario - tasa libre de riesgo diaria) / desviación diaria * sqrt(252)

        Parámetros
        ----------
        risk_free_rate : float, opcional
            Tasa libre de riesgo anual (por defecto usa self.risk_free_rate si está definida).

        Retorna
        -------
        float
            Ratio de Sharpe anualizado.
        """
        if self.datos.empty or self.returns.empty:
            return np.nan

        # Usa la tasa libre de riesgo definida o la pasada como argumento
        rf_annual = risk_free_rate if risk_free_rate is not None else self.risk_free_rate
        rf_daily = rf_annual / 252  # convertir a tasa diaria

        mean_return = self.returns.mean()
        std_return = self.returns.std()

        if std_return == 0 or np.isnan(std_return):
            return np.nan

        sharpe_daily = (mean_return - rf_daily) / std_return
        sharpe_annualized = sharpe_daily * np.sqrt(252)

        return sharpe_annualized

    # ==========================================================
    # Simulación Monte Carlo
    # ==========================================================
    def simulate_montecarlo(self,
                            num_days: int = 252,
                            num_simulations: int = 1000,
                            use_historical_params: bool = True,
                            mu: float = None,
                            sigma: float = None,
                            dt: float = 1 / 252,
                            random_seed: int = None,
                            method: str = "gbm"):
        """
        Simula num_simulations trayectorias para esta serie.

        - Si use_historical_params=True, calcula mu y sigma a partir de los returns logarítmicos diarios.
        - En otro caso usa mu y sigma pasados por argumento (deben ser diarios).
        Retorna DataFrame de shape (num_days, num_simulations).
        """
        if self.datos.empty:
            raise ValueError("No hay datos en esta SeriePrecios para simular.")

        initial_price = float(self.datos['close'].iloc[-1])

        if use_historical_params:
            mu_hist = self.returns.mean()
            sigma_hist = self.returns.std()
            mu = mu_hist if mu is None else mu
            sigma = sigma_hist if sigma is None else sigma
        else:
            if mu is None or sigma is None:
                raise ValueError("Si use_historical_params=False, pasa mu y sigma.")

        if np.isnan(mu) or np.isnan(sigma):
            raise ValueError("Mu o sigma no contienen valores válidos (NaN). Revisa la serie.")

        self.last_initial_price = initial_price

        sim_df = montecarlo_simulation(
            initial_price=initial_price,
            mu=float(mu),
            sigma=float(sigma),
            num_days=num_days,
            num_simulations=num_simulations,
            dt=dt,
            random_seed=random_seed,
            method=method
        )

        self._last_simulation = sim_df
        return sim_df

    def plot_last_simulation(self, n_plot: int = 50, title: str = None, savepath: str = None):
        """Plotea la última simulación guardada."""
        if not hasattr(self, "_last_simulation"):
            raise ValueError("No hay simulación guardada. Llama a simulate_montecarlo() primero.")
        if title is None:
            title = f"{self.ticker} - Monte Carlo"
        plot_simulations(self._last_simulation, n_plot=n_plot, title=title, savepath=savepath)

    # ==========================================================
    # Resumen y reporte
    # ==========================================================
    def resumen(self):
        """Devuelve un resumen básico de la serie de precios."""
        return {
            "ticker": self.ticker,
            "media_close": round(self.media, 4),
            "desviacion_close": round(self.desviacion, 4),
            "volatilidad_anualizada": round(self.volatility, 4),
            "sharpe_ratio": round(self.sharpe_ratio, 4),
            "rendimiento_total": round(self.cumulative_return.iloc[-1], 4)
            if not self.datos.empty else np.nan,
            "n_datos": len(self.datos)
        }

    def report(self):
        """Devuelve un reporte en formato Markdown."""
        if self.datos.empty:
            return f"⚠️ No hay datos disponibles para {self.ticker}\n"

        return (
            f"### 📊 Reporte de {self.ticker}\n"
            f"- Media close: {self.media:.2f}\n"
            f"- Desviación típica close: {self.desviacion:.2f}\n"
            f"- Volatilidad anualizada: {self.volatility:.2%}\n"
            f"- Retorno total: {self.cumulative_return.iloc[-1]:.2%}\n"
            f"- Sharpe Ratio: {self.sharpe_ratio:.2f}\n"
            f"- Nº de datos: {len(self.datos)}\n"
        )

