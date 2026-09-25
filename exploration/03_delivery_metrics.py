import pandas as pd

orders = pd.read_csv("data/processed/delivered_orders.csv")

date_columns = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

print("Data types BEFORE:")
print(orders[date_columns].dtypes)

missing_before = orders[date_columns].isna().sum()

for column in date_columns:
    orders[column] = pd.to_datetime(orders[column])

print("Data types AFTER:")
print(orders[date_columns].dtypes)

print("Missing values before vs after (should match):")
print(pd.DataFrame({"before": missing_before, "after": orders[date_columns].isna().sum()}))

print("Earliest and latest date in each column:")
print(orders[date_columns].agg(["min", "max"]).T)

orders["delivery_time"] = orders["order_delivered_customer_date"] - orders["order_purchase_timestamp"]

print("delivery_time data type:", orders["delivery_time"].dtype)
print("delivery_time missing:", orders["delivery_time"].isna().sum())
print("delivery_time negative:", (orders["delivery_time"] < pd.Timedelta(0)).sum())
print("delivery_time shortest, median, longest:")
print(orders["delivery_time"].agg(["min", "median", "max"]))

slowest = orders.sort_values("delivery_time", ascending=False).head(10)
print("10 slowest orders:")
print(slowest[["order_purchase_timestamp", "order_delivered_carrier_date",
               "order_delivered_customer_date", "order_estimated_delivery_date",
               "delivery_time"]].to_string())

print("Orders taking more than 60 days:", (orders["delivery_time"] > pd.Timedelta(days=60)).sum())

delivered_day = orders["order_delivered_customer_date"].dt.date
print("Busiest delivery days (all orders):")
print(delivered_day.value_counts().head(5))

on_sept_19 = delivered_day == pd.Timestamp("2017-09-19").date()
is_very_slow = orders["delivery_time"] > pd.Timedelta(days=60)
print("Delivered on 2017-09-19:", on_sept_19.sum())
print("...of which took more than 60 days:", (on_sept_19 & is_very_slow).sum())

orders["suspicious_date"] = on_sept_19 & is_very_slow

print("suspicious_date counts:")
print(orders["suspicious_date"].value_counts())
print("Total rows (should still be 96470):", len(orders))
print("Median delivery time, all orders:       ", orders["delivery_time"].median())
print("Median delivery time, without suspicious:", orders.loc[~orders["suspicious_date"], "delivery_time"].median())

orders["is_late"] = orders["order_delivered_customer_date"].dt.normalize() > orders["order_estimated_delivery_date"]

late_rule_a = orders["order_delivered_customer_date"] > orders["order_estimated_delivery_date"]
print("Late rate, rule A (exact times, not used):", round(late_rule_a.mean() * 100, 2), "%")
print("Late rate, rule B (calendar days, chosen):", round(orders["is_late"].mean() * 100, 2), "%")
print("is_late counts:")
print(orders["is_late"].value_counts())
print("Late rate without suspicious orders:", round(orders.loc[~orders["suspicious_date"], "is_late"].mean() * 100, 2), "%")
print("Total rows (should still be 96470):", len(orders))

orders.to_csv("data/processed/orders_with_metrics.csv", index=False)
print("Saved to data/processed/orders_with_metrics.csv")
