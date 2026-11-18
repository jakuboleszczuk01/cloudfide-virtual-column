# Virtual columns & revenue by region

A pandas take-home in three parts: a function that adds a calculated column to a
DataFrame, a pipeline that uses it on a messy sales export, and tests for both.

| File | Purpose |
|------|---------|
| `solution.py` | Part 1 – `add_virtual_column(df, role, new_column)` |
| `pipeline.py` | Part 2 – cleans `sales.csv`, computes revenue, writes `revenue_by_region.csv` |
| `revenue_by_region.csv` | Part 2 output |
| `explore.py` | The profiling queries used to find the problems in `sales.csv` |
| `test_virtual_column.py` | Sample tests provided with the task |
| `test_pipeline.py` | My tests for the pipeline and extra cases for Part 1 |

## Setup and run

Python 3.10+.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python pipeline.py      # writes revenue_by_region.csv and prints the result
pytest                  # runs test_virtual_column.py and test_pipeline.py (22 tests)
python explore.py       # optional: prints the raw-data profile behind the table below
```

Result:

```
region,revenue
Central,515824.67
East,442219.91
North,665897.52
South,504036.04
West,442268.89
```

## Part 1 – `add_virtual_column`

```python
fruits = pd.DataFrame({"quantity": [10, 3], "price": [10, 1]})
add_virtual_column(fruits, "quantity * price", "total")
#    quantity  price  total
# 0        10     10    100
# 1         3      1      3
```

* Labels may contain only letters and underscores; operators are `+`, `-`, `*`;
  whitespace is ignored.
* Normal arithmetic precedence: `*` first, then `+`/`-` left to right, so
  `quantity * unit_price - discount` = `(quantity * unit_price) - discount`.
* Any invalid input (bad character, unknown column, `/`, numbers, parentheses,
  invalid `new_column`) returns an empty DataFrame. The input DataFrame is not
  modified.
* The expression is validated with a regex and evaluated in two passes
  (multiply, then add/subtract) – no `eval`, so only the allowed grammar can run.

**Assumption:** the task example shows the result column as `price_total` while
passing `new_column="total"`. I treat that as a typo and name the column exactly
`new_column`, which is also what the sample tests expect.

## Part 2 – pipeline

`load_sales()` reads the file as text, fixes the issues below and returns typed
rows; `revenue_by_region()` adds `revenue = quantity * unit_price - discount`
with `add_virtual_column` and sums it per region.

### Problems found in `sales.csv`

Found by reading the file as text and, for each column, printing every value
that does not match what a good value should look like (see `explore.py`).

| Problem | Rows | Fix |
|---------|-----:|-----|
| Header `Quantity ` has a trailing space | – | Strip headers, rename all columns to snake_case |
| Header line repeated in the middle of the file | 1 | Dropped |
| `TOTAL,,,37150,,65924.67,` footer | 1 | Dropped – not an order |
| Identical order lines exported twice (`SO-10305`, `SO-10822`, `SO-10966`, `SO-11240`, `SO-11405`) | 5 | `drop_duplicates()` |
| Region with spaces / wrong case (`" North"`, `"west  "`, `"EAST"`) | 15 | `strip()` + `title()` → 5 regions |
| Quantity with space as thousands separator (`"1 762"`) | 4 | Remove space → 1762 |
| Negative quantity (`-2` … `-5`) | 6 | **Kept** – treated as returns, they reduce revenue |
| Unit price with decimal comma (`"59,00"`) | 7 | `,` → `.` |
| Unit price missing | 4 | Filled from the same product (every product has one price in the file) |
| Discount empty | 959 | `0` – no discount |

After cleaning: 1 500 rows, unique order IDs, no missing values.

Checked and fine: order IDs all match `SO-nnnnn`, dates are all valid
`YYYY-MM-DD`, product names are consistent, no discount exceeds its line value.

### Assumptions

* Discount is an absolute amount per line (as stated), not a percentage.
* Negative quantities are returns and should lower revenue. Dropping them or
  flipping the sign would overstate it.
* `"1 762"` is a real quantity of 1762 (locale formatting), not a typo.
* Two identical lines with the same order ID are the same line twice, not two
  orders.
* Output has one row per region, sorted by name, revenue rounded to 2 decimals.
