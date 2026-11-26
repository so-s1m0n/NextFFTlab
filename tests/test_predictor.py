from itertools import product
import pytest
from nextfft_lab.predictor import predict, window


def test_paper_three_bit_example():
    digits=list(product(range(2),repeat=3))
    inside=outside=0
    for k,beta in product(digits,repeat=2):
        p,z,ok=predict(k,beta,bounds=(1,2))
        if ok:
            assert p==z
            inside+=1
        else:
            assert p!=z
            outside+=1
    assert (inside,outside)==(48,16)


@pytest.mark.parametrize('ell,m',[(2,2),(2,128),(7,64),(17,64)])
def test_window_counts(ell,m):
    u,v=window(m,ell)
    for c in range(m*(ell-1)+1):
        k=[min(ell-1,max(0,c-i*(ell-1))) for i in range(m)]
        p,z,ok=predict(k,[0]*m,ell)
        assert ok==(u<=c<=v)
        if ok:
            assert p==z


def test_invalid():
    with pytest.raises(ValueError): predict([0,1],[0])
    with pytest.raises(ValueError): predict([0,2],[0,0])
    with pytest.raises(ValueError): predict([0,1],[0,0],bounds=(2,1))
