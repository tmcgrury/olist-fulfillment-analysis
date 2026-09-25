import os
import pandas as pd
import matplotlib.pyplot as plt

by_month = pd.read_csv("data/processed/late_rate_by_month.csv")

chart_data = by_month[by_month["purchase_month"] >= "2017-01"]
print("Months shown:", len(chart_data), "of", len(by_month))
print("Orders left out of chart:", by_month["orders"].sum() - chart_data["orders"].sum())

fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(
    chart_data["purchase_month"],
    chart_data["late_rate"],
    color="#2a78d6",
    linewidth=2,
    marker="o",
    markersize=8,
)

for month, note in [("2017-11", "Black Friday\n12.4%"), ("2018-03", "19.0%")]:
    y = chart_data.loc[chart_data["purchase_month"] == month, "late_rate"].iloc[0]
    ax.annotate(note, (month, y), textcoords="offset points", xytext=(0, 12),
                ha="center", color="#0b0b0b")

ax.set_ylim(0, 25)
ax.set_ylabel("Late orders (%)", color="#52514e")
ax.set_xlabel("Month order was placed", color="#52514e")
ax.set_title("Late deliveries spiked in Nov 2017 and again in Feb-Mar 2018",
             loc="left", fontsize=13, color="#0b0b0b")
ax.grid(axis="y", color="#e5e4e0", linewidth=1)
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(colors="#52514e")
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

fig.text(0.01, 0.01, "Source: Olist delivered orders (n = 96,203 shown). 2016 months left out "
         "(267 orders; too few for reliable rates). Recent months may understate lateness: "
         "orders still in transit are excluded.", fontsize=8, color="#52514e", wrap=True)

os.makedirs("outputs", exist_ok=True)
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig("outputs/late_rate_over_time.png", dpi=150)
print("Saved to outputs/late_rate_over_time.png")
