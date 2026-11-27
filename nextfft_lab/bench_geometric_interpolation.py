"""Compare exact interpolation and a polynomial multiplication application."""
import json
from random import Random

from .bench_repair import environment, measure
from .exact import P, convolution
from .geometric import NewtonPlan
from .geometric_baselines import GeometricChirp, divided_difference_geometric
from .geometric_interpolation import BostanSchostPlan


def run():
    seed, q, repeats = 20261127, 3, 7
    rng = Random(seed)
    rows, products = {}, {}
    for n in (8, 32, 128, 512):
        baseline, candidate = NewtonPlan.build(n, q), BostanSchostPlan.build(n, q)
        samples = [[rng.randrange(P) for _ in range(n)] for _ in range(16)]
        classical = lambda: divided_difference_geometric(samples[0], q)
        assert baseline.apply(samples[0], inverse=True) == classical()
        assert all(candidate.interpolate(y) == baseline.apply(y, inverse=True) for y in samples)
        rows[n] = {
            "newton_setup": measure(lambda: NewtonPlan.build(n, q), repeats),
            "bostan_schost_setup": measure(lambda: BostanSchostPlan.build(n, q), repeats),
            "newton_cold_one": measure(lambda: NewtonPlan.build(n, q).apply(samples[0], inverse=True), repeats),
            "bostan_schost_cold_one": measure(
                lambda: BostanSchostPlan.build(n, q).interpolate(samples[0]), repeats
            ),
            "quadratic_one": measure(classical, repeats),
            "warm": {
                width: {
                    "newton": measure(lambda: [baseline.apply(y, inverse=True) for y in samples[:width]], repeats),
                    "bostan_schost": measure(lambda: [candidate.interpolate(y) for y in samples[:width]], repeats),
                }
                for width in (1, 4, 16)
            },
        }
    for m in (8, 32, 128):
        n = 2 * m - 1
        left, right = ([rng.randrange(P) for _ in range(m)] for _ in range(2))
        a, b = left + [0] * (m - 1), right + [0] * (m - 1)
        evaluate = GeometricChirp.build(n, q)
        interpolate = BostanSchostPlan.build(n, q)

        def product(forward, inverse):
            values = [x*y % P for x, y in zip(forward.apply(a), forward.apply(b))]
            return inverse.interpolate(values)

        def cold():
            return product(GeometricChirp.build(n, q), BostanSchostPlan.build(n, q))

        def dense():
            result = [0] * n
            for i, x in enumerate(left):
                for j, y in enumerate(right):
                    result[i + j] = (result[i + j] + x*y) % P
            return result

        assert product(evaluate, interpolate) == dense() == convolution(left, right)
        products[m] = {
            "product_length": n,
            "geometric_warm": measure(lambda: product(evaluate, interpolate), repeats),
            "geometric_cold": measure(cold, repeats),
            "classical_linear_ntt": measure(lambda: convolution(left, right), repeats),
        }
    return {"environment": environment(), "seed": seed, "q": q, "field": P, "repeats": repeats,
            "interpolation_rows": rows, "polynomial_products": products}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
