"""
02_clean_data.py
Applies the approved value fixes from docs/cleaning_log.md to each table.
Reads data/raw/ (never changes it). Writes one clean CSV per table to data/interim/.
No rows are removed. Exclusions are handled later with flags (03_build_tables.py).
"""
import os
import pandas as pd

RAW = "data/raw/"
INTERIM = "data/interim/"

# ---------------------------------------------------------------
# Section 1: Load the tables
# #28: zip code prefixes are read as text so leading zeros are kept
# (geolocation is not used in this project - cleaning log #29-31)
# ---------------------------------------------------------------
orders = pd.read_csv(RAW + "olist_orders_dataset.csv")
customers = pd.read_csv(RAW + "olist_customers_dataset.csv", dtype={"customer_zip_code_prefix": str})
order_items = pd.read_csv(RAW + "olist_order_items_dataset.csv")
order_payments = pd.read_csv(RAW + "olist_order_payments_dataset.csv")
order_reviews = pd.read_csv(RAW + "olist_order_reviews_dataset.csv")
products = pd.read_csv(RAW + "olist_products_dataset.csv")
sellers = pd.read_csv(RAW + "olist_sellers_dataset.csv", dtype={"seller_zip_code_prefix": str})
category_translation = pd.read_csv(RAW + "product_category_name_translation.csv")

raw_row_counts = {
    "orders": len(orders),
    "customers": len(customers),
    "order_items": len(order_items),
    "order_payments": len(order_payments),
    "order_reviews": len(order_reviews),
    "products": len(products),
    "sellers": len(sellers),
    "category_translation": len(category_translation),
}

# ---------------------------------------------------------------
# Section 2: Standardize column names
# #26: fix the misspelled "lenght" columns
# ---------------------------------------------------------------
products = products.rename(columns={
    "product_name_lenght": "product_name_length",
    "product_description_lenght": "product_description_length",
})

# ---------------------------------------------------------------
# Section 3: Convert text dates to real dates
# #4: dates are stored as text in the raw files
# errors="raise" (the default) stops the script if any value is not a valid date
# ---------------------------------------------------------------
order_date_columns = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]
for column in order_date_columns:
    orders[column] = pd.to_datetime(orders[column])

order_items["shipping_limit_date"] = pd.to_datetime(order_items["shipping_limit_date"])
order_reviews["review_creation_date"] = pd.to_datetime(order_reviews["review_creation_date"])
order_reviews["review_answer_timestamp"] = pd.to_datetime(order_reviews["review_answer_timestamp"])

# ---------------------------------------------------------------
# Section 4: Fix values in individual tables
# ---------------------------------------------------------------
# #18: invalid payment type "not_defined" -> "unknown"
not_defined_before = (order_payments["payment_type"] == "not_defined").sum()
order_payments["payment_type"] = order_payments["payment_type"].replace("not_defined", "unknown")

# #20: 0 installments is impossible -> blank (unknown)
# "Int64" (capital I) is a whole-number type that allows blanks
zero_installments_before = (order_payments["payment_installments"] == 0).sum()
order_payments["payment_installments"] = order_payments["payment_installments"].astype("Int64")
order_payments.loc[order_payments["payment_installments"] == 0, "payment_installments"] = pd.NA

# #22: products with no category -> "unknown"
blank_category_before = products["product_category_name"].isna().sum()
products["product_category_name"] = products["product_category_name"].fillna("unknown")

# #24: product weight of 0 g is impossible -> blank (unknown)
zero_weight_before = (products["product_weight_g"] == 0).sum()
products.loc[products["product_weight_g"] == 0, "product_weight_g"] = pd.NA

# #23: add English names for the 2 untranslated categories
missing_translations = pd.DataFrame({
    "product_category_name": ["pc_gamer", "portateis_cozinha_e_preparadores_de_alimentos"],
    "product_category_name_english": ["pc_gamer", "portable_kitchen_and_food_preparers"],
})
category_translation = pd.concat([category_translation, missing_translations], ignore_index=True)

# ---------------------------------------------------------------
# Section 5: Check every fix worked (before -> after)
# ---------------------------------------------------------------
print("FIXES (before -> after)")
print(f"#18 payment_type 'not_defined':      {not_defined_before} -> {(order_payments['payment_type'] == 'not_defined').sum()}"
      f"   ('unknown' now: {(order_payments['payment_type'] == 'unknown').sum()})")
print(f"#20 payments with 0 installments:    {zero_installments_before} -> {(order_payments['payment_installments'] == 0).sum()}"
      f"   (blank now: {order_payments['payment_installments'].isna().sum()})")
print(f"#22 products with blank category:    {blank_category_before} -> {products['product_category_name'].isna().sum()}"
      f"   ('unknown' now: {(products['product_category_name'] == 'unknown').sum()})")
print(f"#24 products weighing 0 g:           {zero_weight_before} -> {(products['product_weight_g'] == 0).sum()}"
      f"   (blank now: {products['product_weight_g'].isna().sum()})")
translated = products["product_category_name"].isin(category_translation["product_category_name"])
print(f"#23 products with untranslated category (excluding 'unknown'): "
      f"{(~translated & (products['product_category_name'] != 'unknown')).sum()}")
print(f"#26 columns now: {[c for c in products.columns if 'length' in c or 'lenght' in c]}")
print(f"#28 example customer zip codes: {customers['customer_zip_code_prefix'].head(3).tolist()}"
      f"   shortest: {customers['customer_zip_code_prefix'].str.len().min()} characters")
print(f"#4  order date column types: {sorted(set(str(orders[c].dtype) for c in order_date_columns))}")

# ---------------------------------------------------------------
# Section 6: Confirm no rows were removed, then export
# ---------------------------------------------------------------
clean_tables = {
    "orders": orders,
    "customers": customers,
    "order_items": order_items,
    "order_payments": order_payments,
    "order_reviews": order_reviews,
    "products": products,
    "sellers": sellers,
    "category_translation": category_translation,
}

print()
print("ROW COUNTS (raw -> clean)")
os.makedirs(INTERIM, exist_ok=True)
for name, table in clean_tables.items():
    expected = raw_row_counts[name]
    if name == "category_translation":
        expected += len(missing_translations)
    status = "OK" if len(table) == expected else "MISMATCH"
    print(f"{name:<22}{raw_row_counts[name]:>9} -> {len(table):>9}   {status}")
    table.to_csv(INTERIM + name + ".csv", index=False)

print()
print("Saved", len(clean_tables), "clean tables to", INTERIM)
