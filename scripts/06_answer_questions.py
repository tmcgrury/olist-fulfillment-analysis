"""
06_answer_questions.py
Answers the 9 analytical questions in docs/business_questions.md using the final tables
in data/processed/. Reads only. Saves one result table per question to outputs/.
"""
import os
import pandas as pd

PROCESSED = "data/processed/"
OUTPUTS = "outputs/"
os.makedirs(OUTPUTS, exist_ok=True)

fact_orders = pd.read_csv(PROCESSED + "fact_orders.csv", parse_dates=["purchase_date", "carrier_handoff_date"])
fact_order_items = pd.read_csv(PROCESSED + "fact_order_items.csv")
dim_customer = pd.read_csv(PROCESSED + "dim_customer.csv", dtype={"customer_zip_code_prefix": str})
delivered = fact_orders[fact_orders["is_delivered"]]

# ---------------------------------------------------------------
# Q1: How many orders arrive late, and how long do deliveries take?
# ---------------------------------------------------------------
print("=" * 70)
print("Q1: How many orders arrive late, and how long do deliveries take?")
q1 = pd.DataFrame([{
    "delivered_orders": len(delivered),
    "late_orders": int(delivered["is_late"].sum()),
    "late_rate_%": round(delivered["is_late"].mean() * 100, 2),
    "median_delivery_days": round(delivered["total_delivery_time"].median(), 2),
    "average_delivery_days": round(delivered["total_delivery_time"].mean(), 2),
    "median_transit_days": round(delivered["transit_time"].median(), 2),
    "median_days_vs_promise": float(delivered["delivery_variance"].median()),
}])
print(q1.T.to_string(header=False))
q1.to_csv(OUTPUTS + "q1_baseline.csv", index=False)

# ---------------------------------------------------------------
# Q2: Do late deliveries lower review scores, and by how much?
# ---------------------------------------------------------------
print()
print("=" * 70)
print("Q2: Do late deliveries lower review scores?")
reviewed = delivered[delivered["review_score"].notna()].copy()
reviewed["one_star"] = reviewed["review_score"] == 1
q2 = reviewed.groupby("is_late").agg(
    orders=("order_id", "count"),
    avg_score=("review_score", "mean"),
    one_star_rate=("one_star", "mean"),
)
q2.index = ["On time", "Late"]
q2["one_star_%"] = (q2["one_star_rate"] * 100).round(1)
print(q2[["orders", "avg_score", "one_star_%"]].round(2).to_string())
reviewed["lateness_group"] = pd.cut(reviewed["delivery_variance"], bins=[-10000, -1, 0, 3, 7, 14, 10000],
                                    labels=["Early", "On the day", "1-3 days late", "4-7 days late", "8-14 days late", "15+ days late"])
q2_groups = reviewed.groupby("lateness_group", observed=True).agg(
    orders=("order_id", "count"), avg_score=("review_score", "mean"), one_star_rate=("one_star", "mean"))
q2_groups["one_star_%"] = (q2_groups["one_star_rate"] * 100).round(1)
print()
print(q2_groups[["orders", "avg_score", "one_star_%"]].round(2).to_string())
q2.to_csv(OUTPUTS + "q2_reviews_late_vs_on_time.csv")
q2_groups.to_csv(OUTPUTS + "q2_reviews_by_lateness_group.csv")

# ---------------------------------------------------------------
# Q3: How has the late rate changed over time? (by purchase month)
# ---------------------------------------------------------------
print()
print("=" * 70)
print("Q3: How has the late rate changed over time?")
by_month = delivered.assign(month=delivered["purchase_date"].dt.strftime("%Y-%m")).groupby("month").agg(
    orders=("order_id", "count"), late_rate=("is_late", "mean"))
by_month["late_rate_%"] = (by_month["late_rate"] * 100).round(1)
print(by_month.loc["2017-10":"2018-04", ["orders", "late_rate_%"]].to_string())
spike = delivered["purchase_date"].dt.strftime("%Y-%m").isin(["2018-02", "2018-03"])
print(f"Feb-Mar 2018: {int(delivered.loc[spike, 'is_late'].sum())} of {int(delivered['is_late'].sum())} late orders "
      f"({delivered.loc[spike, 'is_late'].sum() / delivered['is_late'].sum() * 100:.1f}%)")
by_month.to_csv(OUTPUTS + "q3_late_rate_by_month.csv")

# ---------------------------------------------------------------
# Q4: Which states have the highest late rates and the most late orders?
# ---------------------------------------------------------------
print()
print("=" * 70)
print("Q4: Which states have the highest late rates and the most late orders?")
q4_data = delivered.merge(dim_customer[["customer_id", "customer_state"]], on="customer_id", how="left")
assert len(q4_data) == len(delivered), "Join changed the number of orders!"
by_state = q4_data.groupby("customer_state").agg(
    orders=("order_id", "count"), late_orders=("is_late", "sum"), late_rate=("is_late", "mean"),
    median_delivery_days=("total_delivery_time", "median"))
by_state["late_rate_%"] = (by_state["late_rate"] * 100).round(1)
columns_q4 = ["orders", "late_orders", "late_rate_%", "median_delivery_days"]
print("Most late orders:")
print(by_state.sort_values("late_orders", ascending=False).head(4)[columns_q4].round(1).to_string())
print("Highest late rates:")
print(by_state.sort_values("late_rate", ascending=False).head(4)[columns_q4].round(1).to_string())
by_state.to_csv(OUTPUTS + "q4_late_rate_by_state.csv")

# ---------------------------------------------------------------
# Q5: Is lateness caused more by sellers or by carriers? (spike vs other months)
# Single-seller delivered orders with a carrier date
# ---------------------------------------------------------------
print()
print("=" * 70)
print("Q5: Sellers or carriers?")
q5 = delivered[(delivered["seller_count"] == 1) & delivered["carrier_handoff_date"].notna()].copy()
q5["period"] = q5["purchase_date"].dt.strftime("%Y-%m").isin(["2018-02", "2018-03"]).map({True: "Feb-Mar 2018", False: "Other months"})
q5_rows = []
for period, group in q5.groupby("period"):
    q5_rows.append({
        "period": period,
        "orders": len(group),
        "seller_late_%": round(group["seller_late"].mean() * 100, 1),
        "customer_late_%": round(group["is_late"].mean() * 100, 1),
        "late_when_seller_on_time_%": round(group.loc[~group["seller_late"], "is_late"].mean() * 100, 1),
    })
q5_table = pd.DataFrame(q5_rows).set_index("period")
print(q5_table.to_string())
q5_table.to_csv(OUTPUTS + "q5_seller_vs_carrier.csv")

print()
# ---------------------------------------------------------------
# Q6: Do some sellers have consistently high late-handoff rates?
# Uses the seller late-handoff KPI filter: single-seller orders with a carrier date
# ---------------------------------------------------------------
print("=" * 70)
print("Q6: Are late handoffs concentrated in a few sellers?")

seller_of_order = fact_order_items.groupby("order_id")["seller_id"].first()  # one row per order
handoffs = fact_orders[(fact_orders["seller_count"] == 1) & fact_orders["carrier_handoff_date"].notna()].copy()
handoffs["seller_id"] = handoffs["order_id"].map(seller_of_order)
handoffs["in_spike"] = handoffs["purchase_date"].dt.strftime("%Y-%m").isin(["2018-02", "2018-03"])
print("Orders in the seller KPI:", len(handoffs), "| late handoffs:", int(handoffs["seller_late"].sum()),
      f"| overall rate: {handoffs['seller_late'].mean() * 100:.1f}%")

sellers = handoffs.groupby("seller_id").agg(
    orders=("order_id", "count"),
    late_handoffs=("seller_late", "sum"),
    late_rate=("seller_late", "mean"),
)
outside_spike = handoffs[~handoffs["in_spike"]].groupby("seller_id")["seller_late"].mean()
sellers["late_rate_outside_spike"] = outside_spike
print("Sellers in the KPI:", len(sellers))


def concentration(min_orders):
    """Share of late handoffs caused by the 10% of sellers with the most late handoffs."""
    big = sellers[sellers["orders"] >= min_orders].sort_values("late_handoffs", ascending=False)
    top_n = max(1, round(len(big) * 0.10))
    top = big.head(top_n)
    return {
        "min_orders": min_orders,
        "sellers": len(big),
        "top_10pct_sellers": top_n,
        "share_of_orders_%": round(top["orders"].sum() / big["orders"].sum() * 100, 1),
        "share_of_late_handoffs_%": round(top["late_handoffs"].sum() / big["late_handoffs"].sum() * 100, 1),
        "median_seller_late_rate_%": round(big["late_rate"].median() * 100, 1),
        "sellers_over_20pct_late": int((big["late_rate"] > 0.20).sum()),
    }


summary = pd.DataFrame([concentration(n) for n in (20, 50, 100)])
print()
print("Concentration (top 10% of sellers by late handoffs):")
print(summary.to_string(index=False))

main = sellers[sellers["orders"] >= 50].sort_values("late_handoffs", ascending=False)
print()
print("Top 10 sellers by late handoffs (50+ orders):")
top10 = main.head(10).copy()
top10["seller_id"] = top10.index.str[:8] + "..."
top10["late_rate_%"] = (top10["late_rate"] * 100).round(1)
top10["outside_spike_%"] = (top10["late_rate_outside_spike"] * 100).round(1)
print(top10[["seller_id", "orders", "late_handoffs", "late_rate_%", "outside_spike_%"]].to_string(index=False))

main.to_csv(OUTPUTS + "q6_sellers_late_handoff.csv")
summary.to_csv(OUTPUTS + "q6_concentration_summary.csv", index=False)
print()
print("Saved outputs/q6_sellers_late_handoff.csv and outputs/q6_concentration_summary.csv")

# ---------------------------------------------------------------
# Q7: Do certain product categories (e.g. heavy or bulky items) arrive late more often?
# Late rate uses delivered orders. Category analysis uses orders whose items
# all share one category; weight analysis uses orders where every item has a weight.
# ---------------------------------------------------------------
print()
print("=" * 70)
print("Q7: Which product categories and weights arrive late most often?")

# main_category and order_weight_kg are built once, in 03_build_tables.py
orders_q7 = delivered[delivered["order_item_count"] > 0].copy()
orders_q7["category"] = orders_q7["main_category"]
single = orders_q7[orders_q7["category"].notna()]
print(f"Delivered orders with items: {len(orders_q7)} | single-category: {len(single)} "
      f"({len(single) / len(orders_q7) * 100:.1f}%) | left out (mixed categories): {len(orders_q7) - len(single)}")

by_category = single.groupby("category").agg(
    orders=("order_id", "count"),
    late_orders=("is_late", "sum"),
    late_rate=("is_late", "mean"),
    median_weight_kg=("order_weight_kg", "median"),
)
by_category["late_rate_%"] = (by_category["late_rate"] * 100).round(1)
big_categories = by_category[by_category["orders"] >= 500].sort_values("late_rate", ascending=False)
overall_rate = single["is_late"].mean() * 100
print(f"Categories with 500+ orders: {len(big_categories)} | overall late rate in this group: {overall_rate:.1f}%")
print()
print("Highest late rates:")
print(big_categories.head(8)[["orders", "late_orders", "late_rate_%", "median_weight_kg"]].round(2).to_string())
print()
print("Lowest late rates:")
print(big_categories.tail(5)[["orders", "late_orders", "late_rate_%", "median_weight_kg"]].round(2).to_string())
print()
furniture = by_category[by_category.index.str.contains("furniture")]
print("All furniture categories (any size):")
print(furniture[["orders", "late_orders", "late_rate_%", "median_weight_kg"]].round(2).to_string())

# Weight directly: late rate by order weight band
weighted = orders_q7[orders_q7["order_weight_kg"].notna()].copy()
weighted["weight_band"] = pd.cut(weighted["order_weight_kg"], bins=[0, 0.5, 1, 2, 5, 10, 20, 1000],
                                 labels=["<0.5 kg", "0.5-1 kg", "1-2 kg", "2-5 kg", "5-10 kg", "10-20 kg", "20+ kg"])
by_weight = weighted.groupby("weight_band", observed=True).agg(
    orders=("order_id", "count"),
    late_rate=("is_late", "mean"),
    median_delivery_days=("total_delivery_time", "median"),
)
by_weight["late_rate_%"] = (by_weight["late_rate"] * 100).round(1)
print()
print(f"Late rate by order weight ({len(weighted)} delivered orders with known weights):")
print(by_weight[["orders", "late_rate_%", "median_delivery_days"]].round(1).to_string())

big_categories.to_csv(OUTPUTS + "q7_late_rate_by_category.csv")
by_weight.to_csv(OUTPUTS + "q7_late_rate_by_weight.csv")
print()
print("Saved outputs/q7_late_rate_by_category.csv and outputs/q7_late_rate_by_weight.csv")

# ---------------------------------------------------------------
# Q8: Does freight cost or order value relate to lateness?
# Delivered orders split into 5 equal-sized groups (quintiles) for each measure.
# ---------------------------------------------------------------
print()
print("=" * 70)
print("Q8: Do freight cost and order value relate to lateness?")

q8 = delivered.merge(dim_customer[["customer_id", "customer_state"]], on="customer_id", how="left")
assert len(q8) == len(delivered), "Join changed the number of orders!"
q8 = q8[q8["order_value"].notna()].copy()

q8_tables = {}
for measure in ["freight_cost", "order_value", "freight_pct"]:
    q8["group"] = pd.qcut(q8[measure], q=5, labels=["1 lowest", "2", "3", "4", "5 highest"])
    table = q8.groupby("group", observed=True).agg(
        orders=("order_id", "count"),
        from_value=(measure, "min"),
        to_value=(measure, "max"),
        late_rate=("is_late", "mean"),
    )
    table["late_rate_%"] = (table["late_rate"] * 100).round(1)
    q8_tables[measure] = table
    print()
    print(f"Late rate by {measure} quintile:")
    print(table[["orders", "from_value", "to_value", "late_rate_%"]].round(2).to_string())

# Does the freight pattern survive within one state? (freight also reflects distance)
sp = q8[q8["customer_state"] == "SP"].copy()
sp["group"] = pd.qcut(sp["freight_cost"], q=5, labels=["1 lowest", "2", "3", "4", "5 highest"])
sp_table = sp.groupby("group", observed=True).agg(orders=("order_id", "count"), late_rate=("is_late", "mean"))
sp_table["late_rate_%"] = (sp_table["late_rate"] * 100).round(1)
print()
print("Late rate by freight_cost quintile - Sao Paulo customers only (same region, so distance is similar):")
print(sp_table[["orders", "late_rate_%"]].to_string())

far = q8.groupby("customer_state")["freight_cost"].median().sort_values(ascending=False)
print()
print("Median freight cost by customer state - highest 3 and lowest 3:")
print(pd.concat([far.head(3), far.tail(3)]).round(2).to_string())

for measure, table in q8_tables.items():
    table.to_csv(OUTPUTS + f"q8_late_rate_by_{measure}.csv")
sp_table.to_csv(OUTPUTS + "q8_late_rate_by_freight_sp_only.csv")
print()
print("Saved outputs/q8_*.csv")

# ---------------------------------------------------------------
# Q9: How accurate are delivery estimates, and are some regions over-padded?
# Promised days = estimated date - purchase date. Padding = days early (-delivery_variance).
# ---------------------------------------------------------------
print()
print("=" * 70)
print("Q9: How accurate are delivery estimates? Which states are over-padded?")

q9 = delivered.merge(dim_customer[["customer_id", "customer_state"]], on="customer_id", how="left")
assert len(q9) == len(delivered), "Join changed the number of orders!"
q9["estimated_date"] = pd.to_datetime(q9["estimated_date"])
q9["promised_days"] = (q9["estimated_date"] - q9["purchase_date"].dt.normalize()).dt.days
q9["days_early"] = -q9["delivery_variance"]
q9["within_3_days"] = q9["delivery_variance"].abs() <= 3

print(f"All delivered orders: promised {q9['promised_days'].median():.0f} days, "
      f"actual {q9['total_delivery_time'].median():.1f} days, "
      f"arrived {q9['days_early'].median():.0f} days early (median). "
      f"Within 3 days of the promise: {q9['within_3_days'].mean() * 100:.1f}%")

by_state_q9 = q9.groupby("customer_state").agg(
    orders=("order_id", "count"),
    promised_days=("promised_days", "median"),
    actual_days=("total_delivery_time", "median"),
    days_early=("days_early", "median"),
    late_rate=("is_late", "mean"),
)
by_state_q9["late_rate_%"] = (by_state_q9["late_rate"] * 100).round(1)
by_state_q9 = by_state_q9.sort_values("days_early", ascending=False)
columns_q9 = ["orders", "promised_days", "actual_days", "days_early", "late_rate_%"]
print()
print("Most padded states (arrive the most days early):")
print(by_state_q9.head(6)[columns_q9].round(1).to_string())
print()
print("Least padded states:")
print(by_state_q9.tail(6)[columns_q9].round(1).to_string())
print()
correlation = by_state_q9["days_early"].corr(by_state_q9["late_rate"])
print(f"Correlation across states between padding and late rate: {correlation:.2f}")

by_state_q9.to_csv(OUTPUTS + "q9_estimate_padding_by_state.csv")
print()
print("Saved outputs/q9_estimate_padding_by_state.csv")
