"""Closed-form dimension for the existing binary Hamming-label construction."""


def binary_hamming_gram_rank(length, alphabet):
    """Rank over F2 of 1 + HammingDistance on all alphabet**length labels."""
    if type(length) is not int or length < 1:
        raise ValueError("positive label length required")
    if type(alphabet) is not int or alphabet < 2 or alphabet % 2:
        raise ValueError("positive even alphabet required")
    # Each coordinate contributes its even-parity indicator subspace,
    # sharing only constants. The baseline Gram row adds one dimension.
    return length * (alphabet - 2) + 2
