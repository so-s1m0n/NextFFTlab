"""Finite-field straight-line circuits with explicit scalar arithmetic."""
from dataclasses import dataclass

from .exact import P

MAX_INPUTS = 512
MAX_OPS = 8192


def _signed(value):
    value %= P
    return value if value <= P // 2 else value - P


def _scale(value, coefficient):
    if coefficient == 1:
        return value
    if coefficient == -1:
        return -value
    return coefficient * value


@dataclass(frozen=True)
class LinearCircuit:
    inputs: int
    # (a, u, b, v) evaluates a*u+b*v. Unary scaling uses b=0 and v=u.
    ops: tuple
    outputs: tuple

    def __post_init__(self):
        if type(self.inputs) is not int or not 1 <= self.inputs <= MAX_INPUTS:
            raise ValueError("unsupported input count")
        if len(self.ops) > MAX_OPS or len(self.outputs) != self.inputs:
            raise ValueError("circuit size outside supported bounds")
        for i, (a, u, b, v) in enumerate(self.ops, self.inputs):
            if (any(type(x) is not int for x in (a, u, b, v)) or not 0 <= u < i
                    or not 0 <= v < i or not a or _signed(a) != a or _signed(b) != b
                    or (b == 0) != (u == v)):
                raise ValueError("invalid linear operation or forward wire reference")
        for wire, scale in self.outputs:
            if (type(wire) is not int or type(scale) is not int
                    or not 0 <= wire < self.inputs + len(self.ops) or not scale
                    or _signed(scale) != scale):
                raise ValueError("invalid output wire or scale")

    def evaluate(self, values):
        wires = [int(x) % P for x in values]
        if len(wires) != self.inputs:
            raise ValueError("wrong circuit input length")
        for a, u, b, v in self.ops:
            if b == 0:
                value = _scale(wires[u], a)
            else:
                left = _scale(wires[u], abs(a))
                right = _scale(wires[v], abs(b))
                if a < 0:
                    value = right - left if b > 0 else -(left + right)
                else:
                    value = left - right if b < 0 else left + right
            wires.append(value % P)
        return [wires[wire] if scale == 1 else _scale(wires[wire], scale) % P
                for wire, scale in self.outputs]

    def counts(self):
        depth = [0] * self.inputs
        physical_depth = [0] * self.inputs
        fanout = [0] * (self.inputs + len(self.ops))
        gates = multiplications = negations = 0
        for a, u, b, v in self.ops:
            fanout[u] += 1
            if b:
                fanout[v] += 1
                gates += 1
                depth.append(1 + max(depth[u], depth[v]))
                physical_depth.append(1 + max(physical_depth[u], physical_depth[v]))
                negations += int(a < 0 and b < 0)
                multiplications += int(abs(a) != 1) + int(abs(b) != 1)
            else:
                depth.append(depth[u])
                physical_depth.append(physical_depth[u] + int(a != 1))
                negations += int(a == -1)
                multiplications += int(abs(a) != 1)
        for wire, scale in self.outputs:
            fanout[wire] += 1
            negations += int(scale == -1)
            multiplications += int(abs(scale) != 1)

        remaining = fanout.copy()
        live = sum(bool(fanout[i]) for i in range(self.inputs))
        peak = live
        for i, (_, u, b, v) in enumerate(self.ops, self.inputs):
            for source in (u, v) if b else (u,):
                remaining[source] -= 1
                live -= int(remaining[source] == 0)
            live += int(bool(fanout[i]))
            peak = max(peak, live)
        return {
            "binary_gates": gates,
            "adds_subtracts": gates,
            "scalar_multiplications": multiplications,
            "unary_negations": negations,
            "modular_reductions": self.inputs + len(self.ops) + sum(scale != 1 for _, scale in self.outputs),
            "binary_depth": max(depth[i] for i, _ in self.outputs),
            "wire_depth": max(physical_depth[i] + int(scale != 1) for i, scale in self.outputs),
            "max_fanout_with_outputs": max(fanout),
            "peak_live_wires_with_last_use_reuse": peak,
            "eager_wire_slots": len(fanout),
        }

    def to_dict(self):
        return {
            "schema": "nextfft-linear-circuit-v1", "field": P, "inputs": self.inputs,
            "ops": [list(op) for op in self.ops], "outputs": [list(output) for output in self.outputs],
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or data.get("schema") != "nextfft-linear-circuit-v1" or data.get("field") != P:
            raise ValueError("unsupported circuit schema or field")
        ops, outputs = data.get("ops"), data.get("outputs")
        if (not isinstance(ops, list) or len(ops) > MAX_OPS
                or not isinstance(outputs, list) or len(outputs) > MAX_INPUTS
                or any(not isinstance(op, list) or len(op) != 4 for op in ops)
                or any(not isinstance(out, list) or len(out) != 2 for out in outputs)):
            raise ValueError("invalid circuit arrays")
        return cls(data.get("inputs"), tuple(map(tuple, ops)), tuple(map(tuple, outputs)))


def _validate_walsh_size(size):
    if type(size) is not int or not 1 <= size <= MAX_INPUTS or size & (size - 1):
        raise ValueError("expected a supported power-of-two Walsh size")


def verify_walsh(circuit):
    """Check every column against the character formula."""
    _validate_walsh_size(circuit.inputs)
    basis = [0] * circuit.inputs
    for k in range(circuit.inputs):
        basis[k] = 1
        expected = [P - 1 if (k & j).bit_count() % 2 else 1 for j in range(circuit.inputs)]
        if circuit.evaluate(basis) != expected:
            return False
        basis[k] = 0
    return True


def butterfly_circuit(size):
    _validate_walsh_size(size)
    ops = []
    wires = list(range(size))
    for bit in range(size.bit_length() - 1):
        step = 1 << bit
        for i in range(size):
            if not i & step:
                j = i | step
                u, v = wires[i], wires[j]
                wires[i], wires[j] = size + len(ops), size + len(ops) + 1
                ops.extend(((1, u, 1, v), (1, u, -1, v)))
    return LinearCircuit(size, tuple(ops), tuple((wire, 1) for wire in wires))


def tensor_walsh_circuit(block, size):
    """Apply the block along disjoint bit groups, deferring its common scale."""
    _validate_walsh_size(size)
    _validate_walsh_size(block.inputs)
    if block.inputs < 2 or block.inputs > size:
        raise ValueError("block dimension outside supported range")
    common_scale = block.outputs[0][1]
    if any(scale != common_scale for _, scale in block.outputs):
        raise ValueError("block outputs must have one common scale")
    ops = []
    wires = list(range(size))
    stride = 1
    scale = 1
    while stride < size:
        layer = block if stride * block.inputs <= size else butterfly_circuit(2)
        radix = layer.inputs
        for start in range(0, size, stride * radix):
            for i in range(start, start + stride):
                mapping = [wires[i + j * stride] for j in range(radix)]
                for a, u, b, v in layer.ops:
                    mapping.append(size + len(ops))
                    ops.append((a, mapping[u], b, mapping[v]))
                for j, (wire, _) in enumerate(layer.outputs):
                    wires[i + j * stride] = mapping[wire]
        scale = _signed(scale * layer.outputs[0][1])
        stride *= radix
    return LinearCircuit(size, tuple(ops), tuple((wire, scale) for wire in wires))
