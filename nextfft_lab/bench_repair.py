"""Small, reproducible Python component measurements."""
import argparse
import gc
import json
import os
import platform
from random import Random
from statistics import median
from time import perf_counter_ns
import tracemalloc

from .exact import P, root
from .query_polynomial import compile_query_polynomial
from .walsh import direct_walsh, walsh


def measure(operation, repeats):
    operation()
    samples = []
    for _ in range(repeats):
        start = perf_counter_ns()
        operation()
        samples.append(perf_counter_ns() - start)
    gc.collect()
    tracemalloc.start()
    try:
        operation()
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    return {"samples_ns": samples, "median_ns": median(samples), "python_peak_bytes": peak}


def run(repeats):
    rng = Random(20261126)
    results = {}
    for size in (8, 32, 128):
        row = tuple(rng.randrange(P) for _ in range(size))
        assert walsh(row) == direct_walsh(row)
        results[f"walsh_{size}"] = {
            "direct": measure(lambda: direct_walsh(row), repeats),
            "iterative": measure(lambda: walsh(row), repeats),
            "direct_signed_terms": size * size,
            "iterative_adds_subtracts": size * (size.bit_length() - 1),
        }
    for m, ell, bounds in ((3, 2, (1, 2)), (128, 2, None), (16, 7, None), (16, 17, None)):
        shifts = tuple(rng.randrange(ell) for _ in range(m))
        # Use one digit per query so the powers represent an actual eigenvalue.
        digits = tuple(rng.randrange(ell) for _ in shifts)
        powers = tuple(tuple(pow(root(ell), digit * a, P) for a in range(1, ell))
                       for digit in digits)
        polynomial = compile_query_polynomial(shifts, ell, bounds)
        width = len(polynomial.weights) - 1
        form_count = min(width, ell - 1)
        results[f"query_{m}_{ell}"] = {
            "setup": measure(lambda: compile_query_polynomial(shifts, ell, bounds), repeats),
            "evaluation": measure(lambda: polynomial.evaluate(powers), repeats),
            "degree_bound": polynomial.degree_bound,
            "term_bound": polynomial.expanded_term_bound,
            "interpolation_width": width,
            "affine_forms": m * form_count,
            "evaluation_multiply_accumulates": (
                m * form_count * (ell - 1)
                + m * sum(width + 1 - h for h in range(1, form_count + 1))
                + width + 1
            ),
            "max_coefficient_bits": max(
                value.bit_length()
                for value in (*polynomial.initial_series, *polynomial.weights,
                              *(value for forms in polynomial.affine_factors
                                for form in forms for value in form))
            ),
        }
    return {
        "environment": {
            "os": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "cpu": os.environ.get("NEXTFFT_BENCH_CPU", platform.processor()),
            "python": platform.python_version(),
            "threads": 1,
        },
        "seed": 20261126,
        "prime": P,
        "repeats": repeats,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=20)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats must be positive")
    print(json.dumps(run(args.repeats), indent=2))


if __name__ == "__main__":
    main()
