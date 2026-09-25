# Cleaning Log

Every data problem found during profiling, the evidence for it, how it is treated, and what that
means for the analysis. **Raw files in `data/raw/` are never changed.** Treatments are applied by
the pipeline scripts to produce new files.

Evidence comes from `scripts/01_profile_data.py` and the exploratory scripts in `exploration/`.

Status: **Yes** = approved by the project owner. **Pending** = proposed, awaiting a decision.

## Orders and delivery

| # | Problem | Evidence | Proposed treatment | Business effect | Approved? |
|---|---|---|---|---|---|
| 1 | Orders not delivered (canceled, shipped, unavailable, etc.) | 2,963 of 99,441 orders not "delivered" | Delivery KPIs use only orders with status "delivered" AND a delivery date | Delivery KPIs describe completed deliveries only (96,470 orders) | Yes |
| 2 | Status "delivered" but no delivery date | 8 orders | Excluded from delivery KPIs (part of #1) | Can't measure delivery time or lateness | Yes |
| 3 | Delivery date but status not "delivered" | 6 orders | Excluded from delivery KPIs (part of #1) | Status and dates contradict each other | Yes |
| 4 | Dates stored as text | All 5 order date columns load as text | Convert to dates when loading | Enables date calculations | Yes |
| 5 | Estimated delivery dates have no time (always 00:00) | 100% of estimated dates | Compare by calendar day when deciding lateness | Same-day deliveries count as on time (late rate 6.77% instead of 8.11%) | Yes |
| 6 | Suspected bulk update of delivery dates | 28 orders delivered on 2017-09-19 after >60 days; 8 of the 10 slowest orders recorded that afternoon | Keep all orders; flag with `suspicious_date` | Results can be shown with and without them (median delivery time barely changes) | Yes |
| 7 | Very slow deliveries | 306 orders took >60 days; longest 209 days | Keep (only the 28 in #6 are flagged) | Real delays are part of delivery performance | Yes |
| 8 | Carrier handoff date missing on a delivered order | 1 order | Excluded from transit time only | Transit time based on 96,446 orders | Yes |
| 9 | Delivered before carrier pickup (impossible) | 23 orders; gaps 30 min to 16 days; all 2016-2017 | Excluded from transit time only | Prevents negative transit times | Yes |
| 10 | Handed to carrier before approval | 1,359 orders; median gap 17 h, middle half 1.4-26 h, max 171 days | Keep. Treat as a real process. Revisit when building approval time | Affects approval time and fulfillment time only | Yes |
| 11 | Approval date missing | 160 orders (14 of them delivered) | Keep. Exclude from approval-time KPI only | Approval time based on orders that have an approval date | Yes |

## Reviews

| # | Problem | Evidence | Proposed treatment | Business effect | Approved? |
|---|---|---|---|---|---|
| 12 | Orders with more than one review | 547 orders have 2-3 reviews; 202 of them disagree on score | Keep the most recent review per order (latest creation date, then latest answer time) | One score per order; reflects the customer's final opinion | Yes |
| 13 | One review attached to several orders | 789 review_ids appear on 1,603 rows; identical except order_id | Keep. Treat review_id + order_id as the key. Count reviews with distinct review_id | Per-order scores are correct; review counts not inflated | Yes |
| 14 | Delivered orders with no review | 646 orders | Excluded from review KPIs (not counted as 0) | Average review score based on 95,824 orders | Yes |

## Sellers and order items

| # | Problem | Evidence | Proposed treatment | Business effect | Approved? |
|---|---|---|---|---|---|
| 15 | Orders with items from more than one seller | 1,278 orders (1,275 delivered) | Excluded from seller analysis only | Delays can be attributed to one seller | Yes |
| 16 | Items with freight = 0 | 383 items | Keep. Classified as real (free shipping) | Free shipping included in freight KPIs | Yes |
| 17 | Seller city names typed inconsistently | 'são paulo' vs 'sao paulo'; city/state combos; a zip code and an email address as cities | Keep raw values. Use seller_state (clean) for analysis, not city | No city-level seller analysis | Yes |

## Payments

| # | Problem | Evidence | Proposed treatment | Business effect | Approved? |
|---|---|---|---|---|---|
| 18 | Payment type "not_defined" (invalid category) | 3 payments, all with value 0 | Keep rows. Label as "unknown" | No effect on totals (value 0) | Yes |
| 19 | Voucher payments of 0 | 6 payments | Keep. Classified as real (fully discounted) | None | Yes |
| 20 | Credit card payments with 0 installments (impossible) | 2 payments | Keep payment value. Set installments to blank (unknown) | No effect on payment totals | Yes |
| 21 | Very large payment | 1 payment of 13,664 (99th percentile is 1,040) | Keep. Verify against the order's item totals in Phase 8 | Confirms whether it is real | Yes |

## Products

| # | Problem | Evidence | Proposed treatment | Business effect | Approved? |
|---|---|---|---|---|---|
| 22 | Products with no category or product info | 610 products: blank category AND blank photo count | Keep. Label category as "unknown" | Their items still count in delivery KPIs; shown as "unknown" in category analysis | Yes |
| 23 | Categories missing from the translation table | 2 categories, 13 products (pc_gamer, portateis_cozinha_e_preparadores_de_alimentos) | Add English names ("pc_gamer", "portable_kitchen_and_food_preparers") | All categories have an English name | Yes |
| 24 | Product weight = 0 (impossible) | 4 products | Set weight to blank (unknown) | Excluded from weight analysis only | Yes |
| 25 | Product weight and dimensions blank | 2 products | Keep blank | Excluded from weight/size analysis only | Yes |
| 26 | Misspelled column names | `product_name_lenght`, `product_description_lenght` | Rename to `..._length` in clean data | Correct, professional column names | Yes |

## Customers and geolocation

| # | Problem | Evidence | Proposed treatment | Business effect | Approved? |
|---|---|---|---|---|---|
| 27 | customer_id is per order, not per person | 99,441 customer_ids but 96,096 customer_unique_ids | No change. Use customer_unique_id when counting people | Customer counts are not inflated | Yes |
| 28 | Zip code prefixes load as numbers, losing leading zeros | e.g. '01151' loads as 1151 | Read zip code columns as text | Zip codes stay correct and can be matched | Yes |
| 29 | Exact duplicate rows in geolocation | 261,831 of 1,000,163 rows | Not used in this project (states come from customers/sellers). If used later: remove exact duplicates | None now | Yes |
| 30 | Geolocation city names with and without accents | 8,011 names shrink to 5,968 when simplified | Not used in this project | None now | Yes |
| 31 | Customer and seller zips missing from geolocation | 157 customer zips (278 customers); 7 seller zips | Not used in this project | None now | Yes |
