"""
01_profile_data.py
Profiles every raw table. Reads data/raw/ only. Changes nothing.
"""
import pandas as pd

# ---------------------------------------------------------------
# Section 1: Load every raw table
# ---------------------------------------------------------------
RAW = "data/raw/"

tables = {
    "orders": pd.read_csv(RAW + "olist_orders_dataset.csv"),
    "customers": pd.read_csv(RAW + "olist_customers_dataset.csv"),
    "order_items": pd.read_csv(RAW + "olist_order_items_dataset.csv"),
    "order_payments": pd.read_csv(RAW + "olist_order_payments_dataset.csv"),
    "order_reviews": pd.read_csv(RAW + "olist_order_reviews_dataset.csv"),
    "products": pd.read_csv(RAW + "olist_products_dataset.csv"),
    "sellers": pd.read_csv(RAW + "olist_sellers_dataset.csv"),
    "geolocation": pd.read_csv(RAW + "olist_geolocation_dataset.csv"),
    "category_translation": pd.read_csv(RAW + "product_category_name_translation.csv"),
}

# ---------------------------------------------------------------
# Section 2: Test the predicted primary key of each table
# A key is valid if no combination of its values appears twice.
# ---------------------------------------------------------------
predicted_keys = {
    "orders": ["order_id"],
    "customers": ["customer_id"],
    "order_items": ["order_id", "order_item_id"],
    "order_payments": ["order_id", "payment_sequential"],
    "order_reviews": ["review_id"],
    "products": ["product_id"],
    "sellers": ["seller_id"],
    "geolocation": ["geolocation_zip_code_prefix"],
    "category_translation": ["product_category_name"],
}

print("PRIMARY KEY TEST")
print(f"{'table':<22}{'rows':>10}  {'key':<40}{'duplicate keys':>15}  result")
for name, key in predicted_keys.items():
    table = tables[name]
    duplicate_keys = table.duplicated(subset=key).sum()
    result = "UNIQUE" if duplicate_keys == 0 else "NOT UNIQUE"
    print(f"{name:<22}{len(table):>10}  {' + '.join(key):<40}{duplicate_keys:>15}  {result}")

# ---------------------------------------------------------------
# Section 3: Investigate repeated review_ids
# ---------------------------------------------------------------
reviews = tables["order_reviews"]
repeated = reviews[reviews["review_id"].duplicated(keep=False)]

print()
print("REPEATED REVIEW_IDS")
print("Exact duplicate rows in reviews:", reviews.duplicated().sum())
print("Rows sharing a review_id:", len(repeated))
print("Distinct review_ids involved:", repeated["review_id"].nunique())
print("review_id + order_id duplicates:", reviews.duplicated(subset=["review_id", "order_id"]).sum())

columns_other_than_order = [c for c in reviews.columns if c != "order_id"]
same_apart_from_order = repeated.duplicated(subset=columns_other_than_order, keep=False).sum()
print("Repeated rows identical in every column except order_id:", same_apart_from_order, "of", len(repeated))

example_id = repeated["review_id"].iloc[0]
print("Example:")
print(reviews[reviews["review_id"] == example_id][["review_id", "order_id", "review_score", "review_creation_date"]].to_string())

# ---------------------------------------------------------------
# Section 4: Test foreign keys (does every value point to a real row?)
# (child table, child column, parent table, parent column)
# ---------------------------------------------------------------
foreign_keys = [
    ("orders", "customer_id", "customers", "customer_id"),
    ("order_items", "order_id", "orders", "order_id"),
    ("order_items", "product_id", "products", "product_id"),
    ("order_items", "seller_id", "sellers", "seller_id"),
    ("order_payments", "order_id", "orders", "order_id"),
    ("order_reviews", "order_id", "orders", "order_id"),
    ("products", "product_category_name", "category_translation", "product_category_name"),
    ("customers", "customer_zip_code_prefix", "geolocation", "geolocation_zip_code_prefix"),
    ("sellers", "seller_zip_code_prefix", "geolocation", "geolocation_zip_code_prefix"),
]

print()
print("FOREIGN KEY TEST (values with no match in the parent table)")
print(f"{'child.column':<42}{'-> parent':<24}{'blank':>8}{'unmatched':>11}{'unmatched values':>18}")
relationship_rows = []
for child, child_col, parent, parent_col in foreign_keys:
    values = tables[child][child_col]
    blank = values.isna().sum()
    filled = values.dropna()
    unmatched = ~filled.isin(tables[parent][parent_col])
    print(f"{child + '.' + child_col:<42}{'-> ' + parent:<24}{blank:>8}{unmatched.sum():>11}{filled[unmatched].nunique():>18}")
    relationship_rows.append({
        "child_table": child,
        "child_column": child_col,
        "parent_table": parent,
        "parent_column": parent_col,
        "relationship": "many-to-many" if parent == "geolocation" else "many-to-one",
        "blank_values": blank,
        "unmatched_rows": unmatched.sum(),
        "unmatched_distinct_values": filled[unmatched].nunique(),
    })

untranslated = tables["products"]["product_category_name"].dropna()
untranslated = untranslated[~untranslated.isin(tables["category_translation"]["product_category_name"])]
print("Categories with no English translation:", sorted(untranslated.unique()))

# ---------------------------------------------------------------
# Section 5: Impossible date sequences in orders
# (earlier column, later column) - the earlier date must not be after the later one
# ---------------------------------------------------------------
orders = tables["orders"]
order_dates = {
    "purchase": pd.to_datetime(orders["order_purchase_timestamp"]),
    "approved": pd.to_datetime(orders["order_approved_at"]),
    "carrier": pd.to_datetime(orders["order_delivered_carrier_date"]),
    "delivered": pd.to_datetime(orders["order_delivered_customer_date"]),
    "estimated": pd.to_datetime(orders["order_estimated_delivery_date"]),
}

date_rules = [
    ("purchase", "approved"),
    ("approved", "carrier"),
    ("carrier", "delivered"),
    ("purchase", "delivered"),
    ("purchase", "estimated"),
]

print()
print("DATE SEQUENCE TEST (orders where the earlier date is AFTER the later date)")
print(f"{'rule':<28}{'both dates present':>20}{'violations':>12}{'% of checked':>14}")
for earlier, later in date_rules:
    both_present = order_dates[earlier].notna() & order_dates[later].notna()
    violation = order_dates[earlier] > order_dates[later]
    count = violation.sum()
    pct = count / both_present.sum() * 100
    print(f"{earlier + ' <= ' + later:<28}{both_present.sum():>20}{count:>12}{pct:>13.2f}%")

shipped_before_approved = order_dates["approved"] > order_dates["carrier"]
gap_hours = (order_dates["approved"] - order_dates["carrier"])[shipped_before_approved].dt.total_seconds() / 3600
print()
print("Shipped before approved - how many hours early was the carrier handoff?")
print(gap_hours.describe().round(1).to_string())
print("Status of these orders:", orders.loc[shipped_before_approved, "order_status"].value_counts().to_dict())

delivered_before_carrier = order_dates["carrier"] > order_dates["delivered"]
examples = pd.DataFrame({
    "purchase": order_dates["purchase"],
    "carrier": order_dates["carrier"],
    "delivered": order_dates["delivered"],
    "estimated": order_dates["estimated"],
})[delivered_before_carrier]
examples["days_carrier_after_delivery"] = ((examples["carrier"] - examples["delivered"]).dt.total_seconds() / 86400).round(2)
print()
print("Delivered before carrier pickup - all", len(examples), "orders:")
print(examples.to_string())

# ---------------------------------------------------------------
# Section 6: Numeric columns - zeros, negatives, blanks and extremes
# ---------------------------------------------------------------
numeric_checks = [
    ("order_items", "price"),
    ("order_items", "freight_value"),
    ("order_payments", "payment_value"),
    ("order_payments", "payment_installments"),
    ("order_reviews", "review_score"),
    ("products", "product_weight_g"),
    ("products", "product_length_cm"),
    ("products", "product_height_cm"),
    ("products", "product_width_cm"),
    ("products", "product_photos_qty"),
]

print()
print("NUMERIC CHECK")
print(f"{'table.column':<38}{'blank':>7}{'zeros':>7}{'negative':>9}{'min':>10}{'median':>10}{'99th pct':>10}{'max':>11}")
for table_name, column in numeric_checks:
    values = tables[table_name][column]
    print(f"{table_name + '.' + column:<38}"
          f"{values.isna().sum():>7}"
          f"{(values == 0).sum():>7}"
          f"{(values < 0).sum():>9}"
          f"{values.min():>10.1f}"
          f"{values.median():>10.1f}"
          f"{values.quantile(0.99):>10.1f}"
          f"{values.max():>11.1f}")

payments = tables["order_payments"]
products = tables["products"]
print("Zero-value payments by type:", payments[payments["payment_value"] == 0]["payment_type"].value_counts().to_dict())
print("Zero-installment payments by type:", payments[payments["payment_installments"] == 0]["payment_type"].value_counts().to_dict())
print("Payment types:", payments["payment_type"].value_counts().to_dict())
print("Products with blank category AND blank photo count:",
      (products["product_category_name"].isna() & products["product_photos_qty"].isna()).sum())

# ---------------------------------------------------------------
# Section 7: Text formatting - city and state names
# ---------------------------------------------------------------
import unicodedata

def simplify(text):
    """Lowercase, trim spaces and remove accents, e.g. ' São Paulo ' -> 'sao paulo'."""
    text = str(text).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))

text_checks = [
    ("customers", "customer_city"),
    ("sellers", "seller_city"),
    ("geolocation", "geolocation_city"),
    ("customers", "customer_state"),
    ("sellers", "seller_state"),
]

print()
print("TEXT FORMATTING CHECK")
print(f"{'table.column':<30}{'distinct':>10}{'after simplify':>16}{'has uppercase':>15}{'extra spaces':>14}{'has accents':>13}{'has digits':>12}")
for table_name, column in text_checks:
    values = tables[table_name][column].dropna().astype(str)
    distinct = values.unique()
    simplified = pd.Series(distinct).map(simplify).nunique()
    has_upper = sum(v != v.lower() for v in distinct)
    extra_spaces = sum(v != v.strip() or "  " in v for v in distinct)
    has_accents = sum(simplify(v) != v.strip().lower() for v in distinct)
    has_digits = sum(any(ch.isdigit() for ch in v) for v in distinct)
    print(f"{table_name + '.' + column:<30}{len(distinct):>10}{simplified:>16}{has_upper:>15}{extra_spaces:>14}{has_accents:>13}{has_digits:>12}")

for table_name, column in [("customers", "customer_city"), ("sellers", "seller_city"), ("geolocation", "geolocation_city")]:
    values = tables[table_name][column].dropna().astype(str)
    sao_paulo_forms = values[values.map(simplify).str.contains("sao paulo") & ~values.map(simplify).str.contains("sao paulo[a-z ]", regex=True)]
    print(f"Forms of 'sao paulo' in {table_name}.{column}:", sao_paulo_forms.value_counts().to_dict())

odd_seller_cities = tables["sellers"]["seller_city"][tables["sellers"]["seller_city"].str.contains(r"[\d/@\\,]", regex=True)]
print("Seller cities containing digits or symbols:", odd_seller_cities.unique().tolist())

# ---------------------------------------------------------------
# Section 8: Build the data dictionary (data_dictionary.xlsx)
# Facts (types, counts, missing %) are calculated here.
# Descriptions are written by hand in docs/column_descriptions.csv,
# so re-running this script never overwrites them.
# ---------------------------------------------------------------
row_meaning = {
    "orders": "One order",
    "customers": "One order's customer record (new customer_id per order)",
    "order_items": "One item within an order",
    "order_payments": "One payment within an order",
    "order_reviews": "One review attached to one order",
    "products": "One product",
    "sellers": "One seller",
    "geolocation": "One map point within a zip code area",
    "category_translation": "One product category",
}
true_keys = dict(predicted_keys)
true_keys["order_reviews"] = ["review_id", "order_id"]
true_keys["geolocation"] = []

table_rows = []
column_rows = []
for name, table in tables.items():
    table_rows.append({
        "table": name,
        "one_row_means": row_meaning[name],
        "primary_key": " + ".join(true_keys[name]) if true_keys[name] else "(none)",
        "rows": len(table),
        "columns": table.shape[1],
        "exact_duplicate_rows": table.duplicated().sum(),
    })
    for column in table.columns:
        values = table[column]
        non_blank = values.dropna()
        column_rows.append({
            "table": name,
            "column": column,
            "data_type": str(values.dtype),
            "missing_count": values.isna().sum(),
            "missing_pct": round(values.isna().mean() * 100, 2),
            "distinct_values": values.nunique(),
            "example_value": non_blank.iloc[0] if len(non_blank) > 0 else None,
        })

descriptions = pd.read_csv("docs/column_descriptions.csv")
columns_sheet = pd.DataFrame(column_rows).merge(descriptions, on=["table", "column"], how="left")

print()
print("DATA DICTIONARY")
print("Columns profiled:", len(columns_sheet))
print("Columns with a description:", columns_sheet["description"].notna().sum())
print("Columns still needing a description:", columns_sheet["description"].isna().sum())

with pd.ExcelWriter("data_dictionary.xlsx") as writer:
    pd.DataFrame(table_rows).to_excel(writer, sheet_name="Tables", index=False)
    columns_sheet.to_excel(writer, sheet_name="Columns", index=False)
    pd.DataFrame(relationship_rows).to_excel(writer, sheet_name="Relationships", index=False)
print("Saved data_dictionary.xlsx")
