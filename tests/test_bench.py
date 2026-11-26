from nextfft_lab.bench import run

def test_benchmark_schema():
    result=run(3,1,1)
    assert len(result['rows'])==15
    assert {r['domain'] for r in result['rows']}=={'Fp','complex128'}
    assert all(r['median_ns']>0 for r in result['rows'])
