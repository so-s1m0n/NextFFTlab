"""Bounded rational checks of packing.tex, descent-prime/deform.

Only width-two binomial axes; exact Fraction jets and classical Walsh.
No fast-circuit, general prime-axis or practical speed claim.
"""
from fractions import Fraction as Q
from math import comb


def _mul(a, b, n):
    return [sum((a[j]*b[i-j] for j in range(max(0, i-len(b)+1), min(i+1,len(a)))), Q(0)) for i in range(n)]


def _shift(a, c, n):
    return [sum((a[j]*comb(j,i)*c**(j-i) for j in range(i,len(a))), Q(0)) for i in range(n)]


def _unit(c, exponent, n):
    """(1+c*z)^exponent modulo z^n, over Q."""
    out = [Q(1)]
    for k in range(1,n):
        out.append(out[-1]*(exponent-k+1)*c/k)
    return out


def _walsh(rows, inverse=False):
    rows = [list(row) for row in rows]
    w = len(rows)
    bit = 1
    while bit < w:
        for i in range(w):
            if not i & bit:
                x,y = rows[i],rows[i|bit]
                rows[i] = [a+b for a,b in zip(x,y)]
                rows[i|bit] = [a-b for a,b in zip(x,y)]
        bit *= 2
    return [[v/w for v in row] for row in rows] if inverse else rows


def deformed_product(left, right, lambdas, r):
    """Product in Q[z]/z^r [Y_i]/(Y_i^2-lambda_i), d=1..3.

    Rows are monomial-mask indexed; each row holds r jet coefficients.
    Lift at t=1, transform at t=0, recover polynomial, return to t=1.
    """
    d = len(lambdas)
    if not 1 <= d <= 3 or type(r) is not int or not 1 <= r <= 3:
        raise ValueError('supported d,r in 1..3')
    lam = tuple(Q(x) for x in lambdas)
    w = 1 << d
    if not all(lam) or len(left)!=w or len(right)!=w or any(len(row)!=r for row in (*left,*right)):
        raise ValueError('nonzero lambdas and matching jet arrays required')
    H = 2*r+d

    def scale(mask, endpoint, exponent, n):
        out = [Q(1)]+[Q(0)]*(n-1)
        for i,v in enumerate(lam):
            if mask & (1<<i):
                c = v-1 if endpoint==0 else (v-1)/v
                out = _mul(out,_unit(c,exponent,n),n)
        return out

    def lift(rows):
        out = []
        for mask,row in enumerate(rows):
            a = _mul(list(map(Q,row)),scale(mask,1,Q(-1,2),r),r)
            a = _shift(a,-1,H)
            out.append(_mul(a,scale(mask,0,Q(1,2),H),H))
        return _walsh(out)

    a,b = lift(left),lift(right)
    products = _walsh([_mul(x,y,H) for x,y in zip(a,b)],inverse=True)
    result = []
    for mask,row in enumerate(products):
        poly = _mul(row,scale(mask,0,Q(-1,2),H),H)
        if any(poly[2*r-1+d:]):
            raise ArithmeticError('degree bound violated')
        result.append(_mul(_shift(poly,1,r),scale(mask,1,Q(1,2),r),r))
    return result


def cyclic3_product(left, right):
    """Q[C3] -> Q x Q[Y]/(Y^2+3), then the deformation path."""
    if len(left)!=3 or len(right)!=3:
        raise ValueError('three scalar coefficients required')
    def split(x):
        a,b,c = map(Q,x)
        return a+b+c, [[a-(b+c)/2],[(b-c)/2]]
    s,a = split(left)
    t,b = split(right)
    s *= t
    (c,), (g,) = deformed_product(a,b,(-3,),1)
    w0 = 2*(s-c)/3
    return [(s+2*c)/3,w0/2+g,w0/2-g]
