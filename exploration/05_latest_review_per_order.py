import pandas as pd

reviews = pd.read_csv("data/raw/olist_order_reviews_dataset.csv")

reviews["review_creation_date"] = pd.to_datetime(reviews["review_creation_date"])
reviews["review_answer_timestamp"] = pd.to_datetime(reviews["review_answer_timestamp"])

reviews = reviews.sort_values(["order_id", "review_creation_date", "review_answer_timestamp"])
latest_reviews = reviews.drop_duplicates(subset="order_id", keep="last")

print("Reviews before:", len(reviews))
print("Reviews after: ", len(latest_reviews))
print("Unique orders in raw reviews:", reviews["order_id"].nunique())
print("Duplicate order_ids after (should be 0):", latest_reviews["order_id"].duplicated().sum())

latest_reviews.to_csv("data/processed/latest_reviews.csv", index=False)
print("Saved to data/processed/latest_reviews.csv")
