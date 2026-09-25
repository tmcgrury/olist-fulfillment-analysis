import pandas as pd

orders = pd.read_csv("data/processed/orders_with_metrics.csv")
items = pd.read_csv("data/raw/olist_order_items_dataset.csv")

per_order = items.groupby("order_id").agg(
    n_sellers=("seller_id", "nunique"),
    seller_id=("seller_id", "first"),
    shipping_limit_date=("shipping_limit_date", "max"),
    n_limit_dates=("shipping_limit_date", "nunique"),
)
print("Orders in items table:", len(per_order))
print("Multi-seller orders (Decision A: left out):", (per_order["n_sellers"] > 1).sum())

single_seller = per_order[per_order["n_sellers"] == 1]
print("Single-seller orders with more than one shipping deadline:", (single_seller["n_limit_dates"] > 1).sum())

data = orders.merge(single_seller[["seller_id", "shipping_limit_date"]], on="order_id", how="inner")
print("Delivered orders before join:", len(orders))
print("Delivered single-seller orders after join:", len(data))
print("Duplicate order_ids (should be 0):", data["order_id"].duplicated().sum())

carrier_date = pd.to_datetime(data["order_delivered_carrier_date"])
limit_date = pd.to_datetime(data["shipping_limit_date"])
print("Orders missing a carrier date (seller_late can't be judged):", carrier_date.isna().sum())

data["seller_late"] = carrier_date > limit_date

data["purchase_month"] = pd.to_datetime(data["order_purchase_timestamp"]).dt.to_period("M").astype(str)
data["in_spike"] = data["purchase_month"].isin(["2018-02", "2018-03"])

def summarize(group):
    return pd.Series({
        "orders": len(group),
        "seller_late_%": group["seller_late"].mean() * 100,
        "customer_late_%": group["is_late"].mean() * 100,
        "late_when_seller_on_time_%": group.loc[~group["seller_late"], "is_late"].mean() * 100,
        "late_when_seller_late_%": group.loc[group["seller_late"], "is_late"].mean() * 100,
    })

result = data.groupby("in_spike")[["seller_late", "is_late"]].apply(summarize)
result.index = ["Other months", "Feb-Mar 2018"]
print("Seller vs carrier, spike vs other months:")
print(result.round(1).to_string())

late = data[data["is_late"]]
print("Share of late orders where the seller was ALSO late:")
print((late.groupby("in_spike")["seller_late"].mean() * 100).round(1).rename(index={False: "Other months", True: "Feb-Mar 2018"}))
