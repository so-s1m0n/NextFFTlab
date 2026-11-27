# NextFFT Lab — instructions for coding agents

## Mission and definition of done

Translate the pinned November 24, 2026 construction into runnable, auditable code, establish exact correctness and measure its actual cost against mature equivalent baselines. A usable faster implementation is the stretch goal, not a premise. A reproducible negative result is a valid research outcome, but must not be described as a speedup or as proof that no future implementation could win.

Read README.md, docs/AGENT_RESEARCH_PROTOCOL.md and docs/GENERAL_LENGTH_RESEARCH.md first. The latter is the active queue for post-WHT paper verification and applications. docs/ROADMAP.md and docs/FINAL_REPORT.md archive the prior research cycle. Do not restart closed WHT searches without new structural evidence. Start with the next incomplete active task. Inspect git status, CI, and existing tests before changes. Do not overwrite user changes.

## Work loop

1. Pin upstream revision and inspect actual LaTeX/Lean; record lemma labels, hypotheses, dependencies and source URLs in docs/ROADMAP.md. Distinguish observed facts, deductions and conjectures.
2. Implement the smallest next source-mapped component and independent oracle tests. Run the whole suite. Record real output, commands, environment, resource bounds and limitations. Commit small coherent changes.
3. Proceed to the next gate when acceptance passes; if blocked, document the concrete blocker, exact parameter sizes and evidence. Prefer an executable restricted case over an imaginary generic solution. Never fabricate timings, proofs or missing constants.
4. Update the status ledger and README as results change. Keep code and public claims aligned. Continue through feasible gates without asking for approval on routine engineering choices. Stop before costly or destructive actions; use bounded experiments, no external paid resources or credentials without authorization.

## Technical boundaries

- Preserve existing classical exact.py and bench.py behavior and tests unless fixing a documented defect.
- The prime tensor transform (binary case: Walsh–Hadamard on (Z/2)^k) is NOT the cyclic DFT of size 2^k. Compare like for like. Start with F_998244353 and binary radix; track characteristic and required roots/extensions explicitly.
- Scalar frequency-domain predictor oracle, dense matrices, classical transform fallbacks and toy repairs are not the fast algorithm. The construction needs matrix-root pencil evaluation, full-rate Hermite repair, shared query routing, endpoint conversions and finite-template recursion; later general lengths and polynomial multiplication.
- Distinguish paper binary gates au+bv, ring ops, coefficient/setup/index cost, extension rank, memory, batch size and actual time. Count cross-row work and padding. No claim about asymptotic exponent from a finite regression or a toy window.
- No unsupported speed claim: compare equivalent output, arithmetic, precision, size, batch, thread count, amortization, memory and language/compiler optimization. Record raw data. Separate first-call and reused setup. Avoid arbitrary threshold tuning on reported test data.
- Never copy upstream code or manuscript wholesale without reviewing its license. Prefer independent implementation with citations. Do not expose private data, tokens, local paths or unrelated repositories in public outputs.
- Tests must include basis vectors (fixed linear map), seeded random vectors, edge cases and unsupported inputs; assert exact equality over finite fields. Floats, approximate repair and GPU are later research.

## Commands

    python -m pip install -e '.[dev]'
    python -m pytest -q
    python -m nextfft_lab.bench --max-power 7 --repeats 2

A successful test suite verifies implemented components only. Do not say the new Fourier construction is complete before its relevant gate passes.
