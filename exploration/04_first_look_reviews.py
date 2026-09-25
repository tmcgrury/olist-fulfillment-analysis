import pandas as pd

reviews = pd.read_csv("data/raw/olist_order_reviews_dataset.csv")

print("Rows and columns:", reviews.shape)
print("Columns:")
print(list(reviews.columns))

print("Missing values per column:")
print(reviews.isna().sum())

print("Review scores:")
print(reviews["review_score"].value_counts().sort_index())

reviews_per_order = reviews["order_id"].value_counts()
print("Reviews per order:")
print(reviews_per_order.value_counts().sort_index())
