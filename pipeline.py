"""Clean sales.csv and compute total revenue per region.

Usage:  python pipeline.py

Output: revenue_by_region.csv  (columns: region, revenue)
See README.md for the list of data problems and how each one is handled;
explore.py shows the queries used to find them.
"""

import pandas as pd

from solution import add_virtual_column

INPUT = "sales.csv"
OUTPUT = "revenue_by_region.csv"

COLUMNS = {
    "Order ID": "order_id",
    "Region": "region",
    "Product": "product",
    "Quantity": "quantity",
    "Unit Price": "unit_price",
    "Discount": "discount",
    "Order Date": "order_date",
}


def load_sales(path: str = INPUT) -> pd.DataFrame:
    """Read the raw export and return clean, typed order lines."""
    # Read everything as text so values like "1 762" or "59,00" survive parsing.
    df = pd.read_csv(path, dtype=str, keep_default_na=False)

    # Headers: "Quantity " has a trailing space; rename all to snake_case
    # (letters/underscores only, so they work as labels in add_virtual_column).
    df.columns = df.columns.str.strip()
    df = df.rename(columns=COLUMNS)

    # Rows that are not orders: the header repeated mid-file and a TOTAL footer.
    df = df[(df["order_id"] != "Order ID") & (df["order_id"] != "TOTAL")]

    # 5 order lines are exported twice (identical content) - keep one.
    df = df.drop_duplicates()

    # Region: " North", "west  ", "EAST" -> "North", "West", "East".
    df["region"] = df["region"].str.strip().str.title()

    # Quantity: "1 762" uses a space as thousands separator.
    # Negative quantities are kept - they are returns and reduce revenue.
    df["quantity"] = df["quantity"].str.replace(" ", "").astype(int)

    # Unit price: some use a decimal comma ("59,00"); 4 are missing.
    # Every product has exactly one price in the file, so fill from the product.
    df["unit_price"] = pd.to_numeric(df["unit_price"].str.replace(",", "."))
    df["unit_price"] = df["unit_price"].fillna(df.groupby("product")["unit_price"].transform("max"))

    # Discount: empty means no discount.
    df["discount"] = pd.to_numeric(df["discount"]).fillna(0.0)

    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d")
    return df.reset_index(drop=True)


def revenue_by_region(df: pd.DataFrame) -> pd.DataFrame:
    """Total revenue per region, sorted by region name."""
    df = add_virtual_column(df, "quantity * unit_price - discount", "revenue")
    return df.groupby("region", as_index=False)["revenue"].sum().round(2)


if __name__ == "__main__":
    result = revenue_by_region(load_sales(INPUT))
    result.to_csv(OUTPUT, index=False)
    print(result.to_string(index=False))
