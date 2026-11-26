"""Reproduce the exact-window, component, and fixed-batch ablation experiments."""
import argparse
import ctypes
import json
import os
from random import Random
from statistics import median
from time import perf_counter_ns

from .bench_repair import environment, measure
from .binary_kernel import binary_query
from .binary_template import compile_binary_square_template
from .compact_template import compile_compact_square_template
from .exact import P
from .implicit_pencil import compile_implicit_matrix_root, endpoint_factors
from .matrix_pencil import matrix_root, scalar_stage
from .predictor import window
from .spectral_repair import compile_repair
from .walsh import walsh
from .window_search import (
    endpoint_predictor, endpoint_shift_masks, narrowest_symmetric_window, window_cost,
)


def peak_process_bytes():
    """Return process high-water resident bytes, including interpreter and inputs."""
    if os.name != "nt":
        import resource
        import sys
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return rss if sys.platform == "darwin" else rss * 1024

    from ctypes.wintypes import DWORD, HANDLE
    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", DWORD), ("faults", DWORD),
            ("peak_working_set", ctypes.c_size_t), ("working_set", ctypes.c_size_t),
            ("peak_paged", ctypes.c_size_t), ("paged", ctypes.c_size_t),
            ("peak_nonpaged", ctypes.c_size_t), ("nonpaged", ctypes.c_size_t),
            ("pagefile", ctypes.c_size_t), ("peak_pagefile", ctypes.c_size_t),
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    current = ctypes.windll.kernel32.GetCurrentProcess
    current.restype = HANDLE
    info = ctypes.windll.psapi.GetProcessMemoryInfo
    info.argtypes = [HANDLE, ctypes.POINTER(Counters), DWORD]
    if not info(current(), ctypes.byref(counters), counters.cb):
        raise OSError("GetProcessMemoryInfo failed")
    return counters.peak_working_set


def _classical(batch):
    return [[walsh(row) for row in block] for block in batch]


def measure_variant(variant, repeats):
    rng = Random(20261126)
    rows = 128
    start = perf_counter_ns()
    if variant == "baseline":
        plan = compile_binary_square_template()
    elif variant == "classical":
        plan = None
    else:
        plan = compile_compact_square_template(original_radix=variant == "routing-only")
    cold = perf_counter_ns() - start
    batch = [[[rng.randrange(P) for _ in range(256)] for _ in range(rows)] for _ in range(4)]
    expected = _classical(batch)
    apply = _classical if plan is None else plan.apply
    samples = []
    for _ in range(repeats):
        start = perf_counter_ns()
        result = apply(batch)
        samples.append(perf_counter_ns() - start)
        if result != expected:
            raise ArithmeticError("template output differs from classical Walsh")
        del result

    if variant == "classical":
        counts = {"axis_calls": 4 * rows * 8, "walsh_add_sub": 4 * rows * 256 * 8}
    else:
        if variant == "baseline":
            pair_calls = 40 * rows
            constant_edges = sum(bool(a) for line in plan.matrices[0] for a in line)
            query_edges = rows - constant_edges
            gather_rows = 8 * 3 * rows
            final_rows = 8 * rows
        else:
            pair_calls = plan.pair_calls_per_stage
            constant_edges = len(plan.edges[0])
            query_edges = sum(map(len, plan.edges[1:]))
            gather_rows = 8 * query_edges
            final_rows = 4 * len(set().union(*plan.destinations))
        stages = plan.stages
        counts = {
            "axis_calls": 2 * pair_calls * stages,
            "pencil_stages": stages,
            "pair_kernel_calls": pair_calls * stages,
            "pair_kernel_add_sub": 7 * 64 * pair_calls * stages,
            "pair_kernel_multiplications": 8 * 64 * pair_calls * stages,
            "cross_row_mix_mac": (4 * constant_edges + 16 * query_edges) * 256 * stages,
            "charged_gather_scalar_accumulations": gather_rows * 256 * stages,
            "free_output_scalar_accumulations": final_rows * 256 * stages,
            "matrix_coefficient_slots": 4 * rows**2 if variant == "baseline" else rows,
        }
    return {
        "environment": environment(),
        "rows": 4 * rows,
        "size": 256,
        "cold_setup_ns": cold,
        "samples_ns": samples,
        "median_ns": median(samples),
        "peak_process_bytes": peak_process_bytes(),
        "counts": counts,
    }


def _extension_product(left, right):
    rank = len(left)
    out = [0] * rank
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            k = i + j
            if k < rank:
                out[k] += a * b
            else:
                out[k - rank] -= a * b
    return [value % P for value in out]


def _repair_cost(rng, checks, repeats):
    width, size = 24, 8
    batch = [[rng.randrange(P) for _ in range(size)] for _ in range(width)]
    # A different known set at each frequency, implemented as a synthetic
    # spectral predictor here to isolate repair overhead. Zero exceptions uses identity.
    exceptions = [tuple((frequency + offset) % width for offset in range(checks))
                  for frequency in range(size)]
    specs = [(1, indices, [2] * len(indices)) for indices in exceptions]
    plan = compile_repair(range(width), specs)

    def predictor(rows):
        if not checks:
            return [list(row) for row in rows]
        spectra = [walsh(row) for row in rows]
        for frequency, indices in enumerate(exceptions):
            for index in indices:
                spectra[index][frequency] = 2 * spectra[index][frequency] % P
        return [walsh(row, inverse=True) for row in spectra]

    if plan.apply(batch, predictor) != batch:
        raise ArithmeticError("repair failed to recover the known identity")
    return {
        "width": width,
        "size": size,
        "checks": checks,
        "repair_and_synthetic_predictor": measure(lambda: plan.apply(batch, predictor), repeats),
        "synthetic_predictor_once": measure(lambda: predictor(batch), repeats),
        "setup": measure(lambda: compile_repair(range(width), specs), repeats),
        "check_lift_mac": 4 * checks * width * size,
        "spectral_solve_mac": 2 * checks**2 * size,
        "check_conversions": 4 * checks,
    }


def _endpoint_pencil_cost(rng, repeats):
    terms = endpoint_factors(15)
    explicit = matrix_root(16, terms)
    implicit = compile_implicit_matrix_root(16, terms)
    signs = [rng.randrange(2, P - 2) for _ in range(15)]
    row = [rng.randrange(P) for _ in range(explicit.rows)]

    def materialized():
        current = row
        for _ in range(16):
            current = scalar_stage(explicit, current, signs)
        return current

    predicted = endpoint_predictor(signs)
    expected = [predicted * value % P for value in row]
    if implicit.apply_power(row, signs) != expected or materialized() != expected:
        raise ArithmeticError("endpoint pencil differs from the independent factored polynomial")
    return {
        "rows_per_shift": explicit.rows,
        "materialized_setup": measure(lambda: matrix_root(16, terms), repeats),
        "implicit_setup": measure(lambda: compile_implicit_matrix_root(16, terms), repeats),
        "materialized_apply_power": measure(materialized, repeats),
        "implicit_apply_power": measure(lambda: implicit.apply_power(row, signs), repeats),
        "materialized_affine_coefficient_slots": 4096 * 3 * 16,
        "implicit_factor_count": 3 * 16,
        "tensor_transition_visits": 16 * 4096 * 3,
    }


def measure_components(repeats):
    rng = Random(20261126)
    profiles = {}
    for m in (3, 13, 14, 15, 23, 31, 63, 128):
        exact = narrowest_symmetric_window(m)
        profiles[m] = {
            "paper": window_cost(m, window(m)),
            "exact": window_cost(m, exact[:2]),
            "exact_search": measure(lambda: narrowest_symmetric_window(m), repeats),
        }
    axes = {}
    for m, aux in ((3, 0), (3, 1), (3, 2), (5, 0), (3, 3), (5, 1)):
        count = 1 << (2 * (m + aux))
        row = [rng.randrange(P) for _ in range(count)]
        axes[f"{m},{aux}"] = {
            "axes": 2 * (m + aux),
            "entries": count,
            "one_query": measure(lambda: binary_query(row, m, aux, 1, 0), repeats),
            "pair_blocks": (aux + 1) * count // 4,
        }
    extensions = {}
    for d in (1, 2, 4, 8, 16, 32):
        left = [rng.randrange(P) for _ in range(d)]
        right = [rng.randrange(P) for _ in range(d)]
        direct = [sum(left[i] * right[(k - i) % d] * (1 if i <= k else -1)
                      for i in range(d)) % P for k in range(d)]
        if _extension_product(left, right) != direct:
            raise ArithmeticError("extension product differs from signed convolution")
        extensions[d] = {
            "cost": measure(lambda: _extension_product(left, right), repeats),
            "base_multiplications": d*d,
            "packed_operand_bytes": 4*d,
        }
    return {
        "environment": environment(), "seed": 20261126,
        "window_profiles": profiles, "axis_profiles": axes,
        "repair_profiles": [_repair_cost(rng, s, repeats) for s in (0, 1, 2, 4, 8)],
        "extension_profiles": extensions,
        "endpoint_pencil": _endpoint_pencil_cost(rng, min(repeats, 3)),
        "m15_endpoint_shift_design": {
            "shift_count": len(endpoint_shift_masks(15)),
            "max_exception_shifts": 1,
            "rows_per_label": len(endpoint_shift_masks(15)) * 16**3,
            "checks_per_label": 16**3,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=("baseline", "routing-only", "compact", "classical", "components"),
                        default="components")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.repeats <= (20 if args.variant == "components" else 3):
        parser.error("repeat count exceeds the bounded experiment budget")
    run = measure_components(args.repeats) if args.variant == "components" else measure_variant(
        args.variant, args.repeats
    )
    print(json.dumps(run, indent=2))


if __name__ == "__main__":
    main()
