from itertools import product
from math import comb
from random import Random

import pytest

from nextfft_lab.binary_repair import binary_degree_coefficients, compile_binary_repair
from nextfft_lab.exact import P
from nextfft_lab.matrix_pencil import matrix_root, scalar_stage
from nextfft_lab.query_polynomial import compile_query_polynomial
from nextfft_lab.spectral_repair import HALF, _binary_quotient_at, compile_repair, frequency_repair


@pytest.mark.parametrize("radix", [2, 4, 8])
def test_matrix_root_on_basis_and_random_points(radix):
    # (3+2x)(1+y)+(5-y) has overlapping affine variables.
    pencil = matrix_root(radix, [[(3, 2, 0), (1, 0, 1)], [(5, 0, -1)]])
    rng = Random(42)
    for x, y in [(0, 0), (1, P - 1), (rng.randrange(P), rng.randrange(P))]:
        expected = ((3 + 2 * x) * (1 + y) + 5 - y) % P
        for index in range(pencil.rows):
            vector = [int(i == index) for i in range(pencil.rows)]
            for _ in range(radix):
                vector = scalar_stage(pencil, vector, (x, y))
            assert vector == [expected if i == index else 0 for i in range(pencil.rows)]


@pytest.mark.parametrize("target", [1, P - 1])
def test_frequency_repair_at_double_root_and_multiple_errors(target):
    nodes = [7, 13, 23, 101, 509]
    exceptional = (0, 3, 4)
    multipliers = [25, target, 14]
    table = frequency_repair(nodes, target, exceptional, multipliers)
    for x in [target, *multipliers]:
        g = HALF * (3 * x - x**3) % P
        assert (g - target) % P == (x - target)**2 * _binary_quotient_at(x, target) % P
    values = [82, 79, 2, 15, 1]
    predicted = [target * value for value in values]
    for index, multiplier in zip(exceptional, multipliers):
        predicted[index] = values[index] * multiplier
    checks = lambda row: [sum(x * node**h for x, node in zip(row, nodes)) % P for h in range(4)]
    lift, target_lift = table.evaluate(checks(predicted), checks(values))
    assert lift[3] == 0
    assert target_lift == [target * value % P for value in lift]
    for index, multiplier in zip(exceptional, multipliers):
        lifted = sum(a * nodes[index]**h for h, a in enumerate(lift)) % P
        assert lifted == (_binary_quotient_at(multiplier, target)
                          * (multiplier - target) * values[index]) % P


def test_empty_and_changing_exception_sets():
    rng = Random(123)
    spectra = [[rng.randrange(P) for _ in range(2)] for _ in range(3)]
    multipliers = [(1, 11), (1, P - 1), (1, 23)]
    plan = compile_repair(range(3), [(1, [], []), (P - 1, [0, 2], [11, 23])])
    ordinary = lambda a, b: [(a + b) * HALF % P, (a - b) * HALF % P]
    matrix = [ordinary(*row) for row in spectra]

    def predictor(batch):
        return [ordinary((a + b) * x, (a - b) * y)
                for (a, b), (x, y) in zip(batch, multipliers)]

    assert plan.apply(matrix, predictor) == [ordinary(a, -b) for a, b in spectra]


@pytest.mark.parametrize("m,bounds,shape", [(2, None, (32, 0, 8)), (3, (1, 2), (64, 16, 2))])
def test_ordinary_repair_compares_to_independent_xor(m, bounds, shape):
    plan = compile_binary_repair(m, bounds)
    assert (plan.repair.width, plan.repair.check_count, plan.pencils[0].radix) == shape
    rng = Random(777)
    rows = [[rng.randrange(P) for _ in range(plan.size)] for _ in range(plan.repair.width)]
    assert plan.apply(rows) == [row[::-1] for row in rows]
    zeros = [[0] * plan.size for _ in rows]
    for coordinate in range(plan.size):
        for index in range(plan.repair.width):
            zeros[index][coordinate] = 1
            assert plan.apply(zeros) == [row[::-1] for row in zeros]
            zeros[index][coordinate] = 0


def test_actual_toy_conversion_and_predictor_counts(monkeypatch):
    import nextfft_lab.spectral_repair as repair

    plan = compile_binary_repair(3, (1, 2))
    forwards, inverses, applications = [], [], []
    original = repair.walsh

    def walsh(row, inverse=False):
        (inverses if inverse else forwards).append(1)
        return original(row, inverse)

    def predictor(rows):
        applications.append(1)
        return plan.predict(rows)

    monkeypatch.setattr(repair, "walsh", walsh)
    rows = [[(i * i + j) % 137 for j in range(8)] for i in range(64)]
    assert plan.repair.apply(rows, predictor) == [row[::-1] for row in rows]
    assert (len(forwards), len(inverses), len(applications)) == (32, 32, 4)
    assert len({table.exceptional for table in plan.repair.frequencies}) == 4


@pytest.mark.parametrize("bounds", [None, (1, 2), (-1, 3), (3, 3)])
def test_binary_coefficients_against_independent_cube_interpolation(bounds):
    polynomial = compile_query_polynomial([0, 0, 0], bounds=bounds)
    by_degree = binary_degree_coefficients(polynomial)
    cube = list(product((-1, 1), repeat=3))
    for d, value in enumerate(by_degree):
        moment = sum(polynomial.evaluate([(v,) for v in point])
                     * (-1)**(d - sum(v == -1 for v in point[:d])) for point in cube)
        assert value == moment * pow(len(cube), -1, P) % P
    assert sum(comb(3, d) for d, value in enumerate(by_degree) if value) <= polynomial.expanded_term_bound


def test_rejects_unsupported_or_large_constructions():
    with pytest.raises(ValueError, match="above"):
        matrix_root(2, [[(1,)]] * 13)
    with pytest.raises(ValueError, match="divisor"):
        matrix_root(1 << 24, [[(1,)]])
    with pytest.raises(ValueError, match="distinct"):
        compile_repair([0, P], [(1, [], [])])
    with pytest.raises(ValueError, match="shift blocks"):
        compile_binary_repair(128)
    with pytest.raises(ValueError, match="above|exceed"):
        compile_binary_repair(3, (1, 3))
    plan = compile_binary_repair(2)
    with pytest.raises(ValueError, match="shape"):
        plan.apply([[0] * 4])
