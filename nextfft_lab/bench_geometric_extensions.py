"""Matched measurements for occupied words and classical geometric baselines."""
import argparse
import json
from random import Random

from .bench_repair import environment, measure
from .exact import P
from .geometric import NewtonPlan
from .geometric_baselines import GeometricChirp, divided_difference_geometric, horner_geometric
from .occupied import OccupiedNewton


def run(repeats):
    seed, q = 20261127, 3
    rng = Random(seed)
    rows = {}
    for n in (8, 32, 64, 128):
        batch = [[rng.randrange(P) for _ in range(n)] for _ in range(4)]
        plan, chirp = NewtonPlan.build(n, q), GeometricChirp.build(n, q)
        values = [horner_geometric(row, q) for row in batch]
        assert [plan.apply(row) for row in batch] == [chirp.apply(row) for row in batch] == values
        assert [plan.apply(row, inverse=True) for row in values] == [
            divided_difference_geometric(row, q) for row in values
        ] == batch
        row = batch[0]
        results = {
            "newton_setup": measure(lambda: NewtonPlan.build(n, q), repeats),
            "chirp_setup": measure(lambda: GeometricChirp.build(n, q), repeats),
            "newton_one": measure(lambda: plan.apply(row), repeats),
            "chirp_one": measure(lambda: chirp.apply(row), repeats),
            "horner_one": measure(lambda: horner_geometric(row, q), repeats),
            "newton_batch4": measure(lambda: [plan.apply(x) for x in batch], repeats),
            "chirp_batch4": measure(lambda: [chirp.apply(x) for x in batch], repeats),
            "horner_batch4": measure(lambda: [horner_geometric(x, q) for x in batch], repeats),
            "newton_inverse_batch4": measure(lambda: [plan.apply(y, inverse=True) for y in values], repeats),
            "divided_difference_batch4": measure(
                lambda: [divided_difference_geometric(y, q) for y in values], repeats
            ),
        }
        if n <= 32:
            occupied = OccupiedNewton.build(n, q)
            dirty = [rng.randrange(1, P) for _ in range(occupied.register_count - n)]
            registers = row + dirty

            def apply_occupied():
                # Caller restores the same input in the existing slots between samples.
                for i, value in enumerate(row):
                    registers[i] = value
                occupied.apply(registers)

            apply_occupied()
            assert registers == values[0] + dirty
            results["occupied_word"] = {
                "setup": measure(lambda: OccupiedNewton.build(n, q), repeats),
                "apply_with_input_reset": measure(apply_occupied, repeats),
                "data_registers": occupied.register_count,
                "padded_length": occupied.lower.forward.padded,
                "ntt_transforms_per_application": 192,
            }
        rows[n] = results
    return {"environment": environment(), "seed": seed, "field": P, "q": q,
            "repeats": repeats, "rows_by_length": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=7)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 20:
        parser.error("repeats must be between 1 and 20")
    print(json.dumps(run(args.repeats), indent=2))


if __name__ == "__main__":
    main()
