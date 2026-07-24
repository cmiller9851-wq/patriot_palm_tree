import time
import numpy as np


class WormholeBayesianEngine:

    def __init__(
        self, num_features: int, latent_dim: int = 4, prior_anomaly: float = 0.01
    ):
        """Initializes Wormhole Latent Projection Engine.

        - num_features (d): Dimension of input features.
        - latent_dim (m): Reduced wormhole transport space dimension.
        - prior_anomaly: Prior probability P(Anomaly).
        """
        self.d = num_features
        self.m = latent_dim
        self.prior_anomaly = prior_anomaly
        self.prior_normal = 1.0 - prior_anomaly

        # Pre-calculated theoretical logarithmic distribution (Benford baseline)
        digits = np.arange(1, 10, dtype=np.float64)
        self.p_benford = np.log10(1.0 + 1.0 / digits)
        self.p_uniform = np.full(9, 1.0 / 9.0, dtype=np.float64)

        # Precompute isometric wormhole projection matrix W (Orthogonal Latent Space)
        rng = np.random.default_rng(42)
        q_mat, _ = np.linalg.qr(rng.standard_normal((self.d, self.m)))
        self.W_wormhole = q_mat  # Shape: (d, m)

    def extract_leading_digits_vectorized(self, X: np.ndarray) -> np.ndarray:
        """Vectorized extraction of leading digits from 2D tensor X."""
        abs_X = np.abs(X)
        mask = abs_X > 0
        valid_vals = abs_X[mask]

        if valid_vals.size == 0:
            return np.array([], dtype=np.int32)

        # Mathematical mantissa extraction via log10 scale
        log_vals = np.floor(np.log10(valid_vals))
        leading = (valid_vals / (10.0**log_vals)).astype(np.int32)
        return np.clip(leading, 1, 9)

    def evaluate(self, X: np.ndarray) -> dict:
        """Executes full linear-time wormhole projection and Bayesian inference."""
        t0 = time.perf_counter()

        # Step 1: Wormhole Space Compression (Linear OT approximation step)
        # Projects N x d dataset into N x m latent manifold space
        X_wormhole = X @ self.W_wormhole
        t_proj = time.perf_counter() - t0

        # Step 2: Extract leading digit features across compressed tensor
        t1 = time.perf_counter()
        digits = self.extract_leading_digits_vectorized(X_wormhole)
        N_digits = digits.size

        if N_digits == 0:
            raise ValueError("Empty or zero-only array supplied.")

        # Step 3: Fast histogram binning (Counts for digits 1..9)
        counts = np.bincount(digits, minlength=10)[1:10]
        obs_freq = counts / N_digits

        # Step 4: Numerically Stable Log-Likelihood Calculation
        eps = 1e-12
        log_L_normal = np.sum(counts * np.log(self.p_benford + eps))
        log_L_anomaly = np.sum(counts * np.log(self.p_uniform + eps))

        # Log-Sum-Exp Trick for exact Bayesian Update without Underflow
        max_log = max(log_L_normal, log_L_anomaly)
        w_norm = np.exp(log_L_normal - max_log) * self.prior_normal
        w_anom = np.exp(log_L_anomaly - max_log) * self.prior_anomaly

        posterior_anomaly = w_anom / (w_norm + w_anom)
        t_eval = time.perf_counter() - t1

        # Wasserstein Distance Approximation in Latent Wormhole Space
        wasserstein_dist = np.linalg.norm(obs_freq - self.p_benford)

        return {
            "posterior_anomaly_prob": posterior_anomaly,
            "wasserstein_distance": wasserstein_dist,
            "projection_time_ms": t_proj * 1000.0,
            "evaluation_time_ms": t_eval * 1000.0,
            "sample_digits_processed": N_digits,
        }


# Pipeline Execution Benchmark
if __name__ == "__main__":
    NUM_SAMPLES = 50_000
    NUM_FEATURES = 64

    print("=== WORMHOLE-ACCELERATED BAYESIAN ANOMALY ENGINE ===")
    print(
        f"Dataset Shape: ({NUM_SAMPLES}, {NUM_FEATURES}) -> 3,200,000 Elements\n"
    )

    engine = WormholeBayesianEngine(
        num_features=NUM_FEATURES, latent_dim=8, prior_anomaly=0.01
    )

    # 1. Natural Scale-Invariant Matrix
    scale_matrix = 10 ** np.random.uniform(
        1.0, 5.0, size=(NUM_SAMPLES, NUM_FEATURES)
    )
    res_nat = engine.evaluate(scale_matrix)

    print("[+] --- Natural Organic Dataset ---")
    print(
        f"    Posterior Anomaly Prob : {res_nat['posterior_anomaly_prob'] * 100:.6f}%"
    )
    print(
        f"    Wasserstein Distance   : {res_nat['wasserstein_distance']:.6f}"
    )
    print(f"    Latent Projection Time : {res_nat['projection_time_ms']:.2f} ms")
    print(f"    Inference Time         : {res_nat['evaluation_time_ms']:.2f} ms")

    # 2. Uniform Synthetic Matrix
    synth_matrix = np.random.uniform(
        100.0, 999.0, size=(NUM_SAMPLES, NUM_FEATURES)
    )
    res_syn = engine.evaluate(synth_matrix)

    print("\n[+] --- Synthetic Uniform Dataset ---")
    print(
        f"    Posterior Anomaly Prob : {res_syn['posterior_anomaly_prob'] * 100:.6f}%"
    )
    print(
        f"    Wasserstein Distance   : {res_syn['wasserstein_distance']:.6f}"
    )
    print(f"    Latent Projection Time : {res_syn['projection_time_ms']:.2f} ms")
    print(f"    Inference Time         : {res_syn['evaluation_time_ms']:.2f} ms")
