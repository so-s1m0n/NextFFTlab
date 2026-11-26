"""Measure the bounded matrix-pencil and Hermite repair path."""
import argparse
import json
from math import comb
from random import Random

from .bench_repair import environment, measure
from .binary_repair import binary_degree_coefficients, compile_binary_repair
from .exact import P
from .predictor import window
from .query_polynomial import compile_query_polynomial


def theorem_window_estimate(m):
    lower, upper = window(m)
    radix = 1 << (max(2, upper - lower) - 1).bit_length()
    coefficients = binary_degree_coefficients(compile_query_polynomial([0] * m))
    terms = sum(comb(m, degree) for degree, coefficient in enumerate(coefficients) if coefficient)
    log2_width = m + (radix.bit_length() - 1) * terms
    exceptions = sum(comb(m, count) for count in range(m + 1) if not lower <= count <= upper)
    return {
        "window": [lower, upper],
        "radix": radix,
        "terms_per_shift": terms,
        "log2_batch_width": log2_width,
        "exception_shifts": exceptions,
        "factored_cube_indicator_log2_width_upper": (
            m + (radix.bit_length() - 1) * (1 + exceptions) if m <= radix else None
        ),
        "concentration_fraction_bound_holds": exceptions * 2 * m**3 <= 1 << m,
        "paper_cyclotomic_rank_log2": log2_width - 1,
    }


def run(repeats):
    rng = Random(20261126)
    cases = {}
    for name, m, bounds in (("toy_with_repair", 3, (1, 2)), ("theorem_no_exceptions", 2, None)):
        plan = compile_binary_repair(m, bounds)
        width, size, s = plan.repair.width, plan.size, plan.repair.check_count
        batch = [[rng.randrange(P) for _ in range(size)] for _ in range(width)]
        reference = lambda: [row[::-1] for row in batch]
        assert plan.apply(batch) == reference()
        radix = plan.pencils[0].radix
        predictor_calls = 4 if s else 1
        nonzero_coefficients = sum(bool(value) for pencil in plan.pencils for column in pencil.columns
                                   for _, form in column for value in form)
        cases[name] = {
            "setup": measure(lambda: compile_binary_repair(m, bounds), repeats),
            "reused_apply": measure(lambda: plan.apply(batch), repeats),
            "reference_xor_permutation": measure(reference, repeats),
            "width": width,
            "samples_per_row": size,
            "vandermonde_checks": s,
            "matrix_root_radix": radix,
            "predictor_applications": predictor_calls,
            "pencil_stages": radix * predictor_calls,
            "pencil_multiply_accumulates": size * nonzero_coefficients * radix * predictor_calls,
            "forward_row_conversions": 2 * s,
            "inverse_row_conversions": 2 * s,
            "conversion_adds_subtracts": 4 * s * size * m,
            "inverse_conversion_scalings": 2 * s * size,
            "cross_row_check_and_lift_multiply_accumulates": 4 * size * s * width,
            "spectral_inverse_and_transpose_multiply_accumulates": sum(
                2 * len(frequency.exceptional)**2 for frequency in plan.repair.frequencies
            ),
        }
    return {
        "environment": environment(),
        "seed": 20261126,
        "prime": P,
        "repeats": repeats,
        "cases": cases,
        "theorem_estimates": {m: theorem_window_estimate(m) for m in (2, 60, 128)},
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
