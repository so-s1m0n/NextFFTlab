# NextFFT Lab

**v0.1.0 Research Preview candidate** · [日本語](README.ja.md)

An independent study of the November 24, 2026 preprint *The logarithmic exponent of finite Fourier transforms*. This cycle reproduced selected mathematical components, measured a fixed Walsh–Hadamard template and searched small circuit neighborhoods. The project is independent of OpenAI. [Pinned manuscript](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/paper.pdf)

## Results

- **Exact fixed template.** The binary matrix pencil, bounded Hermite repair and shared routing were checked over F₉₉₈₂₄₄₃₅₃. A zero-exception template agreed exactly with classical Walsh–Hadamard on 512 independent length-256 inputs. Repair with nonzero exceptions was tested separately on a toy window.
- **Measured optimization.** Sparse routing and a degree-sized pencil reduced the fixed Python template from 7.718 s to 0.679 s on the same batch. Classical Walsh took 0.0772 s in that comparison. The optimized template still required 24 axis calls per row for eight axes, above the threshold required for recursion.
- **Circuit search.** The bounded H8 and H16 search retained the published comparison points: 19 binary linear gates and 20 scaled arithmetic operations at H8, and 56 scaled arithmetic operations at H16. Witnesses were checked on all basis vectors over the rationals and the finite field. Gate counts, arithmetic counts and scale restoration are reported separately.
- **Open scope.** A saving recursive template, general-length reproduction and local validation of the upstream Lean formalization remain open.

The [final research report](docs/FINAL_REPORT.md) separates published results, lab measurements and bounded negative results.

## Active research: general-length NTT and FFT

[General-length research](docs/GENERAL_LENGTH_RESEARCH.md) records occupied-fiber borrowing, Bostan–Schost interpolation, bounded multi-axis and polynomial packing over small extension fields, and the numerical limits of the tested complex128 factorization. The general-length theorem and saving recursive construction remain open. [Research protocol](docs/AGENT_RESEARCH_PROTOCOL.md)

The characteristic-zero follow-up verifies the prime-five split and width-four deformation over Q(i). The measured split multiplication was about seven times slower than direct schoolbook in the paper-derived quotient at the tested jet orders. [Prime-five results and reproduction](docs/PRIME5_DEFORMATION_A3.md) · [Construction map and runnable examples](docs/CONSTRUCTION_MAP.md)

## Run the tests

Python 3.10 or newer. Run the commands from a virtual environment in the repository root.

```sh
python -m pip install -e '.[dev,research]'
python -m pytest -q
python -m nextfft_lab.bench --max-power 7 --repeats 2
```

The `research` extra pins `z3-solver==4.15.4.0`. The standard suite can use `.[dev]` alone, which skips the single Z3 regression when Z3 is unavailable. The `research-z3` CI job installs the solver and requires that regression to run and pass.

## Reproduce the evidence

- [Dependencies, commands and raw-data index](docs/REPRODUCIBILITY.md)
- [Implementation roadmap and source mapping](docs/ROADMAP.md)
- [Optimization evidence](docs/OPTIMIZATION.md) and [published-record search](docs/RECORD_SEARCH.md)

The classical cyclic DFT/NTT baselines and the binary Walsh transform are separate workloads. The complex NumPy/SciPy benchmarks use a separate arithmetic domain.

## License

NextFFTlab's original code and documentation are [MIT licensed](LICENSE). The two circuit data files derived from Jacob Sussman's H8 work are covered by the [third-party notice](results/record-circuits/NOTICE.md) and [Apache-2.0 license](results/record-circuits/LICENSE-APACHE-2.0.txt).
