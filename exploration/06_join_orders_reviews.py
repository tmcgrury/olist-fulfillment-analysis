import pandas as pd

orders = pd.read_csv("data/processed/orders_with_metrics.csv")
reviews = pd.read_csv("data/processed/latest_reviews.csv")

orders_reviews = orders.merge(
    reviews[["order_id", "review_score"]],
    on="order_id",
    how="inner",
)

print("Orders:        ", len(orders))
print("Reviews:       ", len(reviews))
print("Joined rows:   ", len(orders_reviews))
print("Orders with no review (dropped):", len(orders) - len(orders_reviews))
print("Duplicate order_ids after join (should be 0):", orders_reviews["order_id"].duplicated().sum())
print("Missing review scores (should be 0):", orders_reviews["review_score"].isna().sum())

orders_reviews.to_csv("data/processed/orders_reviews.csv", index=False)
print("Saved to data/processed/orders_reviews.csv")
