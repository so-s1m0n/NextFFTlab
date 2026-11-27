from random import Random

import pytest

from nextfft_lab.exact import P, direct
from nextfft_lab.geometric_packing import good_factor, packed_product


@pytest.mark.parametrize("n,jets,cyclic", [(1, 4, 2), (3, 3, 8), (8, 8, 8), (16, 8, 16)])
def test_packing_carries_and_dense_oracle(n, jets, cyclic):
    rng = Random(n)
    basis = [[int(i == j) for i in range(n)] for j in range(n)]
    pairs = [(a, b) for a in basis for b in basis]
    pairs.append(tuple([rng.randrange(P) for _ in range(n)] for _ in range(2)))
    for a, b in pairs:
        expected = [0] * (2 * n - 1)
        for i, x in enumerate(a):
            for j, y in enumerate(b):
                expected[i + j] = (expected[i + j] + x * y) % P
        assert packed_product(a, b, jets=jets, cyclic=cyclic) == expected


@pytest.mark.parametrize("a,b", [(2, 7), (4, 7), (17, 2)])
def test_good_factor_dense_basis_and_random(a, b):
    n = a * b
    rng = Random(n)
    for row in [[int(i == j) for i in range(n)] for j in range(n)] + [[rng.randrange(P) for _ in range(n)]]:
        assert good_factor(row, a, b) == direct(row)
        assert good_factor(row, a, b, inverse=True) == direct(row, inverse=True)


def test_ineligible_plans():
    with pytest.raises(ValueError):
        packed_product([1], [2], jets=2, cyclic=4 + 4)
    with pytest.raises(ValueError):
        good_factor([0] * 16, 4, 4)
    with pytest.raises(ValueError):
        good_factor([0] * 6, 2, 3)
