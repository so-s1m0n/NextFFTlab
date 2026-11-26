import random
import pytest
from nextfft_lab.exact import P, root, direct, radix2, bluestein, convolution

@pytest.mark.parametrize('n',[1,2,4,8,16,32,64,128])
@pytest.mark.parametrize('kind',['zero','impulse','constant','random','signed'])
def test_power_two(n,kind):
    r=random.Random(n)
    a={'zero':[0]*n,'impulse':[1]+[0]*(n-1),'constant':[7]*n,'random':[r.randrange(P) for _ in range(n)],'signed':[(-1)**j*j for j in range(n)]}[kind]
    expected=direct(a)
    assert radix2(a)==expected==bluestein(a)
    assert radix2(expected,True)==[x%P for x in a]
    assert bluestein(expected,True)==[x%P for x in a]

@pytest.mark.parametrize('n',[7,14,17,28,34,119])
def test_non_power_two(n):
    r=random.Random(n)
    a=[r.randrange(P) for _ in range(n)]
    assert bluestein(a)==direct(a)
    assert bluestein(bluestein(a),True)==a

@pytest.mark.parametrize('a,b',[([], [1]),([1],[2]),([1,2,3],[4,5]),([-3,4],[P-1,2,9]),(list(range(33)),list(range(15)))])
def test_convolution(a,b):
    expected=[] if not a or not b else [sum(a[i]*b[k-i] for i in range(len(a)) if 0<=k-i<len(b))%P for k in range(len(a)+len(b)-1)]
    assert convolution(a,b)==expected

@pytest.mark.parametrize('n',[0,3,5,9])
def test_bad_length(n):
    with pytest.raises(ValueError): root(n)

def test_radix_rejects_non_power():
    with pytest.raises(ValueError): radix2([0]*7)

def test_known_vector():
    assert direct([1,2])==[3,P-1]
