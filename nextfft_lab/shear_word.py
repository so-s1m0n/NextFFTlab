"""Explicit bounded specialization of layers.tex lem:shear over F_998244353."""
from itertools import islice
from operator import index

from .exact import P
from .walsh import walsh

MAX_N = 1024


def _row(values):
    x = list(islice(values, MAX_N + 1))
    n = len(x)
    if not 1 <= n <= MAX_N or n & (n-1):
        raise ValueError('expected a power-of-two length in 1..1024')
    return [index(v) % P for v in x]


def _tensor_scale(x, a, b):
    j = len(x).bit_length()-1
    coefficients = [pow(a,j-k,P)*pow(b,k,P)%P for k in range(j+1)]
    return [v*coefficients[i.bit_count()]%P for i,v in enumerate(x)]


def tensor_shear_word(values, *, inverse=False):
    """U^(tensor j) using three full Walsh transforms and four diagonals.

    U = [[1,1],[0,1]]. Values are integer field representatives.
    For inverse, conjugate by diag(1,-1)^tensor j.
    No gate-saving Walsh backend or asymptotic bound is implemented.
    """
    x = _row(values)
    if inverse:
        x = _tensor_scale(x,1,-1)
    x = _tensor_scale(x,1,4*pow(5,-1,P)%P)
    x = walsh(x)
    x = _tensor_scale(x,3,-1)
    x = walsh(x)
    x = _tensor_scale(x,2,1)
    x = walsh(x)
    x = _tensor_scale(x,pow(8,-1,P),5*pow(24,-1,P)%P)
    return _tensor_scale(x,1,-1) if inverse else x


def tensor_shear_classical(values, *, inverse=False):
    """Superset zeta / Moebius butterfly for integer field representatives."""
    x = _row(values)
    sign = -1 if inverse else 1
    stride = 1
    while stride < len(x):
        for start in range(0,len(x),2*stride):
            for i in range(start,start+stride):
                x[i] = (x[i]+sign*x[i+stride])%P
        stride *= 2
    return x


def forward_counts(n):
    """Application counts, excluding coefficient setup and indexing."""
    if type(n) is not int or not 1 <= n <= MAX_N or n & (n-1):
        raise ValueError('expected a power-of-two length in 1..1024')
    j = n.bit_length()-1
    return {'classical_adds': n*j//2, 'word_walsh_calls': 3,
            'word_classical_walsh_adds_subtracts': 3*n*j,
            'word_diagonal_entry_updates': 4*n}
