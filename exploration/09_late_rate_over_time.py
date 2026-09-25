import pandas as pd

orders = pd.read_csv("data/processed/orders_with_metrics.csv")

orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])
orders["purchase_month"] = orders["order_purchase_timestamp"].dt.to_period("M")

print("Missing purchase_month (should be 0):", orders["purchase_month"].isna().sum())
print("Total rows (should be 96470):", len(orders))

by_month = orders.groupby("purchase_month").agg(
    orders=("order_id", "count"),
    late_rate=("is_late", "mean"),
)
by_month["late_rate"] = by_month["late_rate"] * 100

print("Orders and late rate (%) by purchase month:")
print(by_month.round(1).to_string())
print("Total orders across months (should be 96470):", by_month["orders"].sum())

by_month.to_csv("data/processed/late_rate_by_month.csv")
print("Saved to data/processed/late_rate_by_month.csv")
