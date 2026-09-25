import pandas as pd

orders = pd.read_csv("data/raw/olist_orders_dataset.csv")

print("Columns:")
print(orders.columns)

print("First 5 rows:")
print(orders.head())

print("Rows and columns:")
print(orders.shape)

print("Missing values per column:")
print(orders.isna().sum())

print("Orders per status:")
print(orders["order_status"].value_counts())

is_delivered = orders["order_status"] == "delivered"
has_no_date = orders["order_delivered_customer_date"].isna()

print("Delivered but no delivery date:")
print((is_delivered & has_no_date).sum())

print("Not delivered but has a delivery date:")
print((~is_delivered & ~has_no_date).sum())
