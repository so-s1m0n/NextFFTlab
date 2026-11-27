from itertools import product
from random import Random

import pytest

from nextfft_lab.exact import P
from nextfft_lab.fiber_schedule import OccupiedFiberPlan, _BorrowedRegisters


def dense_tensor(row, shape, ratios):
    coordinates = tuple(product(*(range(n) for n in shape)))
    return [sum(value * pow(ratios[0], i[0] * j[0], P) * pow(ratios[1], i[1] * j[1], P)
                for value, j in zip(row, coordinates)) % P for i in coordinates]


def test_full_tensor_every_basis_both_directions():
    shape, ratios = (8, 8), (3, 5)
    plan = OccupiedFiberPlan.build(shape, ratios)
    for j in range(64):
        basis = [int(i == j) for i in range(64)]
        expected = dense_tensor(basis, shape, ratios)
        values = basis[:]
        plan.apply(values)
        assert values == expected
        plan.apply(values, inverse=True)
        assert values == basis


def test_each_word_restores_previously_processed_fibers_and_tail():
    plan = OccupiedFiberPlan.build((13, 4), (3, 5), (1,))
    axis, = plan.axes
    assert list(axis.groups()) == [(0, 6), (6, 7)]
    rng = Random(20261127)
    values = [rng.randrange(1, P) for _ in range(52)]
    for start, count in axis.groups():
        for offset in range(count):
            registers = _BorrowedRegisters(values, axis, start, count)
            registers.offset = offset
            before = values[:]
            axis.word.apply(registers)
            addresses = [axis.address(start + offset, j) for j in range(4)]
            expected = before[:]
            for i, addr in enumerate(addresses):
                expected[addr] = sum(before[index] * pow(5, i * j, P)
                                     for j, index in enumerate(addresses)) % P
            assert values == expected


def test_rejections():
    with pytest.raises(ValueError, match="neighboring"):
        OccupiedFiberPlan.build((4, 4), (3, 5))
    with pytest.raises(ValueError, match="distinct"):
        OccupiedFiberPlan.build((8, 8), (3, 5), (1, 1))
    with pytest.raises(ValueError, match="size"):
        OccupiedFiberPlan.build((8, 8), (3, 5)).apply([0])
