# A3 — characteristic-zero binomial deformation

## Source and hypothesis

Pinned [packing.tex, poly:lem:descent-prime and poly:lem:descent-deform](https://github.com/openai/math/blob/3344da59991ed94f9ba711217b29c1d760badfa6/preprints/The-logarithmic-exponent-of-finite-Fourier-transforms-November-24-2026/build/packing.tex#L214-L355).

The prior packing tests are in a finite field. This checkpoint checks the separate characteristic-zero argument using exact rational arithmetic. It tests the paper's explicit prime p=3 example, and the deformation lemma for one to three width-two binomial axes, not the prime-grid selection for general p.

For p=3, gamma=x-x^2 in Q[x]/(1+x+x^2) satisfies gamma^2=-3. The cyclic input coefficients a,b,c therefore map to the scalar a+b+c and the binomial factor a-(b+c)/2 + ((b-c)/2)Y. The inverse is obtained by solving this three-coordinate linear map. The implementation multiplies the scalar factor and uses deformation for the other factor before recombining. The scalar backend stays in Q and uses no auxiliary splitting field.

For the binomial block, let each coefficient have r jet entries. The relations are Y_i^2=f_i(t)=1+(lambda_i-1)t. At t=1 the endpoint unit is (1+((lambda_i-1)/lambda_i)z)^(1/2), at t=0 it is (1+(lambda_i-1)t)^(1/2). Undo endpoint one, lift the degree-<r coefficients via z=t-1, apply the zero-endpoint scaling, use two classical Walsh evaluations and one inverse Walsh evaluation with pointwise truncated jet products, undo the scaling, and shift t=1+z to recover the product. The polynomial degree bound is 2r-2+d < H=2r+d. The code checks that every coefficient above this bound vanishes in the recovered polynomial. This is a bounded source-derived identity, not a new algorithm.

## Executable verification

- `nextfft_lab/rational_deformation.py` implements both operations with Fraction, supports d,r in 1..3 and nonzero rational lambda_i. It uses exact classical butterfly Walsh and quadratic jet products.
- `tests/test_rational_deformation.py` compares against independent dense multiplication with explicit binomial wraps and jet truncation. Full bilinear basis pairs: 4 (d=1,r=1), 36 (d=1,r=3), 64 (d=2,r=2); a further 9 pairs for cyclic length 3. Seeded rational inputs also test three axes with nonsquare and fractional parameters.
- Local focused suite: 8 passed (0.24 s in a temporary isolated source directory). The follow-up independently reran these eight tests and the full suite at 71348d5 (263 passed with Z3).

```sh
python -m pytest -q tests/test_rational_deformation.py
```

## Limits and research value

The transform stage makes three tensor Fourier calls on W=2^d jet entries of length H and W pointwise jet products. Exact rational arithmetic introduces coefficient-size costs, and setup, scaling and shifts are deliberately quadratic and recomputed. No timing or memory comparison was performed. This is not the complete prime-axis conversion, fast synchronized circuit, efficient base-field descent or formal convolution complexity result. Its purpose is to give readers an executable example of multiplying in a nonsplit binomial algebra using a split intermediate algebra, including nonconstant jets. This may be useful as a correctness oracle for symbolic polynomial arithmetic; no application performance advantage has been demonstrated.

The [prime-five follow-up](PRIME5_DEFORMATION_A3.md) implements and measures the width-four case over Q(i).
