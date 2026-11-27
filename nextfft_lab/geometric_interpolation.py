"""Bostan–Schost geometric interpolation over the lab's fixed prime field.

Proposition 5 combines Newton interpolation (Proposition 3) and the
Newton-to-monomial conversion (Proposition 4).
"""
from dataclasses import dataclass

from .exact import P
from .geometric import ToeplitzPlan, _size


@dataclass(frozen=True)
class BostanSchostPlan:
    """Two precomputed convolutions and linear work besides NTT setup."""

    input_scale: tuple
    newton_kernel: ToeplitzPlan
    conversion_scale: tuple
    conversion_kernel: ToeplitzPlan
    output_scale: tuple

    @classmethod
    def build(cls, n, q):
        _size(n)
        q = int(q) % P
        if not q:
            raise ValueError("q must be nonzero")
        differences, products = [1], [1]
        q_power = 1
        for _ in range(1, n):
            q_power = q_power * q % P
            difference = (1 - q_power) % P
            if not difference:
                raise ValueError("geometric nodes are not distinct")
            differences.append(difference)
            products.append(products[-1] * difference % P)

        # H[i] = product(1-q^j, j=1..i). Invert the chain with one inversion.
        inverses = [0] * n
        inverses[-1] = pow(products[-1], -1, P)
        for i in range(n - 1, 0, -1):
            inverses[i - 1] = inverses[i] * differences[i] % P

        t, reciprocal_t, q_power, inverse_power = 1, 1, 1, 1
        inverse_q = pow(q, -1, P)
        first_scale, first_kernel, second_scale, second_kernel = [], [], [], []
        for i, (h, h_inv) in enumerate(zip(products, inverses)):
            sign = -1 if i % 2 else 1
            coefficient = t * h_inv % P
            first_scale.append(sign * h_inv % P)
            first_kernel.append(coefficient)
            second_scale.append(h * reciprocal_t % P)
            second_kernel.append(sign * coefficient % P)
            t = t * q_power % P
            reciprocal_t = reciprocal_t * inverse_power % P
            q_power = q_power * q % P
            inverse_power = inverse_power * inverse_q % P
        return cls(tuple(first_scale), ToeplitzPlan.build(first_kernel),
                   tuple(second_scale), ToeplitzPlan.build(second_kernel), tuple(inverses))

    def interpolate(self, values):
        samples = list(values)
        if len(samples) != len(self.input_scale):
            raise ValueError("wrong sample length")
        # First convolution returns Newton coefficients scaled by q^binom(i,2).
        scaled = [int(y) * w % P for y, w in zip(samples, self.input_scale)]
        weighted_newton = self.newton_kernel.apply(scaled)
        scaled = [v * w % P for v, w in zip(weighted_newton, self.conversion_scale)]
        monomial = self.conversion_kernel.apply(scaled, upper=True)
        return [v * w % P for v, w in zip(monomial, self.output_scale)]
