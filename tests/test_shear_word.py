from itertools import count
from random import Random
import pytest
from nextfft_lab.exact import P
from nextfft_lab.shear_word import MAX_N, forward_counts, tensor_shear_classical, tensor_shear_word


def direct(values,inverse=False):
    return [sum((-1 if inverse and (k^i).bit_count()%2 else 1)*v
                for k,v in enumerate(values) if k&i==i)%P for i in range(len(values))]


@pytest.mark.parametrize('n',[1,2,4,8,16,32,64])
def test_full_basis(n):
    for k in range(n):
        x=[int(i==k) for i in range(n)]
        for inv in (False,True):
            expected=direct(x,inv)
            assert tensor_shear_word(x,inverse=inv)==expected
            assert tensor_shear_classical(x,inverse=inv)==expected


@pytest.mark.parametrize('n',[128,256,1024])
def test_dense(n):
    rng=Random(n)
    x=[rng.randrange(P) for _ in range(n)]
    expected=direct(x)
    assert tensor_shear_word(x)==tensor_shear_classical(x)==expected
    assert tensor_shear_word(expected,inverse=True)==x
    assert tensor_shear_word(x,inverse=True)==direct(x,True)


def test_counts_and_rejections():
    assert forward_counts(64)=={'classical_adds':192,'word_walsh_calls':3,
        'word_classical_walsh_adds_subtracts':1152,'word_diagonal_entry_updates':256}
    for x in ([],[0]*3,[0]*2048):
        for fn in (tensor_shear_word,tensor_shear_classical):
            with pytest.raises(ValueError): fn(x)
    for n in (0,3,2048,True):
        with pytest.raises(ValueError): forward_counts(n)


def test_exact_bounded_integer_inputs():
    for apply in (tensor_shear_word, tensor_shear_classical):
        with pytest.raises(TypeError):
            apply([0.75])
        values = count()
        with pytest.raises(ValueError):
            apply(values)
        assert next(values) == MAX_N + 1
        assert apply(iter([P + 1, -2])) == [P - 1, P - 2]
