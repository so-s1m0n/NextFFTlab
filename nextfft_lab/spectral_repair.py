"""Binary full-rate Hermite repair from repair.tex, lem:hermite-repair."""
from dataclasses import dataclass

from .exact import P
from .walsh import walsh

HALF = pow(2, -1, P)


def _row_map(matrix, rows):
    return [[sum(a * b for a, b in zip(coefficients, column)) % P
             for column in zip(*rows)] for coefficients in matrix]


def _inverse_vandermonde(nodes):
    # Rows are coefficient vectors of the node-specific Lagrange basis.
    rows = []
    for index, node in enumerate(nodes):
        coefficients = [1]
        scale = 1
        for j, other in enumerate(nodes):
            if index == j:
                continue
            coefficients = [(before - other * after) % P for before, after in
                            zip([0] + coefficients, coefficients + [0])]
            scale = scale * (node - other) % P
        rows.append([value * pow(scale, -1, P) % P for value in coefficients])
    return tuple(tuple(row) for row in rows)


def _binary_quotient_at(multiplier, target):
    # g(y) - z = (y-z)^2 * (-(y+2z)/2) for z^2=1, including y=z.
    return -(multiplier + 2 * target) * HALF % P


@dataclass(frozen=True)
class FrequencyRepair:
    target: int
    exceptional: tuple
    inverse: tuple
    quotients: tuple

    def evaluate(self, predicted_checks, input_checks):
        errors = [
            (predicted - self.target * original) % P
            for predicted, original in zip(predicted_checks, input_checks)
        ]
        weighted = [
            quotient * sum(value * error for value, error in zip(row, errors)) % P
            for quotient, row in zip(self.quotients, self.inverse)
        ]
        lift = [
            sum(value * error for value, error in zip(column, weighted)) % P
            for column in zip(*self.inverse)
        ]
        lift.extend([0] * (len(errors) - len(lift)))
        return lift, [self.target * value % P for value in lift]


def frequency_repair(nodes, target, exceptional, multipliers):
    """Compile one table column from public spectral multipliers and positions."""
    nodes = tuple(node % P for node in nodes)
    target %= P
    exceptional, multipliers = tuple(exceptional), tuple(multipliers)
    if target * target % P != 1:
        raise ValueError("binary target must be a sign")
    if len(set(nodes)) != len(nodes):
        raise ValueError("Vandermonde nodes must be distinct modulo P")
    if (len(exceptional) != len(multipliers) or len(set(exceptional)) != len(exceptional)
            or any(not 0 <= index < len(nodes) for index in exceptional)):
        raise ValueError("invalid exceptional positions")
    return FrequencyRepair(
        target, exceptional, _inverse_vandermonde(tuple(nodes[i] for i in exceptional)),
        tuple(_binary_quotient_at(multiplier, target) for multiplier in multipliers),
    )


@dataclass(frozen=True)
class RepairPlan:
    checks: tuple
    lift: tuple
    frequencies: tuple
    width: int

    @property
    def check_count(self):
        return len(self.checks)

    def apply(self, batch, predictor):
        """Run the predictor and convert only the two groups of check rows."""
        batch = tuple(tuple(int(value) % P for value in row) for row in batch)
        if len(batch) != self.width or any(len(row) != len(self.frequencies) for row in batch):
            raise ValueError("repair batch shape mismatch")
        predicted = predictor(batch)
        if not self.check_count:
            return predicted

        predicted_checks = [walsh(row) for row in _row_map(self.checks, predicted)]
        input_checks = [walsh(row) for row in _row_map(self.checks, batch)]
        lift_spectra, target_lift_spectra = [], []
        for table, pcol, xcol in zip(self.frequencies, zip(*predicted_checks), zip(*input_checks)):
            lift, target_lift = table.evaluate(pcol, xcol)
            lift_spectra.append(lift)
            target_lift_spectra.append(target_lift)
        z = _row_map(self.lift, [walsh(row, inverse=True) for row in zip(*lift_spectra)])
        fz = _row_map(self.lift, [walsh(row, inverse=True) for row in zip(*target_lift_spectra)])
        pz = predictor(z)
        cubed = predictor(predictor(predicted))
        return [
            [(HALF * (3 * p - p3) - p_z + f_z) % P for p, p3, p_z, f_z in zip(*rows)]
            for rows in zip(predicted, cubed, pz, fz)
        ]


def compile_repair(nodes, frequencies):
    nodes = tuple(node % P for node in nodes)
    frequencies = tuple(frequencies)
    size = len(frequencies)
    if not nodes or not size or size & (size - 1):
        raise ValueError("repair needs rows and a power-of-two frequency count")
    if len(set(nodes)) != len(nodes):
        raise ValueError("Vandermonde nodes must be distinct modulo P")
    tables = tuple(frequency_repair(nodes, *frequency) for frequency in frequencies)
    check_count = max(len(table.exceptional) for table in tables)
    checks = tuple(tuple(pow(node, power, P) for node in nodes)
                   for power in range(check_count))
    return RepairPlan(checks, tuple(zip(*checks)), tables, len(nodes))
