"""Matched timings for extension-coordinate grid and polynomial product checks."""
import argparse
import json
from random import Random

from .bench_repair import environment, measure
from .exact import P, convolution
from .extension_research import QuadraticGeometricGrid, QuarticProductPlan
from .geometric import NewtonPlan


def run(repeats):
    seed = 20261127
    rng = Random(seed)
    grids, products = [], []
    for shape, width in (((2, 3), 2), ((2, 3), 3), ((3, 4), 5), ((2, 2, 3), 8)):
        ratios = (3, 5, 7)[:len(shape)]
        plan = QuadraticGeometricGrid.build(shape, ratios)
        rows = [[rng.randrange(P) for _ in range(plan.size)] for _ in range(width)]
        values = plan.apply_base(rows)
        assert plan.apply(rows) == values
        assert plan.apply(values, inverse=True) == plan.apply_base(values, inverse=True) == rows
        grids.append({
            "shape": shape,
            "ratios": ratios,
            "batch_width": width,
            "packed_setup_with_base_reference": measure(lambda: QuadraticGeometricGrid.build(shape, ratios), repeats),
            "base_setup": measure(lambda: [NewtonPlan.build(n, q) for n, q in zip(shape, ratios)], repeats),
            "packed_forward": measure(lambda: plan.apply(rows), repeats),
            "base_forward": measure(lambda: plan.apply_base(rows), repeats),
            "packed_inverse": measure(lambda: plan.apply(values, inverse=True), repeats),
            "base_inverse": measure(lambda: plan.apply_base(values, inverse=True), repeats),
            "application_counts": plan.application_counts(width),
        })
    for n, jets, cyclic in ((8, 3, 6), (9, 3, 6), (12, 4, 6), (16, 3, 12)):
        left, right = ([rng.randrange(P) for _ in range(n)] for _ in range(2))
        plan = QuarticProductPlan.build(n, jets, cyclic)
        assert plan.multiply(left, right) == convolution(left, right)
        products.append({
            "length": n,
            "extension_degree": 4,
            "jets": jets,
            "cyclic_length": cyclic,
            "packed_setup": measure(lambda: QuarticProductPlan.build(n, jets, cyclic), repeats),
            "packed_warm": measure(lambda: plan.multiply(left, right), repeats),
            "packed_cold": measure(lambda: QuarticProductPlan.build(n, jets, cyclic).multiply(left, right), repeats),
            "base_linear_ntt": measure(lambda: convolution(left, right), repeats),
            "application_counts": plan.application_counts(),
        })
    return {"environment": environment(), "seed": seed, "field": P, "repeats": repeats,
            "quadratic_grids": grids, "quartic_products": products}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=7)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 20:
        parser.error("repeats must be between 1 and 20")
    print(json.dumps(run(args.repeats), indent=2))


if __name__ == "__main__":
    main()
