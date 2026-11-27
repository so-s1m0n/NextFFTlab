from random import Random
import pytest
from nextfft_lab.exact import P, root
from nextfft_lab.extension_coordinates import ONE, auxiliary_root, power, transform, packed_geometric


def oracle(x,q):
    return [sum(a*pow(q,i*j,P) for j,a in enumerate(x))%P for i in range(len(x))]


@pytest.mark.parametrize('b',[6,12,24,48])
def test_extension_root(b):
    assert pow(3,(P-1)//2,P)==P-1
    assert (P-1)%b!=0
    w=auxiliary_root(b)
    assert power(w,b)==ONE
    assert power(w,b//2)!=ONE and power(w,b//3)!=ONE
    assert w[1]!=0
    x=[(j,j*j%P) for j in range(b)]
    assert transform(transform(x),True)==x


@pytest.mark.parametrize('n,q',[(2,root(2)),(3,3),(4,root(4)),(7,root(7)),(8,3),(13,3),(16,root(16))])
def test_independent_coordinate_basis(n,q):
    for lane in range(2):
        for i in range(n):
            x=[[0]*n,[0]*n]
            x[lane][i]=1
            y=packed_geometric(*x,q)
            assert y==(oracle(x[0],q),oracle(x[1],q))
            assert packed_geometric(*y,q,inverse=True)==tuple(x)
    rng=Random(n)
    x=[[rng.randrange(P) for _ in range(n)] for _ in range(2)]
    y=packed_geometric(*x,q)
    assert y==(oracle(x[0],q),oracle(x[1],q))
    assert packed_geometric(*y,q,inverse=True)==tuple(x)


def test_rejections():
    for x,y,q in [([1],[2],3),([1,2],[3],3),([0]*17,[1]*17,3),([1,2,3],[4,5,6],root(2))]:
        with pytest.raises(ValueError): packed_geometric(x,y,q)
    with pytest.raises(ValueError): auxiliary_root(8)
