"""A5 experiment: independently reference complex geometric evaluation with Decimal."""
import argparse
from decimal import Decimal, localcontext
import json
from pathlib import Path
import platform
from statistics import median
from time import perf_counter_ns

import numpy as np
import scipy
from scipy.fft import fft
from scipy.signal import CZT, ZoomFFT

from .complex_geometric import ComplexNewtonPlan

PRECISION = 100
PI = Decimal("3.14159265358979323846264338327950288419716939937510582097494459230781640628620899862803482534211706798214808651")
SEED = 20261127
SIZES = (8, 32, 64, 128)


def _ratio(n, turns, radius):
    with localcontext() as ctx:
        ctx.prec = PRECISION
        theta = -2 * PI * Decimal(turns) / n
        cosine, sine = Decimal(1), theta
        term_c, term_s = cosine, sine
        for k in range(1, 100):
            term_c *= -theta * theta / ((2 * k) * (2 * k - 1))
            term_s *= -theta * theta / ((2 * k) * (2 * k + 1))
            cosine += term_c
            sine += term_s
            if abs(term_c) + abs(term_s) < Decimal(10) ** -PRECISION:
                return Decimal(radius) * cosine, Decimal(radius) * sine
        raise ArithmeticError("Decimal trig series did not converge")


def _mul(a, b):
    x, y = a
    u, v = b
    return x * u - y * v, x * v + y * u


def _float_ratio(q):
    return Decimal.from_float(q.real), Decimal.from_float(q.imag)


def decimal_horner(values, ratio):
    """Independent Horner reference with inputs represented exactly as binary64."""
    values = [_float_ratio(complex(value)) for value in values]
    out = []
    nodes = []
    with localcontext() as ctx:
        ctx.prec = PRECISION
        node = Decimal(1), Decimal(0)
        for _ in values:
            nodes.append(complex(*node))
            a = Decimal(0), Decimal(0)
            for u, v in reversed(values):
                x, y = _mul(a, node)
                a = x + u, y + v
            out.append(complex(*a))
            node = _mul(node, ratio)
    return np.array(out), np.array(nodes)


def _norm(x):
    scale = np.max(np.abs(x))
    return float(scale * np.linalg.norm(x / scale)) if scale else 0.0


def _finite(value):
    return float(value) if np.isfinite(value) else None


def _relative(values, reference):
    return _finite(_norm(values - reference) / _norm(reference))


def _timed(factory, x, reference, rounded_reference, repeats):
    try:
        start = perf_counter_ns()
        apply = factory()
        setup = perf_counter_ns() - start
        first = apply(x)
        if not np.all(np.isfinite(first)):
            raise FloatingPointError("nonfinite output")
        times = []
        for _ in range(repeats):
            start = perf_counter_ns()
            apply(x)
            times.append(perf_counter_ns() - start)
        return {
            "status": "measured", "setup_ns": setup, "warm_ns": times,
            "warm_median_ns": median(times),
            "relative_l2_ideal_grid": _relative(first, reference),
            "relative_l2_rounded_q_grid": _relative(first, rounded_reference),
        }
    except (ValueError, FloatingPointError, OverflowError) as error:
        return {"status": "failed", "reason": str(error)}


def _interpolate(n, q, x, samples, ratio, matrix):
    try:
        plan = ComplexNewtonPlan(n, q)
        coefficients = plan.interpolate(samples)
        if not np.all(np.isfinite(coefficients)):
            raise FloatingPointError("nonfinite coefficients")
        reconstructed, _ = decimal_horner(coefficients, ratio)
        denominator = np.linalg.norm(matrix, ord=2) * _norm(coefficients) + _norm(samples)
        return {
            "status": "measured",
            "relative_l2_coefficient_error": _relative(coefficients, x),
            "normwise_residual": _finite(_norm(reconstructed - samples) / denominator),
            "max_abs_toeplitz_kernel": plan.max_kernel_magnitude,
        }
    except (ValueError, FloatingPointError, OverflowError) as error:
        return {"status": "failed", "reason": str(error)}


def run(repeats=5):
    if not 1 <= repeats <= 20:
        raise ValueError("repeats must be between 1 and 20")
    rng = np.random.default_rng(SEED)
    cases = []
    for n in SIZES:
        x = rng.standard_normal(n) + 1j * rng.standard_normal(n)
        for name, turns, radius in (("dft", "1", "1"), ("unit_arc", "0.08", "1"),
                                    ("spiral", "0.65", "1.002")):
            ratio = _ratio(n, turns, radius)
            q = complex(*ratio)
            rounded_ratio = _float_ratio(q)
            exact, nodes = decimal_horner(x, ratio)
            rounded, rounded_nodes = decimal_horner(x, rounded_ratio)
            gram = rounded_nodes[:, None] ** np.arange(n)
            singular_values = np.linalg.svd(gram, compute_uv=False)
            condition = singular_values[0] / singular_values[-1] if singular_values[-1] else np.inf
            methods = {
                "newton_direct": lambda: ComplexNewtonPlan(n, q).evaluate,
                "newton_fft": lambda: ComplexNewtonPlan(n, q, backend="fft").evaluate,
                "czt_explicit_q": lambda: CZT(n=n, w=q),
            }
            if radius == "1":
                methods["zoom_fft"] = lambda: ZoomFFT(n, (0.0, float(turns)), fs=1.0)
            if name == "dft":
                methods["czt_default_grid"] = lambda: CZT(n=n)
                methods["fft"] = lambda: lambda row: fft(row, workers=1)
            cases.append({
                "grid": name, "length": n, "turns": turns, "step_radius": radius,
                "q_complex128": [q.real, q.imag],
                "relative_l2_parameter_rounding": _relative(rounded, exact),
                "condition_2_estimate": _finite(condition),
                "smallest_singular_value_estimate": _finite(singular_values[-1]),
                "forward": {name: _timed(factory, x, exact, rounded, repeats)
                            for name, factory in methods.items()},
                "newton_interpolation": _interpolate(n, q, x, rounded, rounded_ratio, gram),
            })
    return {
        "schema": 1, "stage": "A5", "arithmetic": "complex128",
        "oracle": "100-digit Decimal geometric Horner; rounded to complex128 once",
        "repeats": repeats, "seed": SEED,
        "environment": {"python": platform.python_version(), "system": platform.system(),
                        "machine": platform.machine(), "numpy": np.__version__,
                        "scipy": scipy.__version__, "fft_workers": 1},
        "cases": cases,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--out", type=Path)
    opts = parser.parse_args()
    if not 1 <= opts.repeats <= 20:
        parser.error("repeats must be between 1 and 20")
    data = json.dumps(run(opts.repeats), indent=2, allow_nan=False) + "\n"
    if opts.out:
        opts.out.write_text(data, encoding="utf-8")
    else:
        print(data, end="")


if __name__ == "__main__":
    main()
