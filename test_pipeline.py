"""Tests for pipeline.py and extra tests for add_virtual_column.

The sample tests for add_virtual_column provided with the task are in
test_virtual_column.py; the ones here cover precedence and the real data.
"""

import pandas as pd
import pytest

from pipeline import load_sales, revenue_by_region
from solution import add_virtual_column

# --- add_virtual_column: cases not covered by the sample tests ---------------


def test_multiplication_before_subtraction():
    df = pd.DataFrame({"q": [2, 3], "p": [10, 10], "d": [1, 2]})
    result = add_virtual_column(df, "q * p - d", "r")
    assert result["r"].tolist() == [19, 28]


def test_left_to_right_subtraction():
    df = pd.DataFrame({"a": [100], "b": [10], "c": [1]})
    assert add_virtual_column(df, "a - b - c", "r")["r"].tolist() == [89]


def test_input_is_not_modified():
    df = pd.DataFrame({"a": [1], "b": [2]})
    add_virtual_column(df, "a + b", "c")
    assert list(df.columns) == ["a", "b"]


@pytest.mark.parametrize("role", ["", "a +", "a / b", "a + 1", "(a + b)", "a + missing"])
def test_invalid_roles_return_empty(role):
    df = pd.DataFrame({"a": [1], "b": [2]})
    assert add_virtual_column(df, role, "c").empty


# --- pipeline: cleaning of the real sales.csv --------------------------------


@pytest.fixture(scope="module")
def sales():
    return load_sales("sales.csv")


def test_non_order_rows_and_duplicates_removed(sales):
    assert len(sales) == 1500  # 1507 lines - repeated header - TOTAL - 5 duplicates
    assert sales["order_id"].is_unique
    assert not sales["order_id"].isin(["Order ID", "TOTAL"]).any()


def test_regions_normalised(sales):
    assert sorted(sales["region"].unique()) == ["Central", "East", "North", "South", "West"]


def test_quantity_parsed(sales):
    assert sales["quantity"].dtype == int
    assert sales.loc[sales["order_id"] == "SO-10251", "quantity"].item() == 1762  # was "1 762"
    assert (sales["quantity"] < 0).sum() == 6  # returns are kept


def test_unit_price_parsed_and_filled(sales):
    assert sales["unit_price"].notna().all()
    assert sales.loc[sales["order_id"] == "SO-10137", "unit_price"].item() == 59.0  # was "59,00"
    assert sales.loc[sales["order_id"] == "SO-10610", "unit_price"].item() == 21.0  # was empty
    assert sales.groupby("product")["unit_price"].nunique().eq(1).all()


def test_missing_discount_is_zero(sales):
    assert sales["discount"].notna().all()
    assert (sales["discount"] == 0).sum() == 959


def test_revenue_by_region_matches_committed_output(sales):
    expected = pd.read_csv("revenue_by_region.csv")
    pd.testing.assert_frame_equal(revenue_by_region(sales), expected)


def test_revenue_formula_on_small_example():
    df = pd.DataFrame(
        {"region": ["A", "A", "B"], "quantity": [2, -1, 3], "unit_price": [10.0, 10.0, 5.0], "discount": [1.0, 0.0, 0.0]}
    )
    result = revenue_by_region(df)
    assert result["revenue"].tolist() == [9.0, 15.0]  # A: 20-1-10, B: 15
