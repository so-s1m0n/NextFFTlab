"""Sparse fixed binary template with exact degree and endpoint reuse."""
from dataclasses import dataclass

from .binary_kernel import _pair_query, binary_endpoint
from .binary_routing import BinarySquareRouting, compile_binary_square_routing
from .exact import P
from .matrix_pencil import matrix_root

SIZE = 256
HALF_BITS = 4


def _accumulate(output, source, coefficient, permutation=None):
    if permutation is None:
        for i, value in enumerate(source):
            output[i] = (output[i] + coefficient * value) % P
    else:
        for i, index in enumerate(permutation):
            output[i] = (output[i] + coefficient * source[index]) % P


@dataclass(frozen=True)
class CompactSquareTemplate:
    routing: BinarySquareRouting
    edges: tuple
    sources: tuple
    destinations: tuple
    stages: int
    rows_per_label: int

    @property
    def pair_calls_per_stage(self):
        return (
            2 * sum(rect.charged for rect in self.routing.rectangles)
            * sum(len(active) for active in self.sources)
            + 4 * len(set().union(*self.sources))
            + 4 * len(set().union(*self.destinations))
        )

    def stage(self, labels):
        # One row per nonzero column, with no dense row matrix or permutation copy.
        output = [[[0] * SIZE for _ in range(self.rows_per_label)] for _ in labels]
        for answer, block in zip(output, labels):
            for dest, source, coeff in self.edges[0]:
                _accumulate(answer[dest], block[source], coeff)

        for rect in self.routing.rectangles:
            if not rect.charged:
                continue
            for j, (edges, sources) in enumerate(zip(self.edges[1:], self.sources)):
                perm = self.routing.permutations[j]
                transformed = {}
                for source in sources:
                    total = [0] * SIZE
                    for label in rect.sources:
                        _accumulate(total, labels[label][source], 1, perm if label in (1, 2) else None)
                    transformed[source] = _pair_query(_pair_query(total, j, HALF_BITS), 3, HALF_BITS)
                for label in rect.destinations:
                    for dest, source, coeff in edges:
                        _accumulate(output[label][dest], transformed[source], coeff * rect.weight % P,
                                    perm if label in (1, 2) else None)

        # The source auxiliary transform is independent of the destination.
        # The destination transform commutes with summing rectangle contributions.
        live_inputs = sorted(set().union(*self.sources))
        live_outputs = sorted(set().union(*self.destinations))
        accumulated = [{row: [0] * SIZE for row in live_outputs} for _ in labels]
        for label, block in enumerate(labels):
            first = {row: _pair_query(block[row], 3, HALF_BITS) for row in live_inputs}
            for rect in self.routing.rectangles:
                if rect.charged or rect.sources != (label,):
                    continue
                destination, = rect.destinations
                for j, edges in enumerate(self.edges[1:]):
                    perm = self.routing.permutations[j]
                    for dest, source, coeff in edges:
                        _accumulate(accumulated[destination][dest], first[source],
                                    coeff * rect.weight % P, perm)
        for answer, rows in zip(output, accumulated):
            for row, partial in rows.items():
                _accumulate(answer[row], _pair_query(partial, 3, HALF_BITS), 1)
        return output

    def apply(self, labels, inverse=False):
        if len(labels) != 4 or any(len(rows) != self.rows_per_label for rows in labels):
            raise ValueError("template needs four blocks of independent rows")
        current = [[binary_endpoint(row, 3, 1, 1) for row in rows] for rows in labels]
        for _ in range(self.stages):
            current = self.stage(current)
        out = [[binary_endpoint(row, 3, 1, 1, output=True) for row in rows] for rows in current]
        if inverse:
            scale = pow(SIZE, -1, P)
            out = [[[value * scale % P for value in row] for row in rows] for rows in out]
        return out


def compile_compact_square_template(rows_per_label=128, *, original_radix=False):
    """Use the degree-three monomial on all shifts of the zero-exception case."""
    if rows_per_label not in (32, 64, 96, 128):
        raise ValueError("rows per label must be a multiple of 32 with a maximum of 128")
    # The multilinear predictor equals Q_0 Q_1 Q_2 on the entire sign cube.
    # One four-lane matrix root per shift suffices. Repeat complete sets of
    # shifts to accept the same 512 independently supplied rows as the baseline.
    radix = 16 if original_radix else 4
    if rows_per_label < 8 * radix:
        raise ValueError("batch must fit all eight shifts at this radix")
    pencil = matrix_root(radix, [[(0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)]])
    edges = [[] for _ in range(4)]
    for start in range(0, rows_per_label, pencil.rows):
        for source, transitions in enumerate(pencil.columns, start=start):
            for destination, form in transitions:
                for kind, coeff in enumerate(form):
                    if coeff:
                        edges[kind].append((start + destination, source, coeff))
    return CompactSquareTemplate(
        compile_binary_square_routing(),
        tuple(tuple(group) for group in edges),
        tuple(tuple(sorted({source for _, source, _ in group})) for group in edges[1:]),
        tuple(tuple(sorted({destination for destination, _, _ in group})) for group in edges[1:]),
        pencil.radix,
        rows_per_label,
    )
