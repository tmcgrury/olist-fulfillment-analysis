import pandas as pd

customers = pd.read_csv("data/raw/olist_customers_dataset.csv")
orders = pd.read_csv("data/processed/orders_with_metrics.csv")

print("Rows and columns:", customers.shape)
print("Columns:", list(customers.columns))
print(customers.head(3).to_string())

print("Missing values per column:")
print(customers.isna().sum())

print("Duplicate customer_ids (0 means one row per customer_id):", customers["customer_id"].duplicated().sum())
print("Unique customer_unique_ids:", customers["customer_unique_id"].nunique())

print("Number of states:", customers["customer_state"].nunique())

matched = orders["customer_id"].isin(customers["customer_id"])
print("Delivered orders with a matching customer:", matched.sum(), "of", len(orders))
