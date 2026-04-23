import hashlib

def compute_state(message_logs):
    state_hash = hashlib.sha256()
    for log in message_logs:
        state_hash.update(log.encode('utf-8'))
    return state_hash.hexdigest()

if __name__ == "__main__":
    # Logic for CU evaluation
    print(f"STATE_EVALUATION: {compute_state(['genesis', 'phi_gate_init'])}")
