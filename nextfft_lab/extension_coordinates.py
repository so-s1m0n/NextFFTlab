"""Bounded grids.tex up:packing check in F_p[t]/(t^2-3).
Classical dense extension DFTs, not the paper's saving circuit.
"""
from .exact import P, root
from .geometric import NewtonPlan, reciprocal

ZERO = (0, 0)
ONE = (1, 0)


def add(x, y):
    return ((x[0]+y[0]) % P, (x[1]+y[1]) % P)


def mul(x, y):
    a, b = x
    c, d = y
    return ((a*c+3*b*d) % P, (a*d+b*c) % P)


def power(x, n):
    if n < 0:
        raise ValueError('nonnegative exponent required')
    y = ONE
    while n:
        if n & 1:
            y = mul(y, x)
        x = mul(x, x)
        n >>= 1
    return y


def auxiliary_root(b):
    """Primitive root of order 3*2^k, 1 <= k <= 4, outside F_p."""
    if b not in (6, 12, 24, 48):
        raise ValueError('unsupported auxiliary length')
    # t^2=3 (3 is a nonsquare); i^2=-1 in the base field.
    # z=(-1+i*t)/2 solves z^2+z+1=0, so has order 3.
    half = pow(2, -1, P)
    z = (-half % P, root(4)*half % P)
    return mul(z, (root(b//3), 0))


def transform(values, inverse=False):
    b = len(values)
    w = auxiliary_root(b)
    if inverse:
        w = power(w, b-1)
    table = [power(w,j) for j in range(b)]
    out = []
    scale = (pow(b,-1,P) if inverse else 1,0)
    for k in range(b):
        total = ZERO
        for j,x in enumerate(values):
            total = add(total,mul(x,table[j*k%b]))
        out.append(mul(total,scale))
    return out


def _toeplitz(x, column, b, upper=False):
    n = len(x)
    if upper:
        x = x[::-1]
    kernel = [(v,0) for v in column]+[ZERO]*(b-n)
    spectrum = transform(kernel)
    y = transform([mul(a,c) for a,c in zip(transform(x+[ZERO]*(b-n)),spectrum)], True)[:n]
    return y[::-1] if upper else y


def _scale(x, d):
    return [mul(v,(c,0)) for v,c in zip(x,d)]


def packed_geometric(first, second, q, *, inverse=False):
    """Pack two independent base-field rows into extension coordinates.

    Newton factors are base-defined, but Toeplitz convolutions require
    a primitive auxiliary root of order divisible by 3, absent in F_p.
    Return both independent results. Bounded reference, dense backend.
    """
    n = len(first)
    if not 2 <= n <= 16 or len(second) != n:
        raise ValueError('two independent equal length rows, 2..16')
    b = next(b for b in (6,12,24,48) if b >= 2*n)
    plan = NewtonPlan.build(n,q)
    x = [(int(a)%P,int(c)%P) for a,c in zip(first,second)]
    if inverse:
        d,m,h = plan.Hinv,plan.midinv,reciprocal(plan.Hinv)
    else:
        d,m,h = plan.H,plan.middle,plan.Hinv
    x = _toeplitz(_scale(x,d),h,b,upper=not inverse)
    x = _toeplitz(_scale(x,m),h,b,upper=inverse)
    x = _scale(x,d)
    return [v[0] for v in x],[v[1] for v in x]
