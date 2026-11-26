"""Materialized L=q=2, f=1 binary template without a recursion saving."""
from dataclasses import dataclass

from .binary_kernel import binary_endpoint
from .binary_repair import compile_binary_repair
from .binary_routing import BinarySquareRouting, compile_binary_square_routing
from .exact import P


@dataclass(frozen=True)
class BinarySquareTemplate:
    routing: BinarySquareRouting
    matrices: tuple
    stages: int

    @property
    def rows_per_label(self):
        return len(self.matrices[0])

    def apply(self, labels, inverse=False):
        """Apply the matrix-root predictor through shared pencil routing."""
        if len(labels) != 4 or any(len(rows) != self.rows_per_label for rows in labels):
            raise ValueError("template needs four blocks of independent rows")
        current = [[binary_endpoint(row, 3, 1, 1) for row in rows] for rows in labels]
        for _ in range(self.stages):
            current = self.routing.apply(current, self.matrices[1:], self.matrices[0])
        out = [[binary_endpoint(row, 3, 1, 1, output=True) for row in rows] for rows in current]
        if inverse:
            scale = pow(256, -1, P)
            out = [[[value * scale % P for value in row] for row in rows] for rows in out]
        return out


def compile_binary_square_template():
    plan = compile_binary_repair(3)
    if plan.repair.check_count:
        raise ValueError("the bounded template only supports zero exceptions")
    width = plan.repair.width
    matrices = [[[0] * width for _ in range(width)] for _ in range(4)]
    start = 0
    for pencil in plan.pencils:
        for source, transitions in enumerate(pencil.columns, start=start):
            for destination, coefficients in transitions:
                for matrix, coefficient in zip(matrices, coefficients):
                    index = start + destination
                    matrix[index][source] = (matrix[index][source] + coefficient) % P
        start += pencil.rows
    return BinarySquareTemplate(
        compile_binary_square_routing(),
        tuple(tuple(tuple(row) for row in matrix) for matrix in matrices),
        plan.pencils[0].radix,
    )
