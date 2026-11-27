"""Independent dense oracles for the prime-five resolvent and deformation."""

from fractions import Fraction as Q
from itertools import product
from random import Random

import pytest

from nextfft_lab.prime5_deformation import (
    Gaussian, WidthFourPlan, cyclic5_product, prime5_constants, prime5_join, prime5_split,
    schoolbook_product,
)

I = Gaussian(0, 1)
ZERO = Gaussian()


def dense_quotient(left, right, lam, order):
    # Form the ordinary bivariate product first, then reduce by the monic
    # polynomial Y**4-lambda and drop degrees >= order in z.
    dense = [[ZERO] * (2 * order - 1) for _ in range(7)]
    for i, j, u, v in product(range(4), range(4), range(order), range(order)):
        dense[i + j][u + v] += left[i][u] * right[j][v]
    return [[dense[i][j] + lam * dense[i + 4][j] if i < 3 else dense[i][j]
             for j in range(order)] for i in range(4)]


def dense_cyclic(left, right):
    return [sum((left[j] * right[(i - j) % 5] for j in range(5)), ZERO) for i in range(5)]


def cyclotomic(coefficients):
    return [coefficient - coefficients[4] for coefficient in coefficients[:4]]


def random_scalar(rng):
    return Gaussian(*(Q(rng.randint(-5, 5), rng.randint(1, 7)) for _ in range(2)))


def test_resolvents_and_coordinate_basis():
    assert I * I == Gaussian(-1)
    assert (I + Gaussian(2)) / (I + Gaussian(2)) == Gaussian(1)
    lam, kappas = prime5_constants()
    gamma = [ZERO, Gaussian(1), -I, I, Gaussian(-1)]
    powers = [[Gaussian(1)] + [ZERO] * 4]
    for _ in range(4):
        powers.append(dense_cyclic(powers[-1], gamma))
    assert lam == Gaussian(-15, -20)
    assert kappas == (Gaussian(1), Gaussian(-1, 2), Gaussian(3, 4))
    assert cyclotomic(powers[4]) == [lam, ZERO, ZERO, ZERO]
    for j in range(1, 4):
        resolvent = [ZERO] * 5
        for t, residue in enumerate((1, 2, 4, 3)):
            resolvent[residue] = (Gaussian(1), -I, Gaussian(-1), I)[j * t % 4]
        permuted = [resolvent[3 * k % 5] for k in range(5)]
        assert cyclotomic(permuted) == cyclotomic(
            [(Gaussian(1), I, Gaussian(-1), -I)[j] * v for v in resolvent]
        )
        assert cyclotomic(powers[j]) == cyclotomic([kappas[j - 1] * v for v in resolvent])
    for k in range(5):
        vector = [Gaussian(int(j == k)) for j in range(5)]
        scalar, coords = prime5_split(vector)
        assert scalar == Gaussian(1)
        reconstructed = [sum((coords[j] * powers[j][i] for j in range(4)), ZERO)
                         for i in range(5)]
        assert cyclotomic(reconstructed) == cyclotomic(vector)
        assert prime5_join(scalar, coords) == vector


@pytest.mark.parametrize("order", [1, 2, 3])
def test_all_bilinear_jet_basis_pairs(order):
    lam, _ = prime5_constants()
    plan = WidthFourPlan(lam, order)
    for i, j in product(range(4 * order), repeat=2):
        left = [[Gaussian(int(row * order + col == i)) for col in range(order)]
                for row in range(4)]
        right = [[Gaussian(int(row * order + col == j)) for col in range(order)]
                 for row in range(4)]
        assert plan.multiply(left, right) == dense_quotient(left, right, lam, order)


@pytest.mark.parametrize("lam", [Gaussian(1), Gaussian(Q(-2, 3), Q(3, 7)), Gaussian(-15, -20)])
def test_dense_jets(lam):
    rng = Random(20261127)
    plan = WidthFourPlan(lam, 3)
    for _ in range(4):
        left, right = ([[random_scalar(rng) for _ in range(3)] for _ in range(4)] for _ in range(2))
        expected = dense_quotient(left, right, lam, 3)
        assert plan.multiply(left, right) == expected
        assert schoolbook_product(left, right, lam, 3) == expected


def test_cyclic_basis_and_random():
    for i, j in product(range(5), repeat=2):
        left = [int(k == i) for k in range(5)]
        right = [int(k == j) for k in range(5)]
        assert cyclic5_product(left, right) == [Q(k == (i + j) % 5) for k in range(5)]
    rng = Random(713485)
    for _ in range(8):
        left, right = ([random_scalar(rng).real for _ in range(5)] for _ in range(2))
        assert cyclic5_product(left, right) == [
            sum(left[j] * right[(i - j) % 5] for j in range(5)) for i in range(5)
        ]


def test_rejections():
    for lam, order in [(0, 1), (1, 0), (1, 4), (1, True)]:
        with pytest.raises(ValueError):
            WidthFourPlan(lam, order)
    with pytest.raises(TypeError):
        Gaussian(0.5)
    with pytest.raises(ValueError):
        WidthFourPlan(1, 1).multiply([[1]], [[1]])
    with pytest.raises(ValueError):
        cyclic5_product([1], [1])
    with pytest.raises(ValueError):
        cyclic5_product([I] * 5, [1] * 5)
