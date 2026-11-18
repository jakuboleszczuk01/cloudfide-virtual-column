"""Add a calculated ("virtual") column to a pandas DataFrame."""

import re

import pandas

# A column label: letters and underscores only.
LABEL = re.compile(r"^[A-Za-z_]+$")
# A role: labels joined by +, - or *, with optional whitespace, e.g. "a * b - c".
ROLE = re.compile(r"^\s*[A-Za-z_]+(\s*[+\-*]\s*[A-Za-z_]+)*\s*$")


def add_virtual_column(df: pandas.DataFrame, role: str, new_column: str) -> pandas.DataFrame:
    """Return a copy of `df` with `new_column` computed from `role`.

    `role` is an arithmetic expression over existing column labels using
    +, - and * (normal precedence: * before + and -), e.g.
    "quantity * unit_price - discount".

    Returns an empty DataFrame if the role is malformed, uses an unknown
    column, or if any label (including `new_column`) contains characters
    other than letters and underscores.
    """
    if not LABEL.match(new_column) or not ROLE.match(role):
        return pandas.DataFrame([])

    # Tokens alternate: label, operator, label, operator, ..., label
    tokens = re.findall(r"[A-Za-z_]+|[+\-*]", role)
    labels, operators = tokens[0::2], tokens[1::2]
    if any(label not in df.columns for label in labels):
        return pandas.DataFrame([])

    # Pass 1: multiply - collapse every "a * b * c" into one term.
    terms = [df[labels[0]]]
    term_operators = []  # the + / - between terms
    for operator, label in zip(operators, labels[1:]):
        if operator == "*":
            terms[-1] = terms[-1] * df[label]
        else:
            terms.append(df[label])
            term_operators.append(operator)

    # Pass 2: add / subtract the terms left to right.
    result = terms[0]
    for operator, term in zip(term_operators, terms[1:]):
        result = result + term if operator == "+" else result - term

    out = df.copy()
    out[new_column] = result
    return out
