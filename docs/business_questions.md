# Business Questions

## Business problem

The operations manager at Olist needs to reduce late deliveries because they are resulting
in negative customer review scores. This analysis will help them decide which states and what
factors are affecting late deliveries so they know where to target improvement.

## Analytical questions

| # | Question | Theme | Status |
|---|---|---|---|
| 1 | How many orders arrive late, and how long do deliveries take? | Baseline | Answered (exploration) |
| 2 | Do late deliveries lower review scores, and by how much? | Customer impact | Answered (exploration) |
| 3 | How has the late rate changed over time? | Time | Answered (exploration) |
| 4 | Which states have the highest late rates and the most late orders? | States | Answered (exploration) |
| 5 | Is lateness caused more by sellers (slow handoff) or by carriers (slow transit)? | Factors | Answered for the Feb-Mar 2018 spike (exploration) |
| 6 | Do some sellers have consistently high late-handoff rates? | Factors | Not yet |
| 7 | Do certain product categories (e.g. heavy or bulky items) arrive late more often? | Factors | Not yet |
| 8 | Does freight cost or order value relate to lateness? | Factors | Not yet |
| 9 | How accurate are the delivery estimates, and are some regions over-padded? | Estimates | Partly answered (exploration) |

"Answered (exploration)" means the question was answered with the exploratory scripts in
`exploration/`. Final answers will be re-produced by the pipeline in `scripts/` and recorded
in `findings.md`.

## KPI definitions

**Delivered orders** (the base for every delivery KPI) = orders with status "delivered"
AND a delivered-to-customer date. 96,470 orders.

| KPI | Definition | Notes |
|---|---|---|
| Late delivery rate | Delivered orders whose delivered calendar day is after the estimated delivery day ÷ delivered orders × 100 | Compares calendar days, because estimated dates are all at 00:00. Arriving on the promised day = on time |
| On-time delivery rate | Delivered orders whose delivered calendar day is on or before the estimated delivery day ÷ delivered orders × 100 | Always equals 100% − late delivery rate (use as a check) |
| Days late (delivery variance) | Delivered calendar day − estimated delivery day, in whole days | Negative = early, 0 = on the day, positive = late |
| Total delivery time | Delivered-to-customer date/time − purchase date/time | Customer's full wait |
| Transit time | Delivered-to-customer date/time − carrier handoff date/time | Carrier's part of the journey. Excluded from this KPI only: 1 delivered order with no carrier date, and 23 delivered orders whose carrier date is after the delivery date (impossible - data error) |
| Seller late-handoff rate | Orders handed to the carrier after the seller's shipping_limit_date ÷ orders × 100 | Exact date/times. Single-seller orders only (multi-seller orders can't be attributed) |
| Average review score | Sum of the latest review score per delivered order ÷ delivered orders with a review | One review per order (the most recent). Orders without a review are excluded, not counted as 0 |
| Freight percentage | Total freight_value of the order's items ÷ total price of the order's items × 100 | Summed per order first. Profiling found no items with price 0, so no division by zero |

## Calculated field definitions (fact_orders)

Numbers in brackets refer to rows in [cleaning_log.md](cleaning_log.md).

### Dates
| Field | Definition |
|---|---|
| purchase_date | order_purchase_timestamp as a date/time |
| approval_date | order_approved_at as a date/time |
| carrier_handoff_date | order_delivered_carrier_date as a date/time |
| delivered_date | order_delivered_customer_date as a date/time |
| estimated_date | order_estimated_delivery_date as a date |

### Flags
| Field | Definition |
|---|---|
| is_delivered | status = "delivered" AND delivered_date exists [1-3] |
| is_late | is_delivered AND delivered calendar day > estimated day [5] |
| suspicious_date | delivered on 2017-09-19 AND total_delivery_time > 60 days [6] |
| valid_transit_time | is_delivered AND carrier_handoff_date exists AND carrier_handoff_date <= delivered_date [8, 9] |
| seller_late | seller_count = 1 AND carrier_handoff_date > shipping deadline [15] |

### Durations (days, with decimals)
| Field | Definition | Blank when |
|---|---|---|
| approval_time | approval_date − purchase_date | no approval date [11] |
| fulfillment_time | carrier_handoff_date − approval_date. Can be negative (ship before approval is a real process [10]) | either date missing |
| transit_time | delivered_date − carrier_handoff_date | valid_transit_time is False |
| total_delivery_time | delivered_date − purchase_date | is_delivered is False |
| delivery_variance | delivered calendar day − estimated day, whole days (negative = early) | is_delivered is False |

### Money and counts (summed from order items)
| Field | Definition |
|---|---|
| seller_id | The order's seller, only when all its items come from one seller [15]. Blank for multi-seller orders and orders with no items |
| order_item_count | Number of items in the order (0 if the order has no items) |
| seller_count | Number of distinct sellers in the order (0 if no items) |
| order_value | Sum of item prices (products only, excludes freight) |
| freight_cost | Sum of item freight_value |
| freight_pct | freight_cost ÷ order_value × 100 |
| main_category | English product category, only when all the order's items share one category. Blank for mixed-category orders |
| order_weight_kg | Sum of the order's item weights in kg. Blank if any item's weight is unknown [24, 25] |

### Reviews
| Field | Definition |
|---|---|
| review_score | Score of the most recent review for the order [12]. Blank if no review [14] |
| review_group | Negative (1-2), Neutral (3), Positive (4-5). Blank if no review |

### How KPIs use the flags
| KPI | Filter |
|---|---|
| Late / on-time delivery rate, total delivery time, delivery variance | is_delivered = True |
| Transit time | valid_transit_time = True |
| Seller late-handoff rate | seller_count = 1 AND carrier_handoff_date exists |
| Average review score | review_score is not blank |
