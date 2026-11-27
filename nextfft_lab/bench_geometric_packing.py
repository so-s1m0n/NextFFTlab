"""Cost of bounded base-field packing and Good-factor checks."""
import json
from random import Random

from .bench_repair import environment, measure
from .exact import P, bluestein, convolution, direct
from .geometric_packing import good_factor, packed_product


def run():
    seed, repeats = 20261127, 7
    rng = Random(seed)
    packing, factors = {}, {}
    for n, jets, cyclic in ((8, 8, 8), (16, 8, 16), (32, 8, 32)):
        x, y = [rng.randrange(P) for _ in range(n)], [rng.randrange(P) for _ in range(n)]
        apply = lambda: packed_product(x, y, jets=jets, cyclic=cyclic)
        assert apply() == convolution(x, y)
        packing[n] = {"jets": jets, "cyclic": cyclic, "packed": measure(apply, repeats),
                      "linear_ntt": measure(lambda: convolution(x, y), repeats)}
    for a, b in ((2, 7), (4, 7), (4, 17)):
        x = [rng.randrange(P) for _ in range(a * b)]
        apply = lambda: good_factor(x, a, b)
        assert apply() == direct(x) == bluestein(x)
        factors[a*b] = {"axes": [a, b], "good": measure(apply, repeats),
                        "bluestein": measure(lambda: bluestein(x), repeats),
                        "dense": measure(lambda: direct(x), repeats)}
    return {"environment": environment(), "seed": seed, "repeats": repeats,
            "field": P, "packing": packing, "good_factors": factors}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
