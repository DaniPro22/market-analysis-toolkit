# src/simulations/montecarlo.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def montecarlo_simulation(
    initial_price: float,
    mu: float,
    sigma: float,
    num_days: int = 252,
    num_simulations: int = 1000,
    dt: float = 1/252,
    random_seed: int = None,
    method: str = "gbm"
) -> pd.DataFrame:
    """
    Simula trayectorias de precio.

    Parámetros:
    - initial_price: precio inicial (float)
    - mu: rendimiento medio diario (drift) - usar media de returns (no anualizada)
    - sigma: desviación típica diaria (volatilidad) (no anualizada)
    - num_days: número de pasos/días a simular
    - num_simulations: número de simulaciones (columnas)
    - dt: paso temporal (por defecto 1/252)
    - random_seed: semilla aleatoria (opcional)
    - method: "gbm" (por defecto) o "additive" (multiplicativo simple)

    Retorna:
    - DataFrame de shape (num_days, num_simulations), cada columna es una simulación.
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    # Prealocar array
    sims = np.zeros((num_days, num_simulations), dtype=float)

    if method == "gbm":
        # Geometric Brownian Motion discretizado:
        # S_{t+dt} = S_t * exp((mu - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z)
        drift = (mu - 0.5 * sigma**2) * dt
        diffusion_scale = sigma * np.sqrt(dt)
        for sim in range(num_simulations):
            prices = np.empty(num_days)
            prices[0] = initial_price
            # genera todo el vector de normales de golpe para velocidad
            z = np.random.normal(size=num_days-1)
            prices[1:] = initial_price * np.exp(
                np.cumsum(drift + diffusion_scale * z)
            )
            sims[:, sim] = prices
    else:
        # método multiplicativo sencillo (uso anterior): price_next = price*(1 + shock)
        for sim in range(num_simulations):
            prices = [initial_price]
            for _ in range(1, num_days):
                shock = np.random.normal(loc=mu, scale=sigma)
                prices.append(prices[-1] * (1 + shock))
            sims[:, sim] = prices

    # DataFrame con índice 0..num_days-1
    df = pd.DataFrame(sims)
    df.index.name = "day"
    return df

def plot_simulations(sim_df: pd.DataFrame, n_plot: int = 50, title: str = "Monte Carlo simulations", figsize=(10,5), savepath: str = None):
    """
    Dibuja las simulaciones (subset de n_plot) y un histograma del valor final.
    """
    plt.figure(figsize=figsize)
    # plot subset of columns
    n_plot = min(n_plot, sim_df.shape[1])
    for c in sim_df.columns[:n_plot]:
        plt.plot(sim_df.index, sim_df[c], alpha=0.08)
    plt.xlabel("Day")
    plt.ylabel("Price")
    plt.title(title)
    if savepath:
        plt.savefig(savepath, bbox_inches='tight')
    plt.show()

    # Histograma de valores finales
    final_vals = sim_df.iloc[-1, :].values
    plt.figure(figsize=(8,4))
    plt.hist(final_vals, bins=40)
    plt.title(f"Distribución del precio final ({sim_df.shape[1]} simulaciones)")
    if savepath:
        plt.savefig(savepath.replace(".png", "_hist.png"), bbox_inches='tight')
    plt.show()