from random import Random
import pytest
from nextfft_lab.exact import P, direct, root
from nextfft_lab.geometric import NewtonPlan, ToeplitzPlan, occupied_lower, reciprocal


def oracle(x,q):
    return [sum(a*pow(q,i*j,P) for j,a in enumerate(x))%P for i in range(len(x))]


@pytest.mark.parametrize('n,q',[(1,1),(4,root(4)),(7,root(7)),(8,root(8)),(16,root(16)),(17,root(17)),(7,3),(12,3)])
def test_newton_basis(n,q):
    plan = NewtonPlan.build(n,q)
    for i in range(n):
        x = [int(j==i) for j in range(n)]
        y = oracle(x,q)
        assert plan.apply(x)==y
        assert plan.apply(y,True)==x
        if pow(q,n,P)==1:
            assert plan.apply(x,True)==direct(x,True)


@pytest.mark.parametrize('n',[2,5,8,16,31,64])
def test_occupied_and_toeplitz(n):
    rng = Random(n)
    h = [rng.randrange(1,P)]+[rng.randrange(P) for _ in range(n-1)]
    x = [rng.randrange(P) for _ in range(n)]
    z = [rng.randrange(P) for _ in range(n)]
    expected = [sum(h[i-j]*x[j] for j in range(i+1))%P for i in range(n)]
    plan = ToeplitzPlan.build(h)
    assert plan.apply(x)==expected
    assert plan.apply(x,True)==[sum(h[j-i]*x[j] for j in range(i,n))%P for i in range(n)]
    assert ToeplitzPlan.build(reciprocal(h)).apply(expected)==x
    assert occupied_lower(h,x,z)==(expected,z)


def test_invalid():
    for n,q in [(0,3),(513,3),(5,root(4)),(4,0)]:
        with pytest.raises(ValueError): NewtonPlan.build(n,q)
    with pytest.raises(ValueError): reciprocal([0,1])
    with pytest.raises(ValueError): NewtonPlan.build(4,3).apply([1])
    with pytest.raises(ValueError): occupied_lower([1,2],[1,2],[3])
