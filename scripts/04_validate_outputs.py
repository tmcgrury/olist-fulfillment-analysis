"""
04_validate_outputs.py
Checks the pipeline outputs against the raw data and the approved definitions.
Reads data/raw/ and data/processed/. Changes no data.
Writes the results to docs/validation_report.md.
"""
import pandas as pd

RAW = "data/raw/"
PROCESSED = "data/processed/"

results = []  # one entry per check: (group, check, expected, actual, passed)


def check(group, name, expected, actual, passed=None):
    """Record one check. If passed isn't given, it passes when expected == actual."""
    if passed is None:
        passed = expected == actual
    results.append((group, name, expected, actual, "PASS" if passed else "FAIL"))


# ---------------------------------------------------------------
# Load raw and processed tables
# ---------------------------------------------------------------
raw = {
    "orders": pd.read_csv(RAW + "olist_orders_dataset.csv"),
    "customers": pd.read_csv(RAW + "olist_customers_dataset.csv"),
    "order_items": pd.read_csv(RAW + "olist_order_items_dataset.csv"),
    "order_payments": pd.read_csv(RAW + "olist_order_payments_dataset.csv"),
    "order_reviews": pd.read_csv(RAW + "olist_order_reviews_dataset.csv"),
    "products": pd.read_csv(RAW + "olist_products_dataset.csv"),
    "sellers": pd.read_csv(RAW + "olist_sellers_dataset.csv"),
}

order_dates = ["purchase_date", "approval_date", "carrier_handoff_date", "delivered_date", "estimated_date", "shipping_deadline"]
fact_orders = pd.read_csv(PROCESSED + "fact_orders.csv", parse_dates=order_dates)
fact_order_items = pd.read_csv(PROCESSED + "fact_order_items.csv")
fact_payments = pd.read_csv(PROCESSED + "fact_payments.csv")
fact_reviews = pd.read_csv(PROCESSED + "fact_reviews.csv")
dim_customer = pd.read_csv(PROCESSED + "dim_customer.csv")
dim_seller = pd.read_csv(PROCESSED + "dim_seller.csv")
dim_product = pd.read_csv(PROCESSED + "dim_product.csv")
dim_date = pd.read_csv(PROCESSED + "dim_date.csv")

# ---------------------------------------------------------------
# 1. Row counts reconcile (raw -> processed)
# ---------------------------------------------------------------
pairs = [
    ("orders", fact_orders, "fact_orders"),
    ("customers", dim_customer, "dim_customer"),
    ("order_items", fact_order_items, "fact_order_items"),
    ("order_payments", fact_payments, "fact_payments"),
    ("order_reviews", fact_reviews, "fact_reviews"),
    ("products", dim_product, "dim_product"),
    ("sellers", dim_seller, "dim_seller"),
]
for raw_name, table, processed_name in pairs:
    check("1. Row counts", f"{raw_name} -> {processed_name}", len(raw[raw_name]), len(table))

# ---------------------------------------------------------------
# 2. Money is not inflated by joins (totals match to the cent)
# ---------------------------------------------------------------
def money(value):
    return round(float(value), 2)


def markdown_table(table):
    """Turn a DataFrame into a Markdown table (header row, divider row, one row per record)."""
    header = "| " + " | ".join(str(c) for c in table.columns) + " |"
    divider = "|" + "---|" * len(table.columns)
    rows = ["| " + " | ".join(str(v) for v in row) + " |" for row in table.itertuples(index=False)]
    return "\n".join([header, divider] + rows)

check("2. Money totals", "Item prices: raw vs fact_orders.order_value",
      money(raw["order_items"]["price"].sum()), money(fact_orders["order_value"].sum()))
check("2. Money totals", "Item freight: raw vs fact_orders.freight_cost",
      money(raw["order_items"]["freight_value"].sum()), money(fact_orders["freight_cost"].sum()))
check("2. Money totals", "Item prices: raw vs fact_order_items",
      money(raw["order_items"]["price"].sum()), money(fact_order_items["price"].sum()))
check("2. Money totals", "Payments: raw vs fact_payments",
      money(raw["order_payments"]["payment_value"].sum()), money(fact_payments["payment_value"].sum()))

# ---------------------------------------------------------------
# 3. Primary keys are unique
# ---------------------------------------------------------------
keys = [
    ("fact_orders", fact_orders, ["order_id"]),
    ("fact_order_items", fact_order_items, ["order_id", "order_item_id"]),
    ("fact_payments", fact_payments, ["order_id", "payment_sequential"]),
    ("fact_reviews", fact_reviews, ["review_id", "order_id"]),
    ("dim_customer", dim_customer, ["customer_id"]),
    ("dim_seller", dim_seller, ["seller_id"]),
    ("dim_product", dim_product, ["product_id"]),
    ("dim_date", dim_date, ["date"]),
]
for name, table, key in keys:
    check("3. Unique keys", f"{name}: {' + '.join(key)} duplicates", 0, int(table.duplicated(subset=key).sum()))
check("3. Unique keys", "fact_orders.seller_id blank exactly when seller_count is not 1 (mismatches)", 0,
      int((fact_orders["seller_id"].isna() != (fact_orders["seller_count"] != 1)).sum()))
check("3. Unique keys", "fact_orders.seller_id values all exist in dim_seller (unmatched)", 0,
      int((~fact_orders["seller_id"].dropna().isin(dim_seller["seller_id"])).sum()))
check("3. Unique keys", "fact_reviews: exactly one latest review per reviewed order",
      int(fact_reviews["order_id"].nunique()), int(fact_reviews["is_latest_for_order"].sum()))

# ---------------------------------------------------------------
# 4. Durations follow logical date sequences
# ---------------------------------------------------------------
check("4. Date logic", "Negative transit_time", 0, int((fact_orders["transit_time"] < 0).sum()))
check("4. Date logic", "Negative total_delivery_time", 0, int((fact_orders["total_delivery_time"] < 0).sum()))
check("4. Date logic", "Negative approval_time", 0, int((fact_orders["approval_time"] < 0).sum()))
check("4. Date logic", "Late orders that are not delivered", 0, int((fact_orders["is_late"] & ~fact_orders["is_delivered"]).sum()))

# ---------------------------------------------------------------
# 5. Calculated fields reproduce when recalculated a different way
# ---------------------------------------------------------------
delivered = fact_orders[fact_orders["is_delivered"]]

# is_late, recalculated by comparing the date text "YYYY-MM-DD" (no date maths at all)
late_by_text = delivered["delivered_date"].dt.strftime("%Y-%m-%d") > delivered["estimated_date"].dt.strftime("%Y-%m-%d")
check("5. Recalculation", "is_late vs date-text comparison (mismatches)", 0, int((late_by_text != delivered["is_late"]).sum()))

# is_late must agree with delivery_variance > 0
check("5. Recalculation", "is_late vs delivery_variance > 0 (mismatches)", 0,
      int(((delivered["delivery_variance"] > 0) != delivered["is_late"]).sum()))

# freight_pct, recalculated from fact_order_items
per_order = fact_order_items.groupby("order_id")[["price", "freight_value"]].sum()
recalculated_pct = per_order["freight_value"] / per_order["price"] * 100
stored_pct = fact_orders.set_index("order_id")["freight_pct"].dropna()
# Decimals are compared with a tolerance, not exact equality: computers store decimals
# in binary, so the same calculation done two ways can differ in the 15th decimal place
difference = (recalculated_pct.reindex(stored_pct.index) - stored_pct).abs()
check("5. Recalculation", "freight_pct vs recalculated from items (differences > 0.000001)", 0,
      int((difference > 0.000001).sum()))

on_time_rate = round((~delivered["is_late"]).mean() * 100, 2)
late_rate = round(delivered["is_late"].mean() * 100, 2)
check("5. Recalculation", "On-time rate + late rate = 100%", 100.0, round(on_time_rate + late_rate, 2))

# ---------------------------------------------------------------
# 6. Known results from exploration are reproduced
# ---------------------------------------------------------------
check("6. Known results", "Delivered orders", 96470, int(fact_orders["is_delivered"].sum()))
check("6. Known results", "Late orders", 6534, int(fact_orders["is_late"].sum()))
check("6. Known results", "Late rate %", 6.77, late_rate)
check("6. Known results", "Valid transit time orders (96,470 - 24)", 96446, int(fact_orders["valid_transit_time"].sum()))
check("6. Known results", "Suspicious-date orders", 28, int(fact_orders["suspicious_date"].sum()))
check("6. Known results", "Delivered orders with a review", 95824, int(delivered["review_score"].notna().sum()))
check("6. Known results", "Delivered single-category orders (main_category filled, Q7)", 95690, int(delivered["main_category"].notna().sum()))
check("6. Known results", "Delivered orders with a known weight (Q7)", 96448, int(delivered["order_weight_kg"].notna().sum()))
check("6. Known results", "Office furniture late rate % (Q7)", 8.15,
      round(delivered.loc[delivered["main_category"] == "office_furniture", "is_late"].mean() * 100, 2))

# ---------------------------------------------------------------
# 7. Cleaning log #21: is the 13,664 payment real?
# ---------------------------------------------------------------
big = fact_payments.loc[fact_payments["payment_value"].idxmax()]
big_order = fact_orders.set_index("order_id").loc[big["order_id"]]
order_paid = fact_payments.loc[fact_payments["order_id"] == big["order_id"], "payment_value"].sum()
items_total = big_order["order_value"] + big_order["freight_cost"]
check("7. Cleaning log #21", f"Largest payment ({money(big['payment_value'])}) = its order's items + freight",
      money(items_total), money(order_paid), passed=abs(items_total - order_paid) < 1)

# ---------------------------------------------------------------
# 8. Manual examples: one real order per scenario, for a person to inspect
# ---------------------------------------------------------------
same_day = delivered["delivered_date"].dt.normalize() == delivered["estimated_date"]
scenarios = {
    "A. Early": delivered[delivered["delivery_variance"] < -5],
    "B. On the promised day, afternoon": delivered[same_day & (delivered["delivered_date"].dt.hour >= 12)],
    "C. One day late": delivered[delivered["delivery_variance"] == 1],
    "D. Very late": delivered[delivered["delivery_variance"] > 30],
    "E. Canceled": fact_orders[fact_orders["order_status"] == "canceled"],
    "F. Delivered before carrier pickup": delivered[delivered["carrier_handoff_date"] > delivered["delivered_date"]],
}
example_columns = ["order_id", "order_status", "carrier_handoff_date", "delivered_date", "estimated_date",
                   "is_delivered", "is_late", "delivery_variance", "transit_time"]
examples = pd.concat(
    [rows.head(1)[example_columns].assign(scenario=name) for name, rows in scenarios.items()]
)[["scenario"] + example_columns]

# ---------------------------------------------------------------
# Write the report
# ---------------------------------------------------------------
report = pd.DataFrame(results, columns=["Group", "Check", "Expected", "Actual", "Result"])
passed = (report["Result"] == "PASS").sum()

lines = [
    "# Validation Report",
    "",
    "Generated by `scripts/04_validate_outputs.py`. Re-run it after any change to the pipeline.",
    "",
    f"**{passed} of {len(report)} checks passed.**",
    "",
    "## Automated checks",
    "",
    markdown_table(report),
    "",
    "## Manual examples",
    "",
    "One real order per scenario. Check by eye that `is_late`, `delivery_variance` and `transit_time`",
    "follow the definitions in [business_questions.md](business_questions.md).",
    "",
    markdown_table(examples),
    "",
    "## Excel and Power BI",
    "",
    "- **Excel** (`excel/olist_fulfillment_analysis.xlsx`): its Data Validation sheet compares 10 Excel",
    "  formula results with Python. Result on 2026-09-22: 10 of 10 PASS.",
    "- **Power BI** (`powerbi/olist_fulfillment_dashboard.pbix`): 12 DAX measures checked by hand against",
    "  Python on 2026-09-22, all matched: Delivered Orders 96,470; Late Orders 6,534; Late Rate 6.77%;",
    "  On-Time Rate 93.23%; Median Delivery Days 10.22; Avg Delivery Days 12.56; Median Transit Days 7.10;",
    "  Median Days vs Promise -12; Avg Review Score 4.16; One-Star Rate 9.76%; Seller Late Rate 9.13%;",
    "  Freight % 16.57%. All 8 table row counts also matched after loading.",
]
with open("docs/validation_report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(report.to_string(index=False))
print()
print(f"{passed} of {len(report)} checks passed. Report saved to docs/validation_report.md")
print()
print(examples.to_string(index=False))
