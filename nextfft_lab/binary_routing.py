"""Shared binary pencil routing for kernel.tex with L=q=2 and f=1."""
from dataclasses import dataclass

from .binary_kernel import _pair_query, _shape, binary_rectangles
from .exact import P


def _swap_permutation(j, auxiliary, half_bits):
    low_j, low_aux = 1 << j, 1 << auxiliary
    out = []
    for index in range(1 << (2 * half_bits)):
        delta = ((index & low_j != 0) ^ (index & low_aux != 0)) * (low_j | low_aux)
        high = index >> half_bits
        delta_high = ((high & low_j != 0) ^ (high & low_aux != 0)) * (low_j | low_aux)
        out.append(index ^ delta ^ (delta_high << half_bits))
    return tuple(out)


def _combine_into(output, source, matrix, weight=1):
    for row, coefficients in zip(output, matrix):
        for index, coefficient in coefficients:
            source_row = source[index]
            scalar = weight * coefficient % P
            if scalar:
                for i, value in enumerate(source_row):
                    row[i] = (row[i] + scalar * value) % P


@dataclass(frozen=True)
class BinarySquareRouting:
    rectangles: tuple
    permutations: tuple

    def apply(self, labels, query_matrices, constant_matrix):
        """Apply one pencil stage on independent label × row × address inputs."""
        m = len(query_matrices)
        half_bits = _shape(m, 1, 1)
        size = 1 << (2 * half_bits)
        rows = len(constant_matrix)
        if m != 3 or not 1 <= rows <= 128 or len(labels) != 4:
            raise ValueError("three queries, four labels and 1..128 rows per label required")
        if any(len(matrix) != rows or any(len(row) != rows for row in matrix)
               for matrix in (constant_matrix, *query_matrices)):
            raise ValueError("all pencil matrices must be square and match the batch width")
        if any(len(block) != rows or any(len(row) != size for row in block) for block in labels):
            raise ValueError("label batch shape mismatch")

        constant, *queries = tuple(
            tuple(tuple((i, coefficient % P) for i, coefficient in enumerate(row) if coefficient % P)
                  for row in matrix)
            for matrix in (constant_matrix, *query_matrices)
        )
        output = [[[0] * size for _ in range(rows)] for _ in labels]
        for result, block in zip(output, labels):
            _combine_into(result, block, constant)
        for rectangle in self.rectangles:
            weight = rectangle.weight
            if rectangle.charged:
                for j, matrix in enumerate(queries):
                    mixed = [[0] * size for _ in range(rows)]
                    for source in rectangle.sources:
                        for total, row in zip(mixed, labels[source]):
                            ordered = [row[i] for i in self.permutations[j]] if source in (1, 2) else row
                            for i, value in enumerate(ordered):
                                total[i] = (total[i] + value) % P
                    shared = [_pair_query(_pair_query(row, j, half_bits), m, half_bits) for row in mixed]
                    for destination in rectangle.destinations:
                        block = ([[row[i] for i in self.permutations[j]] for row in shared]
                                 if destination in (1, 2) else shared)
                        _combine_into(output[destination], block, matrix, weight)
                continue

            # In the L=q=2 Gram quotient the two label parities give the
            # two orthogonal basis vectors. A free rectangle is a
            # singleton pair of opposite parities, so relabeling swaps
            # the distinguished and auxiliary coordinates in each half.
            source, = rectangle.sources
            destination, = rectangle.destinations
            first = [_pair_query(list(row), m, half_bits) for row in labels[source]]
            mixed = [[0] * size for _ in range(rows)]
            for j, matrix in enumerate(queries):
                transposed = [[row[i] for i in self.permutations[j]] for row in first]
                _combine_into(mixed, transposed, matrix)
            final = [_pair_query(row, m, half_bits) for row in mixed]
            for target, row in zip(output[destination], final):
                for i, value in enumerate(row):
                    target[i] = (target[i] + weight * value) % P
        return output


def compile_binary_square_routing():
    """Precompute the four-label rectangle decomposition."""
    _, rectangles = binary_rectangles(2, 2)
    return BinarySquareRouting(rectangles, tuple(_swap_permutation(j, 3, 4) for j in range(3)))
