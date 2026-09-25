import pandas as pd

data = pd.read_csv("data/processed/orders_reviews.csv")

data["is_one_star"] = data["review_score"] == 1

summary = data.groupby("is_late").agg(
    orders=("order_id", "count"),
    avg_score=("review_score", "mean"),
    pct_one_star=("is_one_star", "mean"),
)
summary["pct_one_star"] = summary["pct_one_star"] * 100
print("Review scores: on time (False) vs late (True)")
print(summary.round(2))

print("Score distribution (% of orders in each group):")
distribution = pd.crosstab(data["is_late"], data["review_score"], normalize="index") * 100
print(distribution.round(1))

without_suspicious = data[~data["suspicious_date"]]
print("Average score without suspicious orders:")
print(without_suspicious.groupby("is_late")["review_score"].mean().round(2))

delivered = pd.to_datetime(data["order_delivered_customer_date"]).dt.normalize()
estimated = pd.to_datetime(data["order_estimated_delivery_date"])
data["days_late"] = (delivered - estimated).dt.days

print("Orders with days_late > 0:", (data["days_late"] > 0).sum())
print("Orders with is_late True: ", data["is_late"].sum())
print("Missing days_late:", data["days_late"].isna().sum())
print("days_late summary:")
print(data["days_late"].describe().round(1))

bin_edges = [float("-inf"), -1, 0, 3, 7, 14, float("inf")]
bin_labels = ["Early", "On the day", "1-3 days late", "4-7 days late", "8-14 days late", "15+ days late"]
data["lateness_group"] = pd.cut(data["days_late"], bins=bin_edges, labels=bin_labels)

print("Missing lateness_group (should be 0):", data["lateness_group"].isna().sum())
print("Early count check:", (data["days_late"] < 0).sum())

by_group = data.groupby("lateness_group", observed=True).agg(
    orders=("order_id", "count"),
    avg_score=("review_score", "mean"),
    pct_one_star=("is_one_star", "mean"),
)
by_group["pct_one_star"] = by_group["pct_one_star"] * 100
print("Review scores by lateness group:")
print(by_group.round(2))
print("Total orders across groups (should be 95824):", by_group["orders"].sum())

by_group.to_csv("data/processed/score_by_lateness.csv")
print("Saved to data/processed/score_by_lateness.csv")
