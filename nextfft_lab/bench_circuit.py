"""Verify, save and measure bounded Walsh circuit synthesis and tensor lifts."""
import argparse
import json
from pathlib import Path
from random import Random

from .bench_repair import environment, measure
from .exact import P
from .linear_circuit import butterfly_circuit, tensor_walsh_circuit, verify_walsh
from .walsh import walsh
from .walsh_search import (
    MAX_CONFIGURATIONS, MAX_SEARCH_SECONDS, sussman_h8_circuit, synthesize_rank_one,
)

PYTHON_PEAK_LIMIT = 16 * 1024**2


def _measure(operation, repeats):
    data = measure(operation, repeats)
    if data["python_peak_bytes"] > PYTHON_PEAK_LIMIT:
        raise MemoryError("experiment exceeded the Python allocation budget")
    return data


def run(repeats, output_dir=None):
    rng = Random(20261126)
    searched = {size: synthesize_rank_one(size) for size in (4, 8)}
    known = sussman_h8_circuit()
    artifacts = {f"rank-one-h{size}": value.circuit for size, value in searched.items()}
    artifacts["sussman-h8"] = known
    search_results = {
        size: {
            "configurations": value.configurations,
            "matching": value.matching,
            "anchors": value.anchors,
            "search": _measure(lambda: synthesize_rank_one(size), min(repeats, 3)),
        }
        for size, value in searched.items()
    }
    profiles = {}
    for size in (4, 8, 64, 512):
        row = [rng.randrange(P) for _ in range(size)]
        expected = walsh(row)
        bench = {"iterative_walsh": _measure(lambda: walsh(row), repeats)}
        variants = {"butterfly_circuit": butterfly_circuit(size)}
        if size in searched:
            variants["synthesized"] = searched[size].circuit
        if size >= 8:
            variants["published_h8_lift"] = tensor_walsh_circuit(known, size)
        for name, circuit in variants.items():
            if not verify_walsh(circuit) or circuit.evaluate(row) != expected:
                raise ArithmeticError(f"circuit mismatch at {name}, n={size}")
            bench[name] = {
                "counts": circuit.counts(),
                "verified_basis_vectors": size,
                "evaluation": _measure(lambda: circuit.evaluate(row), repeats),
            }
        profiles[size] = bench

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        for name, circuit in artifacts.items():
            (output_dir / f"{name}.json").write_text(
                json.dumps(circuit.to_dict(), indent=2) + "\n", encoding="utf-8"
            )
    return {
        "environment": environment(), "prime": P, "seed": 20261126, "repeats": repeats,
        "budget": {
            "max_search_configurations": MAX_CONFIGURATIONS,
            "max_seconds_per_search": MAX_SEARCH_SECONDS,
            "max_python_peak_bytes_per_measurement": PYTHON_PEAK_LIMIT,
        },
        "search": search_results, "profiles": profiles,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--repeats", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 30:
        parser.error("repeat count must be between 1 and 30")
    print(json.dumps(run(args.repeats, args.out_dir), indent=2))


if __name__ == "__main__":
    main()
