import numpy as np
import pytest
from scipy.fft import fft
from scipy.signal import CZT, ZoomFFT

from nextfft_lab.bench_complex_geometric import _float_ratio, _ratio, decimal_horner
from nextfft_lab.complex_geometric import ComplexNewtonPlan


@pytest.mark.parametrize("backend", ["direct", "fft"])
@pytest.mark.parametrize("q", [0.92 * np.exp(-0.9j), np.exp(-2j * np.pi / 8)])
def test_all_basis_columns_against_independent_decimal_horner(backend, q):
    plan = ComplexNewtonPlan(8, q, backend=backend)
    for basis in np.eye(8):
        expected, _ = decimal_horner(basis, _float_ratio(q))
        np.testing.assert_allclose(plan.evaluate(basis), expected, atol=3e-12, rtol=3e-12)
        np.testing.assert_allclose(plan.interpolate(expected), basis, atol=3e-12, rtol=3e-12)


def test_scipy_forward_grid_orientation_matches_decimal():
    x = np.array([1j, 0.25, -2j, -0.5, 2 + 1j, 3, 0, 1.25])
    full, _ = decimal_horner(x, _ratio(len(x), "1", "1"))
    arc, _ = decimal_horner(x, _ratio(len(x), "0.08", "1"))
    spiral_q = _ratio(len(x), "0.65", "1.002")
    spiral, _ = decimal_horner(x, spiral_q)
    np.testing.assert_allclose(fft(x), full, atol=1e-13, rtol=1e-13)
    np.testing.assert_allclose(ZoomFFT(len(x), (0.0, 0.08), fs=1.0)(x), arc, atol=1e-13, rtol=1e-13)
    np.testing.assert_allclose(CZT(len(x), w=complex(*spiral_q))(x), spiral, atol=1e-13, rtol=1e-13)


@pytest.mark.parametrize("n,q", [(0, 1), (129, 2), (4, 0), (4, complex("nan")), (3, -1), (2, 1)])
def test_plan_validation(n, q):
    with pytest.raises(ValueError):
        ComplexNewtonPlan(n, q)


def test_singleton_and_invalid_rows():
    plan = ComplexNewtonPlan(1, 1, backend="fft")
    np.testing.assert_array_equal(plan.evaluate([2 + 3j]), [2 + 3j])
    np.testing.assert_array_equal(plan.interpolate([2 + 3j]), [2 + 3j])
    for row in ([1, 2], [np.inf], [[1]]):
        with pytest.raises(ValueError):
            plan.evaluate(row)
