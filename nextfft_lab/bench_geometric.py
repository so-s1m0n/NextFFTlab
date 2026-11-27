"""Reproduce bounded Newton-factorization checks and matched NTT timings."""
import argparse
import json
import platform
from random import Random
from statistics import median
from time import perf_counter_ns
from .exact import P, radix2, root
from .geometric import NewtonPlan


def measure(fn, repeats):
    fn()
    samples = []
    for _ in range(repeats):
        start = perf_counter_ns()
        fn()
        samples.append(perf_counter_ns()-start)
    return {'samples_ns': samples, 'median_ns': median(samples)}


def run(repeats=20):
    if not 1 <= repeats <= 100:
        raise ValueError('repeats outside budget')
    rng = Random(20261127)
    rows = []
    for n in (16,64,256,512):
        q = root(n)
        x = [rng.randrange(P) for _ in range(n)]
        plan = NewtonPlan.build(n,q)
        expected = radix2(x)
        assert plan.apply(x)==expected and plan.apply(expected,True)==x
        rows.append({'n':n,'padded':plan.lower.padded,'forward_backend_ntts':4,
                     'setup_includes_inverse_reciprocal':True,
                     'setup':measure(lambda:NewtonPlan.build(n,q),repeats),
                     'newton_forward':measure(lambda:plan.apply(x),repeats),
                     'classical_forward':measure(lambda:radix2(x),repeats)})
    return {'field':P,'seed':20261127,'repeats':repeats,'python':platform.python_version(),
            'platform':platform.system()+' '+platform.machine(),'rows':rows}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repeats',type=int,default=20)
    args = p.parse_args()
    print(json.dumps(run(args.repeats),indent=2))


if __name__ == '__main__':
    main()
