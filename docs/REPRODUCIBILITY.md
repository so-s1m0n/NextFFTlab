# Reproducibility and provenance

The commands below reproduce the archived experiments. Use a virtual environment with Python 3.10 or newer. Standard CI uses CPython 3.10 and 3.12, and research CI uses CPython 3.12. The package declares NumPy and SciPy as runtime dependencies, pytest in the `dev` extra, and Z3 4.15.4.0 in the `research` extra. Git is required to read the pinned third-party circuit descriptions for the record search.

```sh
python -m pip install -e '.[dev,research]'
python -m pip check
python -c "import z3; print(z3.get_version_string())"
python -m pytest -q -rs
python -m nextfft_lab.bench --max-power 7 --repeats 2
```

Use the same environment for the bounded benchmarks below. Keep newly generated reports and circuits in an untracked output location. Benchmark JSON with archived measurements is indexed separately from the output paths in the examples.

## Archived benchmarks

| Experiment | Raw evidence |
|---|---|
| Classical cyclic DFT, radix-2 NTT, Bluestein and the separate complex track | [Baseline](../results/baseline.json) |
| Walsh baselines and query-power predictor | [Component run](../results/gate1-components.json) |
| Matrix pencil and toy repair | [Pencil run](../results/gate2-pencil.json) |
| Fixed shared-routing template | [Kernel run](../results/gate3-kernel.json) |
| Sparse routing and degree-sized pencil | [Original](../results/optimization-baseline.json), [routing only](../results/optimization-routing-only.json), [compact](../results/optimization-compact.json), [classical](../results/optimization-classical.json), [components](../results/optimization-components.json) |
| Finite-field circuit synthesis and tensor lift | [Circuit search](../results/circuit-search.json), [witnesses](../results/circuits) |
| Bounded search against the published H8/H16 points | [Record search](../results/record-search.json), [rational witness and notices](../results/record-circuits) |

The recorded Windows runs identify the OS, CPU, Python version, thread count and input seed in the JSON or experiment reports. Benchmark times are warm medians from saved samples. Full-template setup time, traced Python allocations and process working set are different measurements. [Optimization methodology](OPTIMIZATION.md) · [Record-search limits and methods](RECORD_SEARCH.md)

```sh
python -m nextfft_lab.bench_repair --repeats 20
python -m nextfft_lab.bench_pencil --repeats 20
python -m nextfft_lab.bench_kernel --repeats 20 --template-repeats 3
python -m nextfft_lab.bench_optimization --variant components --repeats 20
python -m nextfft_lab.bench_optimization --variant baseline --repeats 3
python -m nextfft_lab.bench_optimization --variant routing-only --repeats 3
python -m nextfft_lab.bench_optimization --variant compact --repeats 3
python -m nextfft_lab.bench_optimization --variant classical --repeats 3
python -m nextfft_lab.bench_circuit --repeats 20
```

On Windows, the archived fixed-template process peak was measured by launching the base CPython executable in a separate process and sampling its `PeakWorkingSet64`. In PowerShell, with the virtual environment active, use the following single-repetition run for the memory measurement. The process peak includes the interpreter, inputs and reference output.

```powershell
$basePython = python -c "import sys; print(sys._base_executable)"
$benchmark = Start-Process -FilePath $basePython -ArgumentList '-m nextfft_lab.bench_kernel --repeats 20 --template-repeats 1' -NoNewWindow -PassThru -RedirectStandardOutput kernel-local.json
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

## Pinned circuit search and source licenses

Put the reference checkout outside the NextFFTlab checkout. The search driver reads circuit text with `git show` at the pinned commit and parses it as data. The solver is optional when running with `--skip-smt`, which omits that search method.

```sh
git clone --no-checkout https://github.com/jacobalansussman/wht-fewer-operations.git ../published-wht-reference
python -m nextfft_lab.bench_record_search --reference-repo ../published-wht-reference
```

The driver verifies the published and retained circuits on every basis vector over the rationals and the finite field. The archived search used the Windows Job Object 1 GiB process commit limit. See the [search report](RECORD_SEARCH.md) for the separate solver, neighbor, state and time bounds.

- OpenAI's November 24 preprint and higher-level claims are tied to the source commit in the [source map](ROADMAP.md). The repository records the Lean correspondence and leaves local compilation open.
- The chronological comparison uses the Alman–Rao arithmetic bound and Sussman's distinct gate and scaled-arithmetic counts. [Alman and Rao v2](https://arxiv.org/abs/2211.06459) · [Sussman at bbb7f830](https://github.com/jacobalansussman/wht-fewer-operations/tree/bbb7f830d8c5612465a9922ace566750ce6d09d2)
- NextFFTlab's original code and documentation are [MIT licensed](../LICENSE). For Sussman's two H8-derived JSON artifacts, see the [attributions](../results/record-circuits/NOTICE.md) and [Apache-2.0 license](../results/record-circuits/LICENSE-APACHE-2.0.txt). The pinned proof and reference repository remain separately licensed external sources.

## Characteristic-zero prime axes

The exact width-four quotient comparison records raw batch samples, setup, operation counts, coefficient bits and traced Python allocation peaks. It uses standard-library Fraction arithmetic. [Protocol and results](PRIME5_DEFORMATION_A3.md) · [Raw JSON](../results/prime5-deformation.json) · [Runnable examples](CONSTRUCTION_MAP.md)

```sh
python -m pytest -q tests/test_rational_deformation.py tests/test_prime5_deformation.py
python -m nextfft_lab.bench_prime5_deformation --output prime5-local.json
```

## Core proof and shear checks

- [Lean toolchain, fixed dependency inventory, attempted build and commands](LEAN_FOURIER_AUDIT.md)
- [Shear basis checks, exact operation counts and conditional subset applications](SHEAR_WORD.md)
- [Strict saving and padding conditions](RECURSION_GATE.md)

```sh
python -m pytest -q tests/test_shear_word.py
```
