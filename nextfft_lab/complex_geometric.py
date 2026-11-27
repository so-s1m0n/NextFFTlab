"""Bounded complex128 experiment for the geometric Newton factorization."""

import numpy as np
from scipy.fft import fft, ifft, next_fast_len

MAX_SIZE = 128


class ComplexNewtonPlan:
    """Evaluate at q**j. The experiment makes no numerical stability assumption."""

    def __init__(self, n, q, *, backend="direct"):
        if type(n) is not int or not 1 <= n <= MAX_SIZE:
            raise ValueError(f"n must be an integer between 1 and {MAX_SIZE}")
        if backend not in ("direct", "fft"):
            raise ValueError("backend must be direct or fft")
        q = complex(q)
        if not np.isfinite(q) or q == 0:
            raise ValueError("q must be finite and nonzero")

        self.n = n
        self.backend = backend
        self._h = np.ones(n, dtype=np.complex128)
        self._c = np.ones(n, dtype=np.complex128)
        power = 1 + 0j
        with np.errstate(over="raise", divide="raise", invalid="raise"):
            for i in range(1, n):
                self._c[i] = -self._c[i - 1] * power
                power *= q
                if power == 1:
                    raise ValueError("repeated geometric nodes in complex128")
                self._h[i] = self._h[i - 1] * (1 - power)
            if np.any(self._h == 0) or np.any(self._c == 0):
                raise FloatingPointError("a diagonal factor underflowed to zero")
            self._kernel = 1 / self._h
            self._middle = self._c / self._h

        if backend == "fft":
            self._padded = next_fast_len(2 * n - 1)
            self._spectrum = fft(self._kernel, n=self._padded, workers=1)

    def _row(self, values):
        row = np.asarray(values, dtype=np.complex128)
        if row.shape != (self.n,) or not np.all(np.isfinite(row)):
            raise ValueError("expected one finite row of the configured size")
        return row

    def _product(self, row):
        if self.backend == "fft":
            spectrum = fft(row, n=self._padded, workers=1)
            return ifft(spectrum * self._spectrum, workers=1)[:self.n]
        return np.convolve(row, self._kernel)[:self.n]

    @property
    def max_kernel_magnitude(self):
        """Diagnostic for intermediate scaling, not a condition number."""
        return float(np.max(np.abs(self._kernel)))

    def evaluate(self, values):
        """Apply diag(H) T diag(c/H) T^t diag(H)."""
        with np.errstate(over="raise", divide="raise", invalid="raise"):
            scaled = self._row(values) * self._h
            upper = self._product(scaled[::-1])[::-1]
            return self._h * self._product(upper * self._middle)

    def interpolate(self, samples):
        """Reverse the factors using a direct reciprocal-series experiment."""
        with np.errstate(over="raise", divide="raise", invalid="raise"):
            row = self._row(samples) / self._h
            inverse = np.ones(self.n, dtype=np.complex128)
            for i in range(1, self.n):
                inverse[i] = -np.dot(self._kernel[1:i + 1], inverse[i - 1::-1])
            lower = np.convolve(row, inverse)[:self.n] * (self._h / self._c)
            return np.convolve(lower[::-1], inverse)[:self.n][::-1] / self._h
