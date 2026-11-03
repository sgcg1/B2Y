"""Deterministic FP32-representable inputs; standard library only."""
import random

N = 16384

def build_cases():
    rng = random.Random(20261103)
    def shuffled(values):
        rng.shuffle(values)
        return values
    cases = [
        {"label": "random-control", "values": [rng.gauss(0, 1) for _ in range(N)], "window": [0, N], "overflow": None},
        {"label": "boundary-2048", "values": shuffled([1000.] * 2047 + [100.] * 2048 + [0.] * (N - 4095)), "window": [0, N], "overflow": False},
        {"label": "boundary-2049", "values": shuffled([1000.] * 2047 + [100.] * 2049 + [0.] * (N - 4096)), "window": [0, N], "overflow": True},
        {"label": "quantized-four-levels", "values": shuffled([1. + (i % 4) / 64 for i in range(N)]), "window": [0, N], "overflow": True},
        {"label": "close-fp32", "values": shuffled([1. + (i % 8192) * 2**-22 for i in range(N)]), "window": [0, N], "overflow": True},
        {"label": "shuffled-two-levels", "values": shuffled([1.] * 8192 + [1.125] * 8192), "window": [0, N], "overflow": True},
        {"label": "narrow-overflow", "values": [10000.] * 512 + shuffled([1000.] * 1024 + [100.] * 3072) + [10000.] * (N - 4608), "window": [512, 4608], "overflow": True},
    ]
    return cases

def validation_cases():
    values = [float("nan"), float("inf"), -float("inf"), 0., -0., 65520., -65520., 65504.] * (N // 8)
    return [("special-full", values, 0, N), ("special-short", values, 9, 59),
            ("empty", values, 50, 50), ("reversed", values, 60, 50)]
