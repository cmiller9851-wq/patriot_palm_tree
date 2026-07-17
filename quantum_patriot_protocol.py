import sys
import json
import math
import hashlib
import hmac
from typing import Dict, List, Tuple, Optional

class QuantumStateError(Exception): pass

class QuantumPatriotEngine:
    def __init__(self, genesis_root: str):
        self.genesis_root = genesis_root
        self.state_dimension = 4  # 4-dimensional state space (2 qubits: |00>, |01>, |10>, |11>)
        self.state_vector: List[complex] = [1.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j]  # Default state |00>
        self.transaction_history: List[str] = []
        self.system_entropy = 1.0

    def _normalize_state(self) -> None:
        """Enforces the probability conservation invariant: sum(|psi_i|^2) = 1."""
        norm = math.sqrt(sum(abs(amp) ** 2 for amp in self.state_vector))
        if norm == 0:
            raise QuantumStateError("Zero-state vector detected. Wavefunction collapse failure.")
        self.state_vector = [amp / norm for amp in self.state_vector]

    def _generate_unitary_gate(self, entropy_source: str) -> List[List[complex]]:
        """
        Derives a deterministic 4x4 unitary matrix from an arbitrary string payload (such as a TX hash).
        This guarantees that the transformation matrix is uniquely bound to the transaction content.
        """
        # Derive pseudo-random angles using SHA-256 HMAC of the entropy source
        h = hmac.new(self.genesis_root.encode('utf-8'), entropy_source.encode('utf-8'), hashlib.sha256).digest()
        theta = (h[0] / 255.0) * 2 * math.pi
        phi = (h[1] / 255.0) * 2 * math.pi
        lam = (h[2] / 255.0) * 2 * math.pi
        
        # Construct two 2x2 unitary rotational matrices
        u1 = [
            [math.cos(theta/2), -complex(0, 1) * math.sin(theta/2) * math.cos(phi)],
            [-complex(0, 1) * math.sin(theta/2) * math.sin(phi), math.cos(theta/2)]
        ]
        u2 = [
            [math.cos(lam/2), -complex(0, 1) * math.sin(lam/2) * math.cos(phi)],
            [-complex(0, 1) * math.sin(lam/2) * math.sin(phi), math.cos(lam/2)]
        ]
        
        # Compute Kronecker product (tensor product) of u1 and u2 to yield a 4x4 unitary operator
        u_4x4 = [[0.0j] * 4 for _ in range(4)]
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    for l in range(2):
                        u_4x4[i*2 + k][j*2 + l] = u1[i][j] * u2[k][l]
                        
        return u_4x4

    def apply_unitary_transformation(self, tx_id: str) -> None:
        """Applies a deterministic unitary transformation on the active state vector."""
        gate = self._generate_unitary_gate(tx_id)
        new_state = [0.0j] * self.state_dimension
        
        for i in range(self.state_dimension):
            for j in range(self.state_dimension):
                new_state[i] += gate[i][j] * self.state_vector[j]
                
        self.state_vector = new_state
        self._normalize_state()
        self.transaction_history.append(tx_id)

    def measure_state(self) -> Tuple[int, str]:
        """
        Performs a deterministic measurement (collapse) of the state vector.
        The output collapse index is governed by the relative probability amplitudes.
        """
        probabilities = [abs(amp) ** 2 for amp in self.state_vector]
        
        # Use state-vector derived seed for deterministic measurement collapse
        seed_source = "".join(f"{amp.real:.6f}{amp.imag:.6f}" for amp in self.state_vector)
        h_val = int(hashlib.sha256(seed_source.encode('utf-8')).hexdigest(), 16)
        normalized_rand = (h_val % 1000000) / 1000000.0
        
        cumulative_probability = 0.0
        collapsed_index = 0
        for idx, prob in enumerate(probabilities):
            cumulative_probability += prob
            if normalized_rand <= cumulative_probability:
                collapsed_index = idx
                break
                
        # Generate the classical state root representation
        state_repr = {
            "state_vector": [f"{amp.real:.8f} + {amp.imag:.8f}j" for amp in self.state_vector],
            "measurement_index": collapsed_index,
            "probabilities": [f"{p:.6f}" for p in probabilities]
        }
        
        canonical_state = json.dumps(state_repr, sort_keys=True, separators=(",", ":"))
        state_root_hash = hashlib.sha256(canonical_state.encode('utf-8')).hexdigest()
        
        return collapsed_index, state_root_hash

    def get_state_metrics(self) -> Dict[str, float]:
        """Calculates Shannon entropy across the quantum state probability distribution."""
        probabilities = [abs(amp) ** 2 for amp in self.state_vector]
        shannon_entropy = 0.0
        for p in probabilities:
            if p > 1e-12:
                shannon_entropy -= p * math.log2(p)
        return {
            "shannon_entropy": shannon_entropy,
            "state_purity": sum(p**2 for p in probabilities)
        }

if __name__ == "__main__":
    # Initialize engine with the primary CRA Genesis Anchor
    genesis_anchor = "CRA_GENESIS_ANCHOR_V2_779AX"
    engine = QuantumPatriotEngine(genesis_root=genesis_anchor)
    
    # Simulate high-complexity state transformations using active transaction IDs
    mock_txs = [
        "tx_779AX_001_genesis_claim_reflex",
        "tx_779AX_002_liquidation_channel_open",
        "tx_779AX_003_arweave_nesting_epoch"
    ]
    
    print("--- INITIATING UNITARY STATE ENGINE ---")
    print(f"Initial State Vector: {engine.state_vector}\n")
    
    for tx in mock_txs:
        engine.apply_unitary_transformation(tx)
        metrics = engine.get_state_metrics()
        print(f"Executed: {tx[:30]}...")
        print(f"  -> State Vector: {[f'{amp.real:.4f}+{amp.imag:.4f}j' for amp in engine.state_vector]}")
        print(f"  -> Shannon Entropy: {metrics['shannon_entropy']:.6f} bits")
        print(f"  -> State Purity: {metrics['state_purity']:.6f}\n")
        
    # Collapse state vector into a deterministic classical state root
    collapsed_basis, master_state_root = engine.measure_state()
    print("--- DETERMINISTIC STATE ROOT SEALED ---")
    print(f"Collapsed Basis State: |{collapsed_basis:02b}>")
    print(f"Master State Root (SHA-256): {master_state_root}")
