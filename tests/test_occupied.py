from random import Random

import pytest

from nextfft_lab.exact import P
from nextfft_lab.occupied import OccupiedNewton, OccupiedToeplitz, OccupiedTriangular


def basis(size):
    for i in range(size):
        yield [int(j == i) for j in range(size)]


@pytest.mark.parametrize("n", [1, 3, 5])
def test_combined_toeplitz_basis(n):
    col, row = [4 + j for j in range(n)], [4 + 2 * j for j in range(n)]
    plan = OccupiedToeplitz.build(col, row)
    for registers in basis(plan.register_count):
        expected = registers[:]
        for i in range(n):
            expected[n + i] = (expected[n + i] + sum(
                registers[j] * (col[i-j] if i >= j else row[j-i]) for j in range(n)
            )) % P
        original = registers[:]
        plan.shear(registers)
        assert registers == expected
        plan.shear(registers, inverse=True)
        assert registers == original


@pytest.mark.parametrize("upper", [False, True])
def test_triangular_basis_and_dirty_registers(upper):
    n = 4
    col = [11, 8, 0, P - 2]
    plan = OccupiedTriangular.build(col)
    rng = Random(20261127)
    trials = [*basis(plan.register_count), [rng.randrange(1, P) for _ in range(plan.register_count)]]
    for registers in trials:
        y = [sum(col[abs(i-j)] * registers[j] for j in range(n)
                 if (i <= j if upper else i >= j)) % P for i in range(n)]
        expected = y + registers[n:]
        plan.apply(registers, upper=upper)
        assert registers == expected


def test_newton_basis_both_directions():
    n, q = 5, 3
    plan = OccupiedNewton.build(n, q)
    cols = [[pow(q, i * j, P) for i in range(n)] for j in range(n)]
    for j, registers in enumerate(basis(plan.register_count)):
        if j < n:
            expected = cols[j] + registers[n:]
            inverse_input = cols[j] + registers[n:]
        else:
            expected = registers[:]
            inverse_input = registers[:]
        basis_vector = registers[:]
        plan.apply(registers)
        assert registers == expected
        plan.apply(inverse_input, inverse=True)
        assert inverse_input == basis_vector


def test_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        OccupiedToeplitz.build([1, 0], [2, 0])
    with pytest.raises(ValueError):
        OccupiedTriangular.build([0, 1])
    with pytest.raises(ValueError):
        OccupiedNewton.build(2, 1)
    with pytest.raises(ValueError):
        OccupiedToeplitz.build([1], [1]).shear([3])
