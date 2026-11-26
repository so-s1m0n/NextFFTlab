"""Scalar oracle for repair.tex, lem:count-predict; not a fast circuit."""
from math import comb, isqrt
from .exact import P, root


def window(m, ell=2):
    """Integer endpoints of the paper's concentration window."""
    if m < 2 or ell not in (2, 7, 17):
        raise ValueError("m >= 2 and ell in {2,7,17} required")
    r = (2*m-1).bit_length()
    a = 2*m*r
    b = (ell-1)*(isqrt(a-1)+1)
    center2 = m*(ell-1)
    return center2//2-b, (center2+1)//2+b


def _binomial(n, h):
    if n >= 0:
        return comb(n,h) if h <= n else 0
    return (-1)**h * comb(h-n-1,h)


def predict(k, beta, ell=2, bounds=None):
    """Evaluate P_beta at a single frequency in the fixed prime field.

    Returns (predicted multiplier, target multiplier, inside window).
    The integer count is an oracle only: it does not implement pencils.
    A custom window is for toy experiments, not the concentration bound.
    """
    k,beta = tuple(k),tuple(beta)
    if len(k)!=len(beta) or any(not 0<=x<ell for x in k+beta):
        raise ValueError("matching digit vectors required")
    default = window(len(k),ell)
    u,v = default if bounds is None else bounds
    if u>v:
        raise ValueError("invalid window")
    c = sum((x+y)%ell for x,y in zip(k,beta))
    z = root(ell)
    p = pow(z,u-sum(beta),P)*sum(_binomial(c-u,h)*pow(z-1,h,P) for h in range(v-u+1))%P
    return p,pow(z,sum(k),P),u<=c<=v
