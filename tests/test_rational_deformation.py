from fractions import Fraction as Q
from itertools import product
from random import Random
import pytest
from nextfft_lab.rational_deformation import cyclic3_product, deformed_product


def oracle(a,b,lambdas,r):
    w=1<<len(lambdas)
    out=[[Q(0)]*r for _ in range(w)]
    for i,j in product(range(w),repeat=2):
        c=Q(1)
        for k,v in enumerate(lambdas):
            if (i&j)&(1<<k): c*=v
        for u,v in product(range(r),repeat=2):
            if u+v<r: out[i^j][u+v]+=c*a[i][u]*b[j][v]
    return out


@pytest.mark.parametrize('lam,r',[((-3,),1),((-3,),3),((-3,2),2)])
def test_all_bilinear_basis(lam,r):
    w=1<<len(lam)
    for i,j in product(range(w*r),repeat=2):
        a=[[Q(0)]*r for _ in range(w)]
        b=[[Q(0)]*r for _ in range(w)]
        a[i//r][i%r]=1
        b[j//r][j%r]=1
        assert deformed_product(a,b,lam,r)==oracle(a,b,lam,r)


@pytest.mark.parametrize('lam,r',[((Q(2,3),),2),((-3,2,Q(5,7)),3),((1,1),2)])
def test_dense(lam,r):
    rng=Random(20261127)
    for _ in range(3):
        a,b=([[Q(rng.randrange(-9,10),rng.randrange(1,6)) for _ in range(r)] for _ in range(1<<len(lam))] for _ in range(2))
        assert deformed_product(a,b,lam,r)==oracle(a,b,lam,r)


def test_cyclic3():
    def oracle(a,b):
        return [sum(a[i]*b[(k-i)%3] for i in range(3)) for k in range(3)]
    for i,j in product(range(3),repeat=2):
        a=[int(k==i) for k in range(3)]
        b=[int(k==j) for k in range(3)]
        assert cyclic3_product(a,b)==oracle(a,b)
    a=[Q(2,3),-1,Q(4,7)]; b=[2,Q(-1,3),5]
    assert cyclic3_product(a,b)==oracle(a,b)


def test_rejections():
    for lam,r in [((),1),((0,),1),((1,),0),((1,),4)]:
        with pytest.raises(ValueError): deformed_product([[1],[2]],[[1],[2]],lam,r)
    with pytest.raises(ValueError): cyclic3_product([1],[2])
