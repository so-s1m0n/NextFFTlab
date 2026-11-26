# NextFFT Lab

Independent, reproducible research on the practical implications of the November 24, 2026 preprint [The logarithmic exponent of finite Fourier transforms](https://github.com/openai/math/tree/main/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026).
[日本語](README.ja.md)

**Status: classical baselines and scalar predictor oracle implemented. The full new construction and any practical speedup remain unverified.** The preprint concerns binary linear-gate complexity over suitable fields, not measured execution time. The lab aims to bridge that gap; it is not affiliated with OpenAI.

## Quick start

Python 3.10+.

```sh
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
python -m pytest -q
python -m nextfft_lab.bench --max-power 12 --repeats 5 --out results/local.json
```

## Current scope

- Exact direct DFT and classical radix-2 NTT over F_998244353.
- Exact classical Bluestein chirp transform for supported lengths and polynomial convolution.
- Independent small-input direct oracle, roundtrip, edge-case and convolution tests.
- CPU benchmarks with seeded inputs, warmup, raw samples and environment metadata.
- Separate complex128 NumPy/SciPy and finite-field tracks. Do not compare their timings as equivalent workloads.
- Research roadmap, claim ledger and source references: [docs/research.md](docs/research.md).
- One local smoke benchmark: [results/baseline.json](results/baseline.json). It is not a hardware-independent performance claim.

## Development handoff

See [AGENTS.md](AGENTS.md) for coding-agent instructions and [docs/ROADMAP.md](docs/ROADMAP.md) for source mappings, acceptance gates and the current next task. The paper's count predictor now has a scalar reference implementation; it is not a fast Fourier backend.

## Research objective

Implement the preprint's actual construction, map each component to a source location, audit correctness and all implementation overhead, then identify crossover sizes against optimized baselines. Report failures and negative results too.

## Contributing

Small, reproducible experiments are welcome. Every experimental backend needs an oracle test, source attribution, supported field/length assumptions and a cost model. Do not label classical routines or approximation algorithms as the paper's exact construction. See [docs/research.md](docs/research.md).

## License

MIT for this repository's original code and documentation. Linked works retain their own licenses.
