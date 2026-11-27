"""Measure the same occupied word with borrowed and dedicated registers."""
import json
from random import Random
from unittest.mock import patch

from . import geometric, occupied

from .bench_repair import environment, measure
from .exact import P
from .fiber_schedule import OccupiedFiberPlan
from .geometric import NewtonPlan


class _DedicatedRegisters:
    def __init__(self, tensor, scratch, axis):
        self.tensor = tensor
        self.scratch = scratch
        self.axis = axis
        self.fiber = 0

    def __len__(self):
        return self.axis.word.register_count

    def __getitem__(self, i):
        if i < self.axis.length:
            return self.tensor[self.axis.address(self.fiber, i)]
        return self.scratch[i - self.axis.length]

    def __setitem__(self, i, value):
        if i < self.axis.length:
            self.tensor[self.axis.address(self.fiber, i)] = value
        else:
            self.scratch[i - self.axis.length] = value


class _Counted:
    def __init__(self, values):
        self.values = values
        self.reads = self.writes = 0

    def __len__(self):
        return len(self.values)

    def __getitem__(self, i):
        self.reads += 1
        return self.values[i]

    def __setitem__(self, i, value):
        self.writes += 1
        self.values[i] = value


def _dedicated(plan, data, scratch):
    for axis in plan.axes:
        view = _DedicatedRegisters(data, scratch, axis)
        for view.fiber in range(axis.fibers):
            axis.word.apply(view)


def _ordinary(plan, data, ordinary_plans):
    for axis, row_plan in zip(plan.axes, ordinary_plans):
        for fiber in range(axis.fibers):
            values = [data[axis.address(fiber, j)] for j in range(axis.length)]
            for j, value in enumerate(row_plan.apply(values)):
                data[axis.address(fiber, j)] = value


def run():
    seed, repeats = 20261127, 5
    rng = Random(seed)
    cases = []
    for shape, indices in (((8, 8), (0, 1)), ((13, 4), (1,))):
        ratios = (3, 5)
        source = [rng.randrange(1, P) for _ in range(shape[0] * shape[1])]
        plan = OccupiedFiberPlan.build(shape, ratios, indices)
        ordinary = [NewtonPlan.build(shape[i], ratios[i]) for i in indices]
        count = max(axis.word.register_count - axis.length for axis in plan.axes)
        dirty = [rng.randrange(1, P) for _ in range(count)]
        x, y, z = (_Counted(source[:]) for _ in range(3))
        scratch = _Counted(dirty[:])
        with patch.object(occupied, "_ntt_at", wraps=occupied._ntt_at) as transforms:
            plan.apply(x)
            borrowed_ntts = transforms.call_count
            transforms.reset_mock()
            _dedicated(plan, y, scratch)
            dedicated_ntts = transforms.call_count
        with patch.object(geometric, "radix2", wraps=geometric.radix2) as transforms:
            _ordinary(plan, z, ordinary)
            ordinary_ntts = transforms.call_count
        assert borrowed_ntts == dedicated_ntts == plan.ntt_count
        assert ordinary_ntts == 4 * sum(a.fibers for a in plan.axes)
        assert x.values == y.values == z.values and scratch.values == dirty

        cases.append({
            "shape": shape, "axis_indices": indices, "groups": [list(a.groups()) for a in plan.axes],
            "occupied_setup": measure(lambda: OccupiedFiberPlan.build(shape, ratios, indices), repeats),
            "ordinary_setup": measure(lambda: [NewtonPlan.build(shape[i], ratios[i]) for i in indices], repeats),
            "borrowed": {**measure(lambda: plan.apply(source[:]), repeats), "extra_registers": 0,
                         "ntts": borrowed_ntts, "payload_reads": x.reads, "payload_writes": x.writes},
            "dedicated": {**measure(lambda: _dedicated(plan, source[:], dirty[:]), repeats),
                          "extra_registers": count, "ntts": dedicated_ntts,
                          "payload_reads": y.reads, "payload_writes": y.writes,
                          "scratch_reads": scratch.reads, "scratch_writes": scratch.writes},
            "ordinary": {**measure(lambda: _ordinary(plan, source[:], ordinary), repeats),
                         "ntts": ordinary_ntts,
                         "payload_reads": z.reads, "payload_writes": z.writes},
        })
    return {"environment": environment(), "seed": seed, "repeats": repeats, "cases": cases}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
