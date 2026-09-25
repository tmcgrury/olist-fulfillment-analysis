import pandas as pd

orders = pd.read_csv("data/processed/orders_with_metrics.csv")
customers = pd.read_csv("data/raw/olist_customers_dataset.csv")

orders_states = orders.merge(
    customers[["customer_id", "customer_state"]],
    on="customer_id",
    how="inner",
)

print("Rows before join:", len(orders))
print("Rows after join (should be 96470):", len(orders_states))
print("Missing customer_state (should be 0):", orders_states["customer_state"].isna().sum())
print("Duplicate order_ids (should be 0):", orders_states["order_id"].duplicated().sum())

orders_states["delivery_days"] = pd.to_timedelta(orders_states["delivery_time"]).dt.days

by_state = orders_states.groupby("customer_state").agg(
    orders=("order_id", "count"),
    late_rate=("is_late", "mean"),
    late_orders=("is_late", "sum"),
    median_delivery_days=("delivery_days", "median"),
)
by_state["late_rate"] = by_state["late_rate"] * 100
by_state = by_state.sort_values("late_rate", ascending=False)

print("Late rate (%) and median delivery days by customer state:")
print(by_state.round(1).to_string())
print("Total orders across states (should be 96470):", by_state["orders"].sum())
print("Total late orders across states (should be 6534):", by_state["late_orders"].sum())

by_state.to_csv("data/processed/late_rate_by_state.csv")
print("Saved to data/processed/late_rate_by_state.csv")
