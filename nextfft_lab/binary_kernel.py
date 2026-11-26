"""Bounded ordinary-coordinate identities from kernel.tex."""
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations, product
from math import comb, prod

from .exact import P
from .spectral_repair import HALF


def _sign(exponent):
    return 1 - 2 * (exponent & 1)


def _shape(m, auxiliary, columns):
    if m < 3 or m % 2 == 0 or auxiliary < 0 or columns < 1:
        raise ValueError("odd m >= 3, nonnegative auxiliary axes and positive columns required")
    half_bits = (m + auxiliary) * columns
    if half_bits > 6:
        raise ValueError("component experiment is limited to 4096 entries")
    return half_bits


def _pair_query(row, position, half_bits):
    first = 1 << position
    second = first << half_bits
    masks = (0, first, second, first | second)
    out = row.copy()
    for base in range(len(row)):
        if base & masks[-1]:
            continue
        source = [row[base | mask] for mask in masks]
        total = sum(source)
        for k, mask in enumerate(masks):
            # Entry from (x,y) to (s,t) is (-1)^((x-s)(t-y))/2.
            opposite = k ^ 3
            out[base | mask] = HALF * (total - 2 * source[opposite]) % P
    return out


def binary_query(values, m, auxiliary, columns, query):
    """Apply one Q_j using its tensor-product ordinary kernel."""
    half_bits = _shape(m, auxiliary, columns)
    row = [int(value) % P for value in values]
    if len(row) != 1 << (2 * half_bits) or not 0 <= query < m:
        raise ValueError("row size or query index mismatch")
    for axis in (query, *range(m, m + auxiliary)):
        for column in range(columns):
            row = _pair_query(row, axis * columns + column, half_bits)
    return row


def binary_endpoint(values, m, auxiliary, columns, output=False):
    """Input phase or output phase, half swap and scale for the query product."""
    half_bits = _shape(m, auxiliary, columns)
    row = [int(value) % P for value in values]
    half_size = 1 << half_bits
    if len(row) != half_size * half_size:
        raise ValueError("row size mismatch")
    corrected = [0] * len(row)
    for index, value in enumerate(row):
        x, y = index % half_size, index // half_size
        if output:
            corrected[y | (x << half_bits)] = value * half_size * _sign((x & y).bit_count()) % P
        else:
            corrected[index] = value * _sign((x & y).bit_count()) % P
    return corrected


@dataclass(frozen=True)
class Rectangle:
    sources: tuple
    destinations: tuple
    weight: int
    charged: bool


def _first_difference(alphabet):
    pairs = []
    suffix_bits = alphabet.bit_length() - 1
    for remaining in range(suffix_bits):
        size = 1 << remaining
        for start in range(0, alphabet, 2 * size):
            left = tuple(range(start, start + size))
            right = tuple(range(start + size, start + 2 * size))
            pairs.extend(((left, right), (right, left)))
    return tuple(pairs)


def binary_rectangles(length, alphabet):
    """Construct the bounded weighted rectangle identity and its Gram rows."""
    if not 2 <= length <= 6 or not 2 <= alphabet <= 64 or alphabet & (alphabet - 1):
        raise ValueError("length must be 2..6 and alphabet a power of two")
    if alphabet**length > 64:
        raise ValueError("routing experiment is limited to 64 labels")
    labels = tuple(product(range(alphabet), repeat=length))
    label_index = {label: index for index, label in enumerate(labels)}
    t = length // 2
    weights = [prod(Fraction(2 * h - k, 2 * h) for h in range(1, t + 1))
               for k in range(length + 1)]
    weights = [value.numerator * pow(value.denominator, -1, P) % P for value in weights]
    charged_weights = []
    rectangles = []
    for j in range(t + 1):
        value = (weights[length - j] - sum(comb(j, k) * weight
                                          for k, weight in enumerate(charged_weights))) % P
        charged_weights.append(value)
        if value:
            for coordinates in combinations(range(length), j):
                for common in product(range(alphabet), repeat=j):
                    block = tuple(index for index, label in enumerate(labels)
                                  if tuple(label[axis] for axis in coordinates) == common)
                    rectangles.append(Rectangle(block, block, value, True))

    equal = tuple(((letter,), (letter,)) for letter in range(alphabet))
    different = _first_difference(alphabet)
    for distance in range(1, length + 1, 2):
        for coordinates in combinations(range(length), distance):
            unequal = set(coordinates)
            choices = [different if axis in unequal else equal for axis in range(length)]
            for by_axis in product(*choices):
                left, right = zip(*by_axis)
                sources = tuple(label_index[label] for label in product(*left))
                destinations = tuple(label_index[label] for label in product(*right))
                rectangles.append(Rectangle(sources, destinations, -weights[distance] % P, False))

    gram = tuple(sum((1 << j) for j, right in enumerate(labels)
                     if sum(a != b for a, b in zip(left, right)) % 2 == 0) for left in labels)
    return gram, tuple(rectangles)


def binary_rank(rows):
    pivots = {}
    for row in rows:
        while row:
            pivot = row.bit_length()
            if pivot not in pivots:
                pivots[pivot] = row
                break
            row ^= pivots[pivot]
    return len(pivots)
