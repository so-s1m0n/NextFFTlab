"""Bounded checks of layers.tex: Newton factorization and occupied workspace.

Classical radix-2 NTT supplies Toeplitz products; no new asymptotic bound.
"""
from dataclasses import dataclass
from .exact import P, radix2, root

MAX_N = 512


def _size(n):
    if type(n) is not int or not 1 <= n <= MAX_N:
        raise ValueError('expected 1 <= n <= 512')


def reciprocal(h):
    """Truncated reciprocal over F_P, quadratic setup."""
    h = tuple(int(x) % P for x in h)
    _size(len(h))
    if not h[0]:
        raise ValueError('noninvertible series')
    r = [pow(h[0], -1, P)]
    for i in range(1, len(h)):
        r.append(-r[0] * sum(h[j] * r[i-j] for j in range(1, i+1)) % P)
    return tuple(r)


@dataclass(frozen=True)
class ToeplitzPlan:
    n: int
    padded: int
    spectrum: tuple

    @classmethod
    def build(cls, column):
        h = tuple(int(x) % P for x in column)
        _size(len(h))
        b = 1 << (2*len(h)-2).bit_length()
        return cls(len(h), b, tuple(radix2(h + (0,)*(b-len(h)))))

    def apply(self, values, upper=False):
        x = list(values)
        if len(x) != self.n:
            raise ValueError('wrong input length')
        if upper:
            x.reverse()
        f = radix2(x + [0]*(self.padded-self.n))
        y = radix2([a*b % P for a,b in zip(f,self.spectrum)], True)[:self.n]
        return y[::-1] if upper else y


def _scale(x, d):
    return [a*b % P for a,b in zip(x,d)]


@dataclass(frozen=True)
class NewtonPlan:
    """V_ij=q^(ij), with distinct nodes, and its interpolation inverse."""
    n: int
    q: int
    H: tuple
    middle: tuple
    Hinv: tuple
    midinv: tuple
    lower: ToeplitzPlan
    reciprocal_lower: ToeplitzPlan

    @classmethod
    def build(cls, n, q):
        _size(n)
        q = int(q) % P
        if not q:
            raise ValueError('q must be nonzero')
        H, c = [1], [1]
        for i in range(1,n):
            H.append(H[-1]*(1-pow(q,i,P)) % P)
            if not H[-1]:
                raise ValueError('geometric nodes are not distinct')
            c.append(-c[-1]*pow(q,i-1,P) % P)
        inv = tuple(pow(h,-1,P) for h in H)
        mid = tuple(_scale(c,inv))
        return cls(n,q,tuple(H),mid,inv,tuple(pow(x,-1,P) for x in mid),
                   ToeplitzPlan.build(inv), ToeplitzPlan.build(reciprocal(inv)))

    def apply(self, values, inverse=False):
        x = list(values)
        if len(x) != self.n:
            raise ValueError('wrong input length')
        if inverse:
            x = self.reciprocal_lower.apply(_scale(x,self.Hinv))
            x = self.reciprocal_lower.apply(_scale(x,self.midinv), upper=True)
            return _scale(x,self.Hinv)
        x = self.lower.apply(_scale(x,self.H), upper=True)
        x = self.lower.apply(_scale(x,self.middle))
        return _scale(x,self.H)


def _block_diagonal(x,z,S,Sinv):
    # Three triangular block shears and a signed swap, rightmost first.
    x,z = [(-v)%P for v in z], list(x)
    x = [(a+b)%P for a,b in zip(x,S.apply(z))]
    z = [(a-b)%P for a,b in zip(z,Sinv.apply(x))]
    x = [(a+b)%P for a,b in zip(x,S.apply(z))]
    return x,z


def occupied_lower(column, values, scratch):
    """Check T plus identity via the paper's commutator and block shears.

    Scratch may contain arbitrary independent values. The Toeplitz backend
    allocates temporary arrays; this is NOT a constant-workspace word.
    """
    h = tuple(int(v)%P for v in column)
    n = len(h)
    _size(n)
    x,z = [int(v)%P for v in values], [int(v)%P for v in scratch]
    if len(x)!=n or len(z)!=n or not h[0]:
        raise ValueError('invertible column and matching arrays required')
    u = root(1 << (2*n-1).bit_length())
    hnorm = _scale(h,[pow(h[0],-1,P)]*n)
    f = [1]
    for i in range(1,n):
        f.append(sum(hnorm[j]*f[i-j] for j in range(1,i+1))*pow((pow(u,i,P)-1)%P,-1,P)%P)
    S,Sinv = ToeplitzPlan.build(f),ToeplitzPlan.build(reciprocal(f))
    d = [pow(u,i,P) for i in range(n)]
    x,z = _block_diagonal(x,z,Sinv,S)
    x = _scale(x,[pow(v,-1,P) for v in d])
    x,z = _block_diagonal(x,z,S,Sinv)
    return _scale(_scale(x,d),[h[0]]*n),z
