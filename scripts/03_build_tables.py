"""
03_build_tables.py
Builds the analytical tables (4 facts + 4 dimensions) from the clean tables in data/interim/.
Adds the calculated fields and flags defined in docs/business_questions.md.
Writes to data/processed/. No rows are removed - exclusions are flags.
"""
import pandas as pd

INTERIM = "data/interim/"
PROCESSED = "data/processed/"
DAY = pd.Timedelta(days=1)

# ---------------------------------------------------------------
# Section 1: Load the clean tables
# CSV files forget data types, so zip codes are re-read as text
# and dates are converted again
# ---------------------------------------------------------------
orders = pd.read_csv(INTERIM + "orders.csv", parse_dates=[
    "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
    "order_delivered_customer_date", "order_estimated_delivery_date"])
customers = pd.read_csv(INTERIM + "customers.csv", dtype={"customer_zip_code_prefix": str})
order_items = pd.read_csv(INTERIM + "order_items.csv", parse_dates=["shipping_limit_date"])
order_payments = pd.read_csv(INTERIM + "order_payments.csv", dtype={"payment_installments": "Int64"})
order_reviews = pd.read_csv(INTERIM + "order_reviews.csv", parse_dates=["review_creation_date", "review_answer_timestamp"])
products = pd.read_csv(INTERIM + "products.csv")
sellers = pd.read_csv(INTERIM + "sellers.csv", dtype={"seller_zip_code_prefix": str})
category_translation = pd.read_csv(INTERIM + "category_translation.csv")

# ---------------------------------------------------------------
# Section 2: fact_orders - dates (renamed to the defined field names)
# ---------------------------------------------------------------
fact_orders = orders.rename(columns={
    "order_purchase_timestamp": "purchase_date",
    "order_approved_at": "approval_date",
    "order_delivered_carrier_date": "carrier_handoff_date",
    "order_delivered_customer_date": "delivered_date",
    "order_estimated_delivery_date": "estimated_date",
})

# ---------------------------------------------------------------
# Section 3: fact_orders - summaries from order items (one row per order)
# Summed BEFORE joining so the join cannot multiply orders
# ---------------------------------------------------------------
items_per_order = order_items.groupby("order_id").agg(
    order_item_count=("order_item_id", "count"),
    seller_count=("seller_id", "nunique"),
    order_value=("price", "sum"),
    freight_cost=("freight_value", "sum"),
    shipping_deadline=("shipping_limit_date", "max"),
    seller_id=("seller_id", "first"),
).reset_index()
# #15: an order is attributed to a seller only when all its items come from one seller
items_per_order.loc[items_per_order["seller_count"] != 1, "seller_id"] = None

# Product details per order (same approach as Q7 in 06_answer_questions.py):
# main_category only when all items share one category; weight only when every item's weight is known
product_details = products.merge(category_translation, on="product_category_name", how="left")
product_details["category_english"] = product_details["product_category_name_english"].fillna("unknown")
item_products = order_items.merge(product_details[["product_id", "category_english", "product_weight_g"]],
                                  on="product_id", how="left")
assert len(item_products) == len(order_items), "Join changed the number of items!"
products_per_order = item_products.groupby("order_id").agg(
    category_count=("category_english", "nunique"),
    main_category=("category_english", "first"),
    order_weight_kg=("product_weight_g", lambda w: w.sum() / 1000 if w.notna().all() else None),
).reset_index()
products_per_order.loc[products_per_order["category_count"] != 1, "main_category"] = None
items_per_order = items_per_order.merge(products_per_order.drop(columns="category_count"), on="order_id", how="left")

rows_before = len(fact_orders)
fact_orders = fact_orders.merge(items_per_order, on="order_id", how="left")
assert len(fact_orders) == rows_before, "Join changed the number of orders!"

fact_orders["order_item_count"] = fact_orders["order_item_count"].fillna(0).astype(int)
fact_orders["seller_count"] = fact_orders["seller_count"].fillna(0).astype(int)
fact_orders["freight_pct"] = fact_orders["freight_cost"] / fact_orders["order_value"] * 100

# ---------------------------------------------------------------
# Section 4: fact_orders - flags
# ---------------------------------------------------------------
fact_orders["is_delivered"] = (fact_orders["order_status"] == "delivered") & fact_orders["delivered_date"].notna()

delivered_day = fact_orders["delivered_date"].dt.normalize()
fact_orders["is_late"] = fact_orders["is_delivered"] & (delivered_day > fact_orders["estimated_date"])

fact_orders["valid_transit_time"] = (
    fact_orders["is_delivered"]
    & fact_orders["carrier_handoff_date"].notna()
    & (fact_orders["carrier_handoff_date"] <= fact_orders["delivered_date"])
)

fact_orders["seller_late"] = (fact_orders["seller_count"] == 1) & (fact_orders["carrier_handoff_date"] > fact_orders["shipping_deadline"])

# ---------------------------------------------------------------
# Section 5: fact_orders - durations in days (blank where not valid)
# .where(condition) keeps a value where the condition is True, blank elsewhere
# ---------------------------------------------------------------
fact_orders["approval_time"] = (fact_orders["approval_date"] - fact_orders["purchase_date"]) / DAY
fact_orders["fulfillment_time"] = (fact_orders["carrier_handoff_date"] - fact_orders["approval_date"]) / DAY
fact_orders["transit_time"] = ((fact_orders["delivered_date"] - fact_orders["carrier_handoff_date"]) / DAY).where(fact_orders["valid_transit_time"])
fact_orders["total_delivery_time"] = ((fact_orders["delivered_date"] - fact_orders["purchase_date"]) / DAY).where(fact_orders["is_delivered"])
fact_orders["delivery_variance"] = ((delivered_day - fact_orders["estimated_date"]).dt.days).where(fact_orders["is_delivered"]).astype("Int64")

fact_orders["suspicious_date"] = (
    (fact_orders["delivered_date"].dt.date == pd.Timestamp("2017-09-19").date())
    & (fact_orders["total_delivery_time"] > 60)
)

# ---------------------------------------------------------------
# Section 6: fact_reviews + review fields on fact_orders
# #12: the most recent review per order is flagged is_latest_for_order
# ---------------------------------------------------------------
fact_reviews = order_reviews.sort_values(["order_id", "review_creation_date", "review_answer_timestamp"]).copy()
fact_reviews["is_latest_for_order"] = ~fact_reviews.duplicated(subset="order_id", keep="last")

latest_reviews = fact_reviews.loc[fact_reviews["is_latest_for_order"], ["order_id", "review_score"]]
rows_before = len(fact_orders)
fact_orders = fact_orders.merge(latest_reviews, on="order_id", how="left")
assert len(fact_orders) == rows_before, "Join changed the number of orders!"

fact_orders["review_score"] = fact_orders["review_score"].astype("Int64")
fact_orders["review_group"] = fact_orders["review_score"].map({1: "Negative", 2: "Negative", 3: "Neutral", 4: "Positive", 5: "Positive"})

# ---------------------------------------------------------------
# Section 7: fact_order_items and fact_payments
# ---------------------------------------------------------------
fact_order_items = order_items.merge(fact_orders[["order_id", "carrier_handoff_date"]], on="order_id", how="left")
fact_order_items["seller_late"] = fact_order_items["carrier_handoff_date"] > fact_order_items["shipping_limit_date"]
fact_order_items = fact_order_items.drop(columns="carrier_handoff_date")

fact_payments = order_payments.copy()

# ---------------------------------------------------------------
# Section 8: Dimension tables
# ---------------------------------------------------------------
dim_customer = customers.copy()
dim_seller = sellers.copy()

dim_product = products.merge(category_translation, on="product_category_name", how="left")
dim_product["product_category_name_english"] = dim_product["product_category_name_english"].fillna("unknown")

all_dates = pd.concat([fact_orders[c] for c in ["purchase_date", "approval_date", "carrier_handoff_date", "delivered_date", "estimated_date"]]).dropna()
dim_date = pd.DataFrame({"date": pd.date_range(all_dates.min().normalize(), all_dates.max().normalize(), freq="D")})
dim_date["year"] = dim_date["date"].dt.year
dim_date["quarter"] = dim_date["date"].dt.quarter
dim_date["month"] = dim_date["date"].dt.month
dim_date["month_name"] = dim_date["date"].dt.month_name()
dim_date["year_month"] = dim_date["date"].dt.strftime("%Y-%m")
dim_date["weekday"] = dim_date["date"].dt.day_name()
dim_date["is_weekend"] = dim_date["date"].dt.dayofweek >= 5

# ---------------------------------------------------------------
# Section 9: Put fact_orders columns in a readable order, then export
# ---------------------------------------------------------------
fact_orders = fact_orders[[
    "order_id", "customer_id", "seller_id", "order_status",
    "purchase_date", "approval_date", "carrier_handoff_date", "delivered_date", "estimated_date", "shipping_deadline",
    "is_delivered", "is_late", "suspicious_date", "valid_transit_time", "seller_late",
    "approval_time", "fulfillment_time", "transit_time", "total_delivery_time", "delivery_variance",
    "order_item_count", "seller_count", "order_value", "freight_cost", "freight_pct",
    "review_score", "review_group",
    "main_category", "order_weight_kg",  # added at the end so existing column positions don't shift
]]

output_tables = {
    "fact_orders": fact_orders,
    "fact_order_items": fact_order_items,
    "fact_payments": fact_payments,
    "fact_reviews": fact_reviews,
    "dim_customer": dim_customer,
    "dim_seller": dim_seller,
    "dim_product": dim_product,
    "dim_date": dim_date,
}

print("TABLES BUILT")
for name, table in output_tables.items():
    table.to_csv(PROCESSED + name + ".csv", index=False)
    print(f"{name:<18}{len(table):>9} rows {table.shape[1]:>4} columns")
print("Saved to", PROCESSED)
