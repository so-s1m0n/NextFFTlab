"""Classical transforms on the group (Z/2)^k over F_998244353."""
from .exact import P


def _binary_row(values):
    row = [int(value) % P for value in values]
    if not row or len(row) & (len(row) - 1):
        raise ValueError("Walsh transform requires a positive power of two")
    return row


def direct_walsh(values, inverse=False):
    """Apply the sign character matrix in natural binary index order."""
    row = _binary_row(values)
    result = [
        sum(-value if (index & frequency).bit_count() % 2 else value
            for index, value in enumerate(row)) % P
        for frequency in range(len(row))
    ]
    if inverse:
        scale = pow(len(row), -1, P)
        return [value * scale % P for value in result]
    return result


def walsh(values, inverse=False):
    """Iterative in-place butterflies on a private copy of the input row."""
    row = _binary_row(values)
    stride = 1
    while stride < len(row):
        for start in range(0, len(row), 2 * stride):
            for left in range(start, start + stride):
                right = left + stride
                first, second = row[left], row[right]
                row[left] = (first + second) % P
                row[right] = (first - second) % P
        stride *= 2
    if inverse:
        scale = pow(len(row), -1, P)
        row = [value * scale % P for value in row]
    return row
