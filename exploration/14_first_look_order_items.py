import pandas as pd

items = pd.read_csv("data/raw/olist_order_items_dataset.csv")

print("Rows and columns:", items.shape)
print("Columns:", list(items.columns))
print(items.head(3).to_string())

print("Missing values per column:")
print(items.isna().sum())

items_per_order = items.groupby("order_id")["order_item_id"].count()
print("Items per order (how many orders have 1 item, 2 items, ...):")
print(items_per_order.value_counts().sort_index().head(8))

sellers_per_order = items.groupby("order_id")["seller_id"].nunique()
print("Sellers per order:")
print(sellers_per_order.value_counts().sort_index())

print("Number of distinct sellers:", items["seller_id"].nunique())
