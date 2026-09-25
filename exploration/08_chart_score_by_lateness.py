import os
import pandas as pd
import matplotlib.pyplot as plt

summary = pd.read_csv("data/processed/score_by_lateness.csv")

fig, ax = plt.subplots(figsize=(9, 5))

ax.plot(
    summary["lateness_group"],
    summary["avg_score"],
    color="#2a78d6",
    linewidth=2,
    marker="o",
    markersize=8,
)

for x, y in zip(summary["lateness_group"], summary["avg_score"]):
    ax.annotate(f"{y:.2f}", (x, y), textcoords="offset points", xytext=(0, 10),
                ha="center", color="#0b0b0b")

ax.set_ylim(1, 5)
ax.set_ylabel("Average review score (1-5 stars)", color="#52514e")
ax.set_xlabel("Delivery vs. promised date", color="#52514e")
ax.set_title("Review scores fall sharply once an order is even a few days late",
             loc="left", fontsize=13, color="#0b0b0b")
ax.grid(axis="y", color="#e5e4e0", linewidth=1)
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(colors="#52514e")

fig.text(0.01, 0.01, "Source: Olist delivered orders with reviews (n = 95,824). "
         "Late = delivered on a later calendar day than promised.",
         fontsize=8, color="#52514e")

os.makedirs("outputs", exist_ok=True)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig("outputs/score_by_lateness.png", dpi=150)
print("Saved to outputs/score_by_lateness.png")
