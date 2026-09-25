import pandas as pd

orders = pd.read_csv("data/raw/olist_orders_dataset.csv")

is_delivered = orders["order_status"] == "delivered"
has_date = orders["order_delivered_customer_date"].notna()

delivered_orders = orders[is_delivered & has_date]

print("Rows before:", len(orders))
print("Rows after: ", len(delivered_orders))
print("Rows removed:", len(orders) - len(delivered_orders))

delivered_orders.to_csv("data/processed/delivered_orders.csv", index=False)
print("Saved to data/processed/delivered_orders.csv")
