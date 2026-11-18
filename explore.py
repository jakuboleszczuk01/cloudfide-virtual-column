"""Profile the raw sales.csv - the queries used to find the problems listed in README.md.

Usage:  python explore.py

Everything is read as text so nothing is parsed (and hidden) before we look at it.
The approach is the same for every column: describe what a good value looks like
and print everything that does not match.
"""

import pandas as pd

df = pd.read_csv("sales.csv", dtype=str, keep_default_na=False)


def show(title, value):
    print(f"\n== {title}")
    print(value)


show("Headers (look for stray whitespace)", list(df.columns))

show("Rows whose Order ID is not SO-xxxxx (repeated header, TOTAL footer)",
     df.loc[~df["Order ID"].str.startswith("SO-"), "Order ID"].value_counts())

show("Fully duplicated lines",
     df[df.duplicated(keep=False)]["Order ID"].tolist())

show("Region spelling variants",
     df["Region"].value_counts())

show("Quantity values that are not a plain integer",
     df.loc[~df["Quantity "].str.fullmatch(r"\d+"), "Quantity "].value_counts())

show("Unit Price values that are not nn.nn",
     df.loc[~df["Unit Price"].str.fullmatch(r"\d+\.\d+"), "Unit Price"].value_counts())

show("Empty Discount cells",
     (df["Discount"] == "").sum())

show("Order Dates that fail strict YYYY-MM-DD parsing",
     df.loc[pd.to_datetime(df["Order Date"], format="%Y-%m-%d", errors="coerce").isna(), "Order ID"].tolist())

prices = pd.to_numeric(df["Unit Price"].str.replace(",", "."), errors="coerce")
show("Distinct prices per product (1 => a missing price can be filled from the product)",
     df.assign(price=prices).groupby("Product")["price"].nunique())
