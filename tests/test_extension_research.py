from itertools import product
from random import Random

import pytest

from nextfft_lab.exact import P
from nextfft_lab.extension_research import QuadraticGeometricGrid, QuarticProductPlan
from nextfft_lab.geometric_baselines import divided_difference_geometric


def _dense_grid(row, shape, ratios):
    indices = tuple(product(*(range(n) for n in shape)))
    return [sum(value * _entry(i, j, ratios) for j, value in zip(indices, row)) % P
            for i in indices]


def _entry(i, j, ratios):
    value = 1
    for a, b, q in zip(i, j, ratios):
        value = value * pow(q, a * b, P) % P
    return value


def _inverse_grid(row, shape, ratios):
    indices = list(product(*(range(n) for n in shape)))
    current = dict(zip(indices, row))
    for axis, (length, q) in enumerate(zip(shape, ratios)):
        updated = {}
        for key in indices:
            if key[axis] == 0:
                fiber = [key[:axis] + (j,) + key[axis + 1:] for j in range(length)]
                updated.update(zip(fiber, divided_difference_geometric([current[x] for x in fiber], q)))
        current = updated
    return [current[i] for i in indices]


@pytest.mark.parametrize("shape,ratios", [((2, 3), (3, 5)), ((2, 2, 2), (3, 5, 7))])
def test_packed_grid_every_basis_including_incomplete_batch(shape, ratios):
    plan = QuadraticGeometricGrid.build(shape, ratios)
    for column in range(3 * plan.size):
        rows = [[0] * plan.size for _ in range(3)]
        rows[column // plan.size][column % plan.size] = 1
        forward = [_dense_grid(row, shape, ratios) for row in rows]
        inverse = [_inverse_grid(row, shape, ratios) for row in rows]
        assert plan.apply(rows) == plan.apply_base(rows) == forward
        assert plan.apply(rows, inverse=True) == plan.apply_base(rows, inverse=True) == inverse


@pytest.mark.parametrize("width", [1, 2, 3, 8])
def test_packed_grid_seeded(width):
    shape, ratios = (3, 4), (3, 5)
    plan = QuadraticGeometricGrid.build(shape, ratios)
    rng = Random(20261127 + width)
    rows = [[rng.randrange(P) for _ in range(plan.size)] for _ in range(width)]
    assert plan.apply(rows) == [_dense_grid(row, shape, ratios) for row in rows]
    assert plan.apply(rows, inverse=True) == [_inverse_grid(row, shape, ratios) for row in rows]
    counts = plan.application_counts(width)
    assert counts["padded_coordinates"] == width % 2
    assert counts["packed_multiply"] > counts["base_multiply"] > 0
    assert counts["packed_add_sub"] > counts["base_add_sub"] > 0


def _schoolbook(left, right):
    return [sum(left[i] * right[k - i] for i in range(len(left)) if 0 <= k - i < len(right)) % P
            for k in range(len(left) + len(right) - 1)]


@pytest.mark.parametrize("n,jets,cyclic", [(8, 3, 6), (9, 3, 6), (12, 4, 6), (16, 3, 12)])
def test_quartic_packing_every_bilinear_basis(n, jets, cyclic):
    plan = QuarticProductPlan.build(n, jets, cyclic)
    vectors = [[int(i == j) for i in range(n)] for j in range(n)]
    for a, b in product(vectors, repeat=2):
        assert plan.multiply(a, b) == _schoolbook(a, b)
    rng = Random(20261127 + n)
    a, b = [[rng.randrange(P) for _ in range(n)] for _ in range(2)]
    assert plan.multiply(a, b) == _schoolbook(a, b)


def test_quartic_operand_recovery_through_extension_roots():
    plan = QuarticProductPlan.build(9, 3, 6)
    rng = Random(20261127)
    for coefficients in [[rng.randrange(P) for _ in range(9)] for _ in range(2)]:
        transformed = [plan._cyclic(layer) for layer in plan._pack(coefficients)]
        recovered_layers = [plan._cyclic(layer, inverse=True) for layer in transformed]
        recovered = []
        for x in range(6):
            for layer in recovered_layers:
                a, b, c, d = layer[x]
                assert c == d == 0
                recovered.extend((a, b))
        assert recovered == coefficients + [0] * (24 - len(coefficients))


def test_unsupported_shapes_and_lengths():
    for shape, ratios in [((1,), (3,)), ((16, 16), (3, 5)), ((2, 3), (3,)), ((2, 3), (3, 1))]:
        with pytest.raises(ValueError):
            QuadraticGeometricGrid.build(shape, ratios)
    with pytest.raises(ValueError):
        QuadraticGeometricGrid.build((2, 2), (3, 5)).apply([[1, 2]])
    with pytest.raises(ValueError):
        QuarticProductPlan.build(9, 3, 8)
    with pytest.raises(ValueError):
        QuarticProductPlan.build(8, 3, 6).multiply([0] * 7, [0] * 8)
