import pandas as pd

orders = pd.read_csv("data/processed/orders_with_metrics.csv")
customers = pd.read_csv("data/raw/olist_customers_dataset.csv")

orders = orders.merge(customers[["customer_id", "customer_state"]], on="customer_id", how="inner")

orders["purchase_month"] = pd.to_datetime(orders["order_purchase_timestamp"]).dt.to_period("M").astype(str)
orders["in_spike"] = orders["purchase_month"].isin(["2018-02", "2018-03"])

print("Rows (should be 96470):", len(orders))
print("Orders in spike (Feb-Mar 2018):", orders["in_spike"].sum())
print("Late orders in spike:", orders.loc[orders["in_spike"], "is_late"].sum())

by_state = orders.groupby(["customer_state", "in_spike"])["is_late"].agg(["count", "mean", "sum"])
late_rate = (by_state["mean"] * 100).unstack()
late_rate.columns = ["other_months_rate", "spike_rate"]
late_rate["spike_orders"] = by_state["count"].unstack()[True]
late_rate["spike_late_orders"] = by_state["sum"].unstack()[True]
late_rate["share_of_spike_late"] = late_rate["spike_late_orders"] / late_rate["spike_late_orders"].sum() * 100
late_rate = late_rate.sort_values("spike_late_orders", ascending=False)

print("Late rate (%) in the spike vs other months, by state (sorted by late orders in spike):")
print(late_rate.round(1).head(10).to_string())
print("Spike late orders across states (should match above):", late_rate["spike_late_orders"].sum())
