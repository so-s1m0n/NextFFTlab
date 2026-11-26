# NextFFT Lab

Independent, reproducible research on the practical implications of the November 24, 2026 preprint [The logarithmic exponent of finite Fourier transforms](https://github.com/openai/math/tree/main/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026).
[日本語](README.ja.md)

**Status: classical baselines, including Walsh–Hadamard, and query-power predictor implemented. Matrix-pencil and Hermite repair verified on bounded binary cases. One shared-routing template reproduces exact Walsh–Hadamard output at a fixed size. The sparse fixed template is faster than the original prototype and slower than classical Walsh on the tested workload. A saving template and recursive construction remain open.** The preprint concerns binary linear-gate complexity over suitable fields, not measured execution time. The lab aims to bridge that gap; it is not affiliated with OpenAI.

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

## Reproduce the recorded benchmarks

Create the virtual environment above, then run the commands below from the repository root. Each command emits one JSON document on stdout. The seed is 20261126. Set `NEXTFFT_BENCH_CPU` to the CPU model if the platform reports a generic processor identifier.

```sh
python -m nextfft_lab.bench_repair --repeats 20
python -m nextfft_lab.bench_pencil --repeats 20
python -m nextfft_lab.bench_kernel --repeats 20 --template-repeats 3
```

The recorded host used Windows 11 x86-64, AMD Ryzen 7 5800X, CPython 3.13.3 and one algorithm thread. Timings use `perf_counter_ns` and raw samples. Component measurements warm up once and measure `tracemalloc` peak in a separate call. A traced peak covers Python allocations made during that call. Full-template setup is timed once, followed by three applications with reused setup and three same-input classical Walsh runs. The measured template has 512 independent length-256 rows and zero exceptional rows.

On Windows, reproduce the full-template process peak by launching the **base CPython executable** in a separate process and sampling its `PeakWorkingSet64` while it runs. Run the following in PowerShell 7 with the virtual environment active. The process peak includes the interpreter, inputs and reference output.

```powershell
$basePython = python -c "import sys; print(sys._base_executable)"
$benchmark = Start-Process -FilePath $basePython -ArgumentList '-m nextfft_lab.bench_kernel --repeats 20 --template-repeats 1' -NoNewWindow -PassThru -RedirectStandardOutput results/kernel-local.json
$peak = 0
while (!$benchmark.HasExited) {
    $peak = [Math]::Max($peak, $benchmark.PeakWorkingSet64)
    Start-Sleep -Milliseconds 250
    $benchmark.Refresh()
}
$benchmark.WaitForExit()
if ($benchmark.ExitCode -ne 0) { throw "Benchmark exited with code $($benchmark.ExitCode)" }
$peak
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

See [AGENTS.md](AGENTS.md) for coding-agent instructions and [docs/ROADMAP.md](docs/ROADMAP.md) for source mappings, acceptance gates and the current next task. The count predictor has an integer-count oracle and a separate factored query-power evaluator. [Predictor measurements](results/gate1-components.json) and [pencil/repair measurements](results/gate2-pencil.json) report setup, evaluation and tracked allocations. [Fixed-template measurements](results/gate3-kernel.json) compare 512 exact Walsh–Hadamard rows against the classical implementation and record the routing schedule estimates.

The [optimization study](docs/OPTIMIZATION.md) records the exact m=15 window, implicit matrix root, sparse routing and matched-batch benchmarks.

## Research objective

Implement the preprint's actual construction, map each component to a source location, audit correctness and all implementation overhead, then identify crossover sizes against optimized baselines. Report failures and negative results too.

## Contributing

Small, reproducible experiments are welcome. Every experimental backend needs an oracle test, source attribution, supported field/length assumptions and a cost model. Do not label classical routines or approximation algorithms as the paper's exact construction. See [docs/research.md](docs/research.md).

## License

MIT for this repository's original code and documentation. Linked works retain their own licenses.
