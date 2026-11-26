"""Reproducible CPU baseline; compare within arithmetic domains only."""
import argparse
import json
import platform
import random
import statistics
import sys
import time
from pathlib import Path
import numpy as np
import scipy
from scipy import fft
from .exact import P, direct, radix2, bluestein


def measure(fn, repeats):
    fn()  # warm-up, excluded
    samples = []
    for _ in range(repeats):
        t = time.perf_counter_ns()
        fn()
        samples.append(time.perf_counter_ns()-t)
    return {"median_ns": statistics.median(samples), "min_ns": min(samples), "samples_ns": samples}


def run(max_power=16, repeats=5, seed=20261126):
    if not 1 <= max_power <= 20 or repeats < 1:
        raise ValueError("max_power 1..20; repeats >=1")
    rng = np.random.default_rng(seed)
    prng = random.Random(seed)
    rows = []
    for k in range(1,max_power+1):
        n = 2**k
        x = rng.standard_normal(n)+1j*rng.standard_normal(n)
        expected = np.fft.fft(x)
        for name, fn in [("numpy_fft",lambda: np.fft.fft(x)), ("scipy_fft",lambda: fft.fft(x,workers=1))]:
            y = fn()
            err = float(np.linalg.norm(y-expected)/np.linalg.norm(expected))
            if err > 1e-10:
                raise AssertionError((name,n,err))
            rows.append({"domain":"complex128","algorithm":name,"n":n,"relative_l2_vs_numpy":err,**measure(fn,repeats)})
        if k <= 12:
            a = [prng.randrange(P) for _ in range(n)]
            y = radix2(a)
            if radix2(y,True) != a:
                raise AssertionError("NTT roundtrip failed")
            oracle = direct(a) if k <= 7 else None
            for name,fn in [("radix2_ntt",lambda: radix2(a)), ("bluestein_ntt",lambda: bluestein(a))]+([("direct_ntt",lambda: direct(a))] if oracle is not None else []):
                if fn() != y or (oracle is not None and y != oracle):
                    raise AssertionError((name,n))
                rows.append({"domain":"Fp","algorithm":name,"n":n,"exact_match":True,"oracle":"direct" if oracle is not None else "radix2 (roundtrip checked)",**measure(fn,repeats)})
    return {"scope":"classical CPU baselines only; new construction not implemented", "python":sys.version,"platform":platform.platform(),"machine":platform.machine(),"processor":platform.processor(),"numpy":np.__version__,"scipy":scipy.__version__,"seed":seed,"repeats":repeats,"rows":rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-power",type=int,default=16)
    parser.add_argument("--repeats",type=int,default=5)
    parser.add_argument("--seed",type=int,default=20261126)
    parser.add_argument("--out",type=Path,default=Path("results/local.json"))
    args = parser.parse_args()
    report = run(args.max_power,args.repeats,args.seed)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(f"Wrote {len(report['rows'])} rows to {args.out}")

if __name__ == "__main__":
    main()
