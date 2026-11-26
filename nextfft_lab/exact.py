"""Exact Fourier transforms over the fixed prime field F_998244353.
Forward convention: sum_j x[j] * w**(jk). Inverse: w^-1 and 1/n.
These are classical algorithms, not the new paper's construction.
"""
P = 998244353
G = 3


def root(n: int, inverse: bool = False) -> int:
    if n < 1 or (P - 1) % n:
        raise ValueError("n must be a positive divisor of p-1")
    w = pow(G, (P - 1) // n, P)
    return pow(w, -1, P) if inverse else w


def direct(values, inverse=False):
    a = [int(x) % P for x in values]
    n = len(a)
    w = root(n, inverse)
    result = [sum(x * pow(w, j*k, P) for j, x in enumerate(a)) % P for k in range(n)]
    return [(x * pow(n, -1, P)) % P for x in result] if inverse else result


def radix2(values, inverse=False):
    a = [int(x) % P for x in values]
    n = len(a)
    root(n, inverse)
    if n & (n-1):
        raise ValueError("radix2 requires a power of two")
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            a[i], a[j] = a[j], a[i]
    m = 2
    while m <= n:
        wm = root(m, inverse)
        for start in range(0, n, m):
            w = 1
            for k in range(start, start + m//2):
                u, v = a[k], a[k+m//2] * w % P
                a[k], a[k+m//2] = (u+v) % P, (u-v) % P
                w = w*wm % P
        m *= 2
    if inverse:
        inv = pow(n, -1, P)
        a = [x*inv % P for x in a]
    return a


def bluestein(values, inverse=False):
    """Classical chirp identity plus radix-2 NTT convolution.
    Requires a primitive 2n-th root and enough radix-2 padding in F_p.
    This is a building-block check, not a reproduction of the new bound.
    """
    a = [int(x) % P for x in values]
    n = len(a)
    z = root(2*n, inverse)
    m = 1 << (2*n-2).bit_length()
    root(m)
    chirp = [pow(z, j*j, P) for j in range(n)]
    u = [x*c % P for x,c in zip(a,chirp)] + [0]*(m-n)
    v = [0]*m
    v[0] = 1
    for j in range(1,n):
        v[j] = v[-j] = pow(chirp[j], -1, P)
    c = radix2([x*y % P for x,y in zip(radix2(u),radix2(v))], inverse=True)
    out = [c[j]*chirp[j] % P for j in range(n)]
    return [x*pow(n,-1,P)%P for x in out] if inverse else out


def convolution(a,b):
    a,b = list(a),list(b)
    if not a or not b:
        return []
    n = len(a)+len(b)-1
    m = 1 << (n-1).bit_length()
    x = radix2(a+[0]*(m-len(a)))
    y = radix2(b+[0]*(m-len(b)))
    return radix2([u*v % P for u,v in zip(x,y)],True)[:n]
