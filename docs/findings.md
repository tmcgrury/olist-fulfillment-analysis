# Findings

> Approved by the project owner on 2026-09-22.
> Every number comes from `scripts/06_answer_questions.py` (result tables in `outputs/`).

**Audience:** Olist operations manager.
**Question:** Which states and what factors are affecting late deliveries, so improvement can be targeted?

## 1. What happened?

6.8% of our orders (6,534 of 96,470) were late, and late orders got much lower reviews:
**54% of late orders got a 1-star review, compared with 7% of on-time orders.** Lateness was
usually low (3-5% a month), but it spiked in November 2017 (12%) and again in February-March
2018 (up to 19%). Those two months alone account for a third of all late orders.

## 2. Where did it happen?

Rio de Janeiro (RJ) has the most late orders relative to its size: 1,495, second only to São
Paulo, which has three times as many orders. RJ was late more often than most states even in
normal months (8.5%), and in February-March 2018 its late rate jumped to 34.3%, which matches
the nationwide carrier disruption in that period. The northeastern states have the highest late
rates (Alagoas 21.4%, Maranhão 17.4%, Sergipe 15.2%), but far fewer orders, so fixing RJ would
help the most customers.

## 3. How large was the problem?

6.8% sounds small, but it is costly: late deliveries produced about 3,400 one-star reviews,
because a late order is eight times more likely to get one star than an on-time one. The
problem was also concentrated: a third of all late orders came in just two months
(February-March 2018).

## 4. What appears connected to it?

Carriers and sellers matter the most. In February-March 2018, orders that sellers shipped on
time still arrived late 15.5% of the time (normally 3.8%), which points to a carrier problem.
Separately, 10% of sellers cause 51% of late handoffs, and they do so all year, not just during
the spike. Location and delivery promises matter too: states with tighter promised dates have
more late orders. Product weight and order value have only a small effect, and freight cost
looked connected at first, but it really reflects distance: within a single state, the pattern
disappears.

| Factor | Evidence | Effect |
|---|---|---|
| Carriers (Feb-Mar 2018) | Late despite on-time seller handoff: 3.8% -> 15.5% | Large |
| Sellers | Top 10% of sellers (50+ orders) cause 51% of late handoffs, all year | Large |
| Customer state | Late rate 2.8% (AM) to 21.4% (AL) | Large |
| Promise padding | Correlation between padding and late rate across states: -0.56 | Large |
| Order weight | 6.5% (under 0.5 kg) to 9.4% (20+ kg) | Small |
| Order value | 5.9% (lowest fifth) to 7.5% (highest fifth) | Small |
| Freight cost | 4.4% to 8.1% overall, but flat within São Paulo (3.9-5.1%) | Reflects distance |

## 5. What does the data not prove?

- **Lateness is linked to low reviews, but not proven to cause them.** Bad sellers could cause
  both late packages and low reviews (for example, by also sending poor-quality products). The
  step-by-step drop in scores as orders get later (4.03 on the day, 3.29 at 1-3 days late,
  2.10 at 4-7 days late) makes lateness very likely a factor, but not necessarily the only one.
- **The carrier explanation is an inference.** The data does not name carriers, so we cannot say
  which carrier failed in February-March 2018, or why (for example, strikes, weather or capacity).
- **Revenue impact is unknown.** The data has no information on lost sales or whether customers
  who received late orders stopped buying, so the cost is measured in reviews, not money.
- **Only delivered orders were measured.** Orders still in transit when the data was collected
  are missing, which probably makes the most recent months (mid-2018) look better than they were.
  A small number of records have unreliable dates (28 suspected bulk updates; 23 deliveries
  recorded before carrier pickup); they are flagged and do not change the results.

## 6. What should management investigate or change next?

| # | Recommendation | Type | Based on |
|---|---|---|---|
| 1 | **Review the 42 sellers with the most late handoffs**: find out why they ship late (stock, packing, capacity) and agree handoff targets with them. The list is in `outputs/q6_sellers_late_handoff.csv`. | Investigation, then action | 10% of sellers cause 51% of late handoffs, all year |
| 2 | **Investigate the February-March 2018 carrier disruption with the logistics team**: which carriers and routes failed, especially to Rio de Janeiro, and set up a monthly late-rate alert so the next disruption is caught early. | Investigation, then action | On-time handoffs arrived late 15.5% of the time (normally 3.8%); RJ reached 34.3% |
| 3 | **Recalibrate delivery promises by state**: add a few days to promises for the northeast (Alagoas, Maranhão, Sergipe), where promises are tight and late rates are highest, and test shorter promises where padding is very large (about 20 days in the far north). | Action (test first) | Correlation between padding and late rate: -0.56; AL 21.4% late with 10 days of padding |
| 4 | **Treat even a 1-3 day delay as serious**: when an order is predicted to miss its date, contact the customer proactively. | Action (test first) | 1-star reviews triple from 8.5% (on the day) to 25.1% (1-3 days late) |

Recommendations 3 and 4 should be tested on a small group first, because this data shows
association, not proof of cause (see section 5).
