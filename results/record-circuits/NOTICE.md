# Attribution for H8 circuit data

The Walsh-Hadamard transform with fewer operations (wht-fewer-operations)
Copyright 2026 Jacob Sussman

- [sussman-h8.json](../circuits/sussman-h8.json) encodes Sussman's published half-scale H8 circuit in NextFFTlab's finite-field JSON format. NextFFTlab converted the coefficients to F₉₉₈₂₄₄₃₅₃ and records the common restoration factor. [Pinned half-scale circuit source](https://github.com/jacobalansussman/wht-fewer-operations/blob/bbb7f830d8c5612465a9922ace566750ce6d09d2/tools/circuits/programs/h8_half_20ops.txt)
- [h8_19_gate.json](h8_19_gate.json) is an SMT-rescaled derivative of Sussman's 19-gate H8 circuit at the same revision. NextFFTlab changed the wire scales, introduced shared scalar copies and stored the circuit as rational JSON. [Pinned 19-gate circuit source](https://github.com/jacobalansussman/wht-fewer-operations/blob/bbb7f830d8c5612465a9922ace566750ce6d09d2/tools/circuits/programs/h8_19gates.txt)

The accompanying [Apache-2.0 license](LICENSE-APACHE-2.0.txt) applies to these circuit data files. [Upstream notice](https://github.com/jacobalansussman/wht-fewer-operations/blob/bbb7f830d8c5612465a9922ace566750ce6d09d2/NOTICE)
