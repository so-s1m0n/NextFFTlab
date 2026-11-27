"""Bounded serial execution of layers.tex, up:fibers, on an occupied tensor."""
from dataclasses import dataclass
from math import prod

from .occupied import OccupiedNewton

MAX_TENSOR_ENTRIES = 512
MAX_AXIS_APPLICATIONS = 128


@dataclass(frozen=True)
class FiberAxis:
    word: OccupiedNewton
    length: int
    stride: int
    fibers: int
    minimum_group: int

    def address(self, fiber, coordinate):
        tile, lane = divmod(fiber, self.stride)
        return (tile * self.length + coordinate) * self.stride + lane

    def groups(self):
        start = 0
        while self.fibers - start >= 2 * self.minimum_group:
            yield start, self.minimum_group
            start += self.minimum_group
        yield start, self.fibers - start


class _BorrowedRegisters:
    def __init__(self, tensor, axis, start, count):
        self.tensor = tensor
        self.axis = axis
        self.start = start
        self.count = count
        self.offset = 0

    def __len__(self):
        return self.axis.word.register_count

    def _address(self, index):
        block, coordinate = divmod(index, self.axis.length)
        fiber = self.start + (self.offset + block) % self.count
        return self.axis.address(fiber, coordinate)

    def __getitem__(self, index):
        return self.tensor[self._address(index)]

    def __setitem__(self, index, value):
        self.tensor[self._address(index)] = value


@dataclass(frozen=True)
class OccupiedFiberPlan:
    """Precomputed axis words and scheduler for a row-major residue tensor."""

    shape: tuple
    axes: tuple

    @classmethod
    def build(cls, shape, ratios, axis_indices=None):
        shape, ratios = tuple(shape), tuple(ratios)
        if (not shape or len(shape) != len(ratios)
                or any(type(n) is not int or n < 2 for n in shape)
                or prod(shape) > MAX_TENSOR_ENTRIES):
            raise ValueError("expected matching ratios and a tensor of at most 512 entries")
        indices = tuple(range(len(shape))) if axis_indices is None else tuple(axis_indices)
        if (not indices or any(type(i) is not int or not 0 <= i < len(shape) for i in indices)
                or len(set(indices)) != len(indices)):
            raise ValueError("expected distinct valid axis indices")
        volume = prod(shape)
        if sum(volume // shape[i] for i in indices) > MAX_AXIS_APPLICATIONS:
            raise ValueError("too many axis word applications")
        axes = []
        for i in indices:
            n = shape[i]
            word = OccupiedNewton.build(n, ratios[i])
            count = volume // n
            group = (word.register_count + n - 1) // n
            if count < group:
                raise ValueError("too few neighboring fibers to hold one occupied word")
            axes.append(FiberAxis(word, n, prod(shape[i + 1:]), count, group))
        return cls(shape, tuple(axes))

    @property
    def ntt_count(self):
        return 192 * sum(axis.fibers for axis in self.axes)

    def apply(self, tensor, *, inverse=False):
        """Overwrite selected axes in place on canonical integer residues 0 <= x < P."""
        if len(tensor) != prod(self.shape):
            raise ValueError("wrong tensor size")
        axes = reversed(self.axes) if inverse else self.axes
        for axis in axes:
            for start, count in axis.groups():
                registers = _BorrowedRegisters(tensor, axis, start, count)
                for offset in range(count):
                    registers.offset = offset
                    axis.word.apply(registers, inverse=inverse)
