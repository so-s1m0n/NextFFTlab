"""Exact rational small-circuit witnesses and safe import of arithmetic SLPs."""
from dataclasses import dataclass
from fractions import Fraction
import re

from .exact import P
from .linear_circuit import LinearCircuit, _signed, verify_walsh

MAX_INPUTS = 16
MAX_OPS = 128
NAME = re.compile(r"[A-Za-z][A-Za-z0-9]*")
TERM = re.compile(r"([+-]?)(?:(\d+(?:/\d+)?)\*)?([A-Za-z][A-Za-z0-9]*)")


@dataclass(frozen=True)
class RationalCircuit:
    inputs: int
    ops: tuple
    outputs: tuple
    scale: Fraction

    def __post_init__(self):
        if self.inputs not in (4, 8, 16) or len(self.ops) > MAX_OPS or len(self.outputs) != self.inputs:
            raise ValueError("rational circuit exceeds small-witness limits")
        if not self.scale or any(not 0 <= wire < self.inputs + len(self.ops) for wire in self.outputs):
            raise ValueError("invalid output wire or common scale")
        if any(not a or not 0 <= u < i or not 0 <= v < i or (b == 0) != (u == v)
               for i, (a, u, b, v) in enumerate(self.ops, self.inputs)):
            raise ValueError("invalid rational operation")

    def evaluate(self, row):
        wires = list(map(Fraction, row))
        if len(wires) != self.inputs:
            raise ValueError("wrong rational input size")
        for a, u, b, v in self.ops:
            value = a * wires[u]
            if b:
                value += b * wires[v]
            wires.append(value)
        return [wires[i] for i in self.outputs]

    def verify_rational(self):
        for column in range(self.inputs):
            result = self.evaluate(int(i == column) for i in range(self.inputs))
            if any(value != self.scale * (-1)**((i & column).bit_count())
                   for i, value in enumerate(result)):
                return False
        return True

    def as_field_circuit(self):
        def residue(value):
            value = Fraction(value)
            return _signed(value.numerator * pow(value.denominator, -1, P))
        return LinearCircuit(
            self.inputs,
            tuple((residue(a), u, residue(b), v) for a, u, b, v in self.ops),
            tuple((i, residue(1 / self.scale)) for i in self.outputs),
        )

    def verify_field(self):
        return verify_walsh(self.as_field_circuit())

    def cost(self):
        def literal(q):
            q = Fraction(q)
            return q.numerator, q.denominator

        count = self.as_field_circuit().counts()
        # Count rational arithmetic directly. A coefficient could reduce to
        # +/-1 modulo P and must still be charged in the rational model.
        binary = sum(bool(b) for _, _, b, _ in self.ops)
        mult = sum(abs(c) != 1 for a, _, b, _ in self.ops for c in ((a, b) if b else (a,)))
        neg = sum((a < 0 and b < 0) or (not b and a == -1) for a, _, b, _ in self.ops)
        restore = self.inputs if self.scale != 1 else 0
        return {
            "gates": binary, "adds_subtracts": binary, "multiplications": mult,
            "negations": neg, "scaled_arithmetic": binary + mult + neg,
            "restoration_operations": restore, "common_scale": literal(self.scale),
            "binary_depth": count["binary_depth"], "wire_depth": count["wire_depth"],
            "peak_live_wires": count["peak_live_wires_with_last_use_reuse"],
        }

    def to_dict(self):
        return {
            "schema": "nextfft-rational-circuit-v1", "inputs": self.inputs, "scale": str(self.scale),
            "ops": [[str(a), u, str(b), v] for a, u, b, v in self.ops],
            "outputs": list(self.outputs),
        }


    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or data.get("schema") != "nextfft-rational-circuit-v1":
            raise ValueError("unsupported rational circuit schema")
        rows, outputs = data.get("ops"), data.get("outputs")
        if (not isinstance(rows, list) or len(rows) > MAX_OPS
                or not isinstance(outputs, list) or len(outputs) > MAX_INPUTS
                or any(type(wire) is not int for wire in outputs)):
            raise ValueError("invalid rational circuit arrays")

        def read(value):
            if not isinstance(value, str) or len(value) > 64 or not re.fullmatch(r"-?\d+(?:/\d+)?", value):
                raise ValueError("invalid rational literal")
            return Fraction(value)

        ops = []
        for row in rows:
            if not isinstance(row, list) or len(row) != 4 or any(type(row[i]) is not int for i in (1, 3)):
                raise ValueError("invalid rational circuit operation")
            a, u, b, v = row
            ops.append((read(a), u, read(b), v))
        return cls(data.get("inputs"), tuple(ops), tuple(outputs), read(data.get("scale")))

def parse_slp(text, inputs, scale=Fraction(1)):
    """Read listed assignments as data. The parser never evaluates source text."""
    if len(text) > 24_000 or inputs not in (4, 8, 16):
        raise ValueError("SLP outside import bounds")
    names = {f"x{i}": i for i in range(inputs)}
    outputs = {}
    ops = []
    for line in text.splitlines():
        line = "".join(line.partition("#")[0].split())
        if not line:
            continue
        dest, sep, expr = line.partition("=")
        if not sep or not NAME.fullmatch(dest) or dest in names:
            raise ValueError("invalid or duplicate SLP assignment")
        terms = list(TERM.finditer(expr))
        if (len(terms) not in (1, 2) or "".join(t[0] for t in terms) != expr
                or (len(terms) == 2 and not terms[1][1])
                or any(term[3] not in names for term in terms)):
            raise ValueError("invalid SLP expression")
        pieces = [(Fraction(t[2] or "1") * (-1 if t[1] == "-" else 1), names[t[3]]) for t in terms]
        a, u = pieces[0]
        if len(pieces) == 1 and a == 1:
            index = u
        else:
            b, v = pieces[1] if len(pieces) == 2 else (0, u)
            index = inputs + len(ops)
            ops.append((a, u, b, v))
        names[dest] = index
        if re.fullmatch(r"y\d+", dest):
            slot = int(dest[1:])
            if slot in outputs:
                raise ValueError("duplicate SLP output")
            outputs[slot] = index
    if set(outputs) != set(range(inputs)):
        raise ValueError("missing or out-of-range SLP outputs")
    return RationalCircuit(inputs, tuple(ops), tuple(outputs[i] for i in range(inputs)), Fraction(scale))
