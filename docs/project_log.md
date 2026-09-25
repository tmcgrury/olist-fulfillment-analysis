# E-Commerce Fulfillment and Delivery Performance Analysis

## Data source
- Olist Brazilian E-Commerce public dataset (~100k orders, 2016–2018)
- Original: `archive.zip` (kept untouched in Downloads)
- Copy extracted to `data/raw/` on 2026-09-22. Never edit files in `data/raw/`.

## Decisions log
- 2026-09-22: Project set up. Tools: Python 3.13 + pandas 3.0.
- Validation: all 9 extracted CSVs match the file sizes listed inside the zip.
- 2026-09-22: Found data issues in orders: 8 orders marked "delivered" with no delivery
  date; 6 orders NOT marked delivered but with a delivery date.
- 2026-09-22: DECISION (Option A): delivery analysis uses only orders with status
  "delivered" AND a delivery date. Script: `scripts/02_filter_delivered_orders.py`.
  Result: 99,441 -> 96,470 rows (2,971 excluded). Output: `data/processed/delivered_orders.csv`.
  Validated: only "delivered" status, 0 missing delivery dates, 0 duplicate order_ids.

- 2026-09-22: Date columns are stored as text in CSVs. `scripts/03_delivery_metrics.py`
  converts the 5 date columns to datetime on load (in memory only). Validated: all 5 became
  datetime64, missing counts unchanged, date ranges plausible (Sep 2016 - Oct 2018).
  Noted: 14 delivered orders have no approval date and 1 has no carrier date; these don't
  affect our two main metrics.

- 2026-09-22: Added `delivery_time` column (delivered - purchased) in
  `scripts/03_delivery_metrics.py`. Validated: timedelta type, 0 missing, 0 negative.
  Shortest 0.5 days, median ~10.2 days, longest ~209.6 days (possible outlier - to investigate).

- 2026-09-22: Investigated long deliveries. 306 orders took > 60 days. Not a year typo
  (delays ~6 months, not ~12). 8 of the 10 slowest were marked delivered on 2017-09-19
  between 14:00-17:15, suggesting a batch update of delivery records (hypothesis C).
  But only 28 of the 306 fall on that day, so most long deliveries are unexplained.
- 2026-09-22: DECISION (Option 2b): keep all orders; add `suspicious_date` flag =
  delivered on 2017-09-19 AND delivery_time > 60 days. Validated: 28 True, 96,442 False,
  row count unchanged (96,470). Median delivery time barely changes (10d 05:13 vs 10d 05:10),
  so these 28 don't distort the typical result.

- 2026-09-22: DECISION (Rule B): `is_late` = delivered calendar day is after the estimated
  day (estimated dates are all at 00:00, so exact-time comparison would wrongly count
  same-day deliveries as late). Result: 6,534 of 96,470 late = 6.77%
  (Rule A would give 8.11%). Without suspicious orders: 6.75%. Row count unchanged.
  My prediction was 10%.

- 2026-09-22: Reviews: 99,224 rows; 547 orders have 2-3 reviews (not exact copies; 202 of
  them disagree on score). DECISION (Option A): keep the most recent review per order
  (latest creation date; ties broken by latest answer timestamp).
  Script: `scripts/05_latest_review_per_order.py` -> `data/processed/latest_reviews.csv`.
  Validated: 98,673 rows = number of unique orders; 0 duplicate order_ids; spot-check
  order 0130... kept the later 4-star review; raw file unchanged.

- 2026-09-22: Script 03 now saves `data/processed/orders_with_metrics.csv` (96,470 rows,
  adds delivery_time, suspicious_date, is_late). Validated on reload.
- 2026-09-22: DECISION: inner join (keep only orders with both a delivery and a review).
  Script: `scripts/06_join_orders_reviews.py` -> `data/processed/orders_reviews.csv`.
  Result: 95,824 rows; 646 delivered orders had no review and were dropped from this part.
  Validated: 0 duplicate order_ids, 0 missing review scores.

- 2026-09-22: FINDING (`scripts/07_reviews_vs_lateness.py`): on-time orders avg 4.29 stars,
  6.6% one-star (n=89,443); late orders avg 2.27 stars, 53.8% one-star (n=6,381).
  Unchanged when excluding suspicious orders. My predictions: 4.5 / 2.5 / 50%.
  Caveat: shows association, not proof that lateness alone causes low scores.

- 2026-09-22: Added `days_late` (in memory, script 07) = delivered day - estimated day.
  Validated: 6,381 orders with days_late > 0 = 6,381 is_late True; 0 missing.
  FINDING: median order arrives 12 days EARLY (middle half: 7-17 days early), so
  estimated dates appear heavily padded. Range: 147 days early to 188 days late.

- 2026-09-22: Binned days_late into `lateness_group` (in memory, script 07). Validated:
  0 missing, 88,163 early (matches days_late < 0), groups sum to 95,824.
  FINDING - avg score / % one-star by group:
  Early 4.29/6.6% | On the day 4.03/8.5% | 1-3 late 3.29/25.1% | 4-7 late 2.10/58.6% |
  8-14 late 1.67/70.6% | 15+ late 1.72/69.1%.
  Damage starts at 1-3 days late, is steepest by 4-7 days, then levels off after ~1 week.
  My prediction was that the sharp drop would come at 8-14 days.

- 2026-09-22: Installed matplotlib. Script 07 saves `data/processed/score_by_lateness.csv`
  (6-row summary). `scripts/08_chart_score_by_lateness.py` draws a line chart (my choice)
  -> `outputs/score_by_lateness.png`. Validated: plotted values match the summary table.
  Note: x-axis groups have unequal widths (0 / 1-3 / 4-7 / 8-14 / 15+ days), so slopes
  between points are not "per day" rates.

- 2026-09-22: `scripts/09_late_rate_over_time.py`: added `purchase_month` (in memory,
  Option A = purchase date). Validated: 0 missing, months sum to 96,470.
  FINDING: Nov 2017 (Black Friday) late rate 12.4% on 7,288 orders (volume +63% vs Oct) -
  my prediction "higher due to volume" confirmed. BUT Feb 2018 (14.1%) and Mar 2018 (19.0%)
  were worse with normal volume, so volume alone doesn't explain lateness.
  Caveats: 2016-09 and 2016-12 have 1 order each (rates meaningless); 2016-10 has 265.
  Recent months may understate lateness: orders still in transit weren't "delivered" yet
  and are excluded by our filter.

- 2026-09-22: DECISION (Option A): monthly chart starts Jan 2017; 2016 months (267 orders)
  left out of the chart only (data unchanged). Script 09 saves
  `data/processed/late_rate_by_month.csv`; `scripts/10_chart_late_rate_over_time.py` ->
  `outputs/late_rate_over_time.png`. Validated: 20 of 23 months shown, 267 orders left out,
  footnote n = 96,203 (caught and fixed a typo of 95,203).

- 2026-09-22: Customers table: 99,441 rows, one per ORDER (customer_id is per-order);
  customer_unique_id = the real person (96,096). 0 duplicate customer_ids, 0 missing.
- 2026-09-22: `scripts/12_late_rate_by_state.py`: joined customer_state onto delivered orders.
  Validated: 96,470 rows before and after, 0 missing states, 0 duplicate order_ids.
  Helper column `delivery_days` (whole days of delivery_time, in memory) added without
  asking first - flagged to user afterwards.
  FINDING: highest late rates in Northeast (AL 21.4%, MA 17.4%, SE 15.2%) and RJ (12.1% on
  12,350 orders). Far-north states (AM, AP, RR, AC, RO) have the LONGEST deliveries
  (17-25 days median) but among the LOWEST late rates (~3%) - their promised dates must be
  more generous. My prediction (north = more late) was wrong: slow is not the same as late.
  Caveat: RR (41), AP (67), AC (80) have few orders.

- 2026-09-22: Added `late_orders` to state summary. Validated: sums to 6,534. RJ = 1,495.
- 2026-09-22: `scripts/13_spike_by_state.py`: Feb-Mar 2018 = 13,558 orders, 2,254 late
  (34% of ALL late orders in the dataset came from these 2 months).
  FINDING: spike was NATIONWIDE - every large state rose sharply (SP 3.9->8.4%,
  MG 2.9->14.6%, RS 4.4->16.4%) - but hit RJ hardest: 8.5% -> 34.3%, and RJ alone was 26.5%
  of spike late orders. CE 8.7 -> 45.2% (small n=177). Suggests a nationwide cause (e.g.
  carrier/logistics disruption) that was worst in RJ. Cause still unknown.
  Helper column `in_spike` added without asking first - flagged to user afterwards.

- 2026-09-22: Order items: 112,650 rows (one per item); 1,278 orders have >1 seller.
  DECISION (A): seller analysis uses single-seller orders only.
  DECISION: seller_late = order_delivered_carrier_date > shipping_limit_date (exact times).
  `scripts/15_seller_vs_carrier.py`. Validated: 96,470 -> 95,195 rows; the 1,275 dropped are
  exactly the delivered multi-seller orders; 0 duplicates; single-seller orders have one
  deadline each; 1 order has no carrier date (counted as seller not late).
  FINDING: during Feb-Mar 2018, sellers barely changed (late handoff 8.9% -> 10.4%), but
  orders handed over ON TIME still arrived late 15.5% of the time vs 3.8% normally (4x).
  Seller was also late in only 17% of spike late orders vs 33% normally.
  => The spike was mainly a CARRIER problem. My prediction (carriers) confirmed.

- 2026-09-22: Adopted the 12-phase project plan and target repository structure
  (4 pipeline scripts, docs/ folder, Excel + Power BI deliverables). Reorganized: created
  data/interim, docs, excel, powerbi, images, exploration; moved the 15 exploratory
  scripts to exploration/ and the 2 charts to images/; removed empty outputs/.
  Validated: 15 scripts in exploration, 0 in scripts, 2 charts in images, 9 raw files intact.
  Note: exploratory chart scripts still save to outputs/ (historical record, not pipeline).
  Folder rename to olist-fulfillment-analysis: user will do it in File Explorer at Phase 12.
  Power BI Desktop not installed yet (needed for Phase 10).

- 2026-09-22: PHASE 1 COMPLETE. Business problem + 9 analytical questions + 8 KPI definitions
  saved in docs/business_questions.md. DECISIONS: on-time rate = 100% - late rate; transit time
  excludes the 1 order with no carrier date (this KPI only); average review score is per order
  (latest review), no-review orders excluded; freight % = total freight / total price (Option A).

- 2026-09-22: PHASE 2 started. `scripts/01_profile_data.py` (pipeline) tests primary keys of
  all 9 raw tables. Unique: orders, customers, order_items (order_id+order_item_id),
  order_payments (order_id+payment_sequential), products, sellers, category_translation.
  NOT unique: geolocation zip prefix (1,000,163 rows, many points per zip - no single key);
  review_id (789 review_ids shared by 1,603 rows). Investigation: 0 exact duplicate rows;
  repeated rows are identical except order_id => one review applied to several orders.
  True review key = review_id + order_id (0 duplicates). Per-order analysis unaffected;
  counting "number of reviews" would need distinct review_id.
  Spelling issue: products columns `product_name_lenght`, `product_description_lenght`.

- 2026-09-22: Foreign key test (01_profile_data.py section 4). All order/customer/product/
  seller links: 0 unmatched. products.product_category_name: 610 blank, 13 products in 2
  untranslated categories (pc_gamer, portateis_cozinha_e_preparadores_de_alimentos).
  Zip prefixes missing from geolocation: 278 customers (157 zips), 7 sellers (7 zips).

- 2026-09-22: Installed openpyxl 3.1.5; created requirements.txt (pandas, matplotlib, openpyxl).
  01_profile_data.py section 5 builds data_dictionary.xlsx (Tables / Columns / Relationships).
  Descriptions live in docs/column_descriptions.csv (hand-written, merged in, never overwritten).
  Validated: 9 tables, 52 columns, 9 relationships; row counts match earlier checks.
  NEW FINDING: geolocation has 261,831 exact duplicate rows (only table with any).
  8 orders column descriptions left for user to write.

- 2026-09-22: Created README.md skeleton (business problem, relationship map, keys, join
  warning, structure, how to run). PHASE 2 COMPLETE.
- 2026-09-22: PHASE 3 started. 01_profile_data.py section 5 = date sequence test (dictionary
  moved to section 6). Violations: approved > carrier 1,359 (1.39%); carrier > delivered 23
  (0.02%); purchase<=approved, purchase<=delivered, purchase<=estimated all 0.
  Investigation: shipped-before-approved gaps are small and consistent (median 17 h, middle
  half 1.4-26 h) => mostly a real process (ship while approval completes); a few extreme
  (max 171 days) look like errors. 1,350 delivered + 9 shipped. Affects approval-time KPI only.
  Delivered-before-carrier: 23 orders, all 2016-2017, gaps 30 min to 16 days => data entry /
  timestamp errors. DECISION (user): exclude these 23 from transit time only (with the 1 missing
  carrier date, transit time excludes 24 delivered orders). Keep in all other KPIs.

- 2026-09-22: Numeric check (01_profile_data.py section 6; dictionary now section 7).
  price: 0 zeros (min 0.85) => freight % never divides by zero. freight_value: 383 zeros =
  free shipping (real, keep). payment_value: 9 zeros (6 voucher, 3 'not_defined').
  payment_installments: 2 zeros on credit_card (impossible - should be >= 1).
  payment_type has unexpected value 'not_defined' (3 rows). review_score all 1-5.
  product_weight_g: 4 zeros (impossible) + 2 blank; dimensions 2 blank.
  610 products blank on category AND photos (same products - missing product info).
  Extremes (price 6,735; payment 13,664; weight 40 kg) look unusual but plausible.
  None of these affect delivery KPIs. Treatment to be decided in Phase 4.

- 2026-09-22: Text check (01_profile_data.py section 7; dictionary now section 8).
  customer_city: clean (lowercase, no accents). States: clean 2-letter uppercase codes.
  seller_city: messy - 'são paulo' accent variant, city/state combos ('maua/sao paulo',
  'sp / sp'), a zip code ('04482255') and an email address ('vendas@creditparts.com.br').
  geolocation_city: 8,011 distinct -> 5,968 after removing accents/case/spaces
  (e.g. 'sao paulo' 135,800 rows vs 'são paulo' 24,918).
  No uppercase city names anywhere (user predicted 'SAO PAULO' - not present).
  Our analysis uses states (clean), so delivery KPIs unaffected.
  Data type issue spotted: zip code prefixes load as numbers, dropping leading zeros
  (e.g. '01151' -> 1151). Must be read as text.

- 2026-09-22: PHASE 3 COMPLETE. PHASE 4 COMPLETE: docs/cleaning_log.md lists 31 problems with
  evidence, treatment and business effect - all 31 approved by user.

- 2026-09-22: PHASE 5 started. DESIGN (approved): 02_clean_data.py fixes values only, removes no
  rows; 03_build_tables.py adds flags; KPIs filter by flags.
  scripts/02_clean_data.py applies cleaning log #4, #18, #20, #22, #23, #24, #26 (user wrote the
  rename line), #28. Writes 8 tables to data/interim/ (geolocation not used).
  Validated: every fix before->after as expected (#24 blank weights = 6 = 2 original + 4 zeros);
  row counts unchanged (translation 71 -> 73, +2 added rows); reloaded files keep fixes.
  NOTE for 03: CSVs lose types - must re-read zip codes with dtype=str (reloading without it
  turns '01151' back into 1151) and re-parse dates.

- 2026-09-22: PHASE 6/7. Approved 8-table star schema. DECISIONS: order_value = sum of item
  prices (Option A, excludes freight); review_group = Negative 1-2 / Neutral 3 / Positive 4-5
  (Option A). All calculated-field definitions + KPI filters saved in docs/business_questions.md.
  scripts/03_build_tables.py writes 4 facts + 4 dims to data/processed/ (fact_orders 99,441 x 26,
  fact_order_items 112,650, fact_payments 103,886, fact_reviews 99,224, dim_customer 99,441,
  dim_seller 3,095, dim_product 32,951, dim_date 800 days).
  Quick reconciliation: every field reproduces exploration results exactly (96,470 delivered,
  6,534 late, 6.77%, 28 suspicious, 96,446 valid transit, median 10.22 days, variance -12,
  95,824 reviewed, 4.29 vs 2.27 stars, seller late 9.1%); 0 negative transit; 0 duplicate orders.
  DECISION (Option A): moved the 7 old exploratory CSVs to exploration/outputs/. data/processed/
  now holds only the 8 final tables. (Old exploration scripts reference the old paths.)
  User correctly worked a manual example: delivered on the estimated day at 16:45 => not late,
  variance 0.

- 2026-09-22: PHASE 8. scripts/04_validate_outputs.py writes docs/validation_report.md.
  35 checks: row counts, money totals (prices 13,591,643.70; freight 2,251,909.54; payments
  16,008,872.12 - all match raw to the cent), unique keys, date logic, independent
  recalculation, known results, cleaning log #21 (13,664.08 payment = its items + freight:
  CONFIRMED REAL), plus 6 manual scenario examples (A-F).
  First run: 34/35 - freight_pct check failed on 1 order due to floating-point rounding at a
  boundary (difference 3.6e-15), a flaw in the CHECK not the data. Fixed with a tolerance.
  Final: 35/35 PASS. Avoided installing `tabulate` by writing a small markdown_table function.

- 2026-09-22: PHASE 9. DECISIONS: Clean Order Data = all 99,441 orders, key columns only (B);
  dashboard KPIs = late rate, delivery time (median headline + average beneath, C), avg review
  score; summary tables as live Excel formulas (A); new script scripts/05_build_excel.py (A).
  Workbook excel/olist_fulfillment_analysis.xlsx (~10 MB): README, Dashboard, KPI Definitions,
  Clean Order Data (99,441 x 17), Pivot Analysis (month / state / lateness tables), Data Validation.
  Recalculated in Excel: 0 formula errors; Excel vs Python 10/10 PASS (after giving each check a
  visible tolerance - money totals differ by 0.0000121 from summation order).
  Visual check found chart problems (hidden axes, smoothed line, heavy gridlines, overlapping axis
  titles, multi-coloured markers) - all fixed and re-checked. README updated with script 05.

- 2026-09-22: PHASE 11 started. Approved scripts/06_answer_questions.py + outputs/ folder.
  Q6 (user predicted: concentrated): seller KPI = 96,380 single-seller orders with a carrier
  date, 8,797 late handoffs (9.1%), 2,955 sellers. Among sellers with 50+ orders (415), the top
  10% (42 sellers) handle 29.0% of orders but cause 51.1% of late handoffs. Median seller late
  rate 4.9% vs overall 9.1%. Holds at 20+ (58.1%) and 100+ (44.1%) thresholds. Top sellers'
  rates barely change outside the Feb-Mar 2018 spike (e.g. 29.8% vs 29.5%) => consistent,
  not spike-driven. PREDICTION CONFIRMED.

- 2026-09-22: Q7 (user predicted: furniture / office furniture, because of weight). 95,690 of
  96,470 delivered orders are single-category (780 mixed left out). 26 categories with 500+
  orders; late rates only range 4.3% (luggage) to 8.2% (baby, office_furniture). Office furniture
  tied highest (8.2%, median 11.9 kg) - partly confirmed; furniture_decor 7.3% (mostly light).
  Weight gradient is real but modest: <0.5 kg 6.5% -> 20+ kg 9.4% late; median delivery
  9.8 -> 12.7 days. Light categories (baby 0.7 kg, electronics 0.2 kg) are also near the top,
  so weight is not the only driver. Category/weight effect is SMALL compared with state
  (3-21%) and seller (median 4.9%, top sellers ~30%). PREDICTION PARTLY CONFIRMED.

- 2026-09-22: Q8 (user predicted: higher freight and higher value -> late more often).
  Freight quintiles: 4.4% -> 8.1% late (confirmed on the surface). BUT within Sao Paulo only,
  flat (3.9-5.1%) => freight mostly reflects DISTANCE (remote states pay ~2.5-3x more freight:
  AC 39 vs SP 14 median). Freight is a confounded proxy, not a cause. Order value quintiles:
  5.9% -> 7.5% (confirmed, small). Freight % of order value: no pattern (6.4-7.0%).
  Quintiles sum to 96,470 delivered orders.

- 2026-09-22: Q9 (user predicted: remote northern states more padded). CONFIRMED. Overall:
  promised 24 days (median), actual 10.2, arrives 12 days early; only 8.2% arrive within
  +/-3 days of the promise. Most padded: AC/AP 22 days early, RO 21, RR 20, AM 19 (late rates
  ~3%, except RR 12.2% on 41 orders). Least padded: AL 10 days (21.4% late), MA 11 (17.4%),
  SP 11 (4.5% - fast deliveries, 7.2 days). Correlation across states between padding and
  late rate: -0.56 (more padding, fewer late orders).

- 2026-09-22: Q1-Q5 re-answered from final tables in 06_answer_questions.py - all match
  exploration (6.77%, 10.22 median, 4.29 vs 2.27, 53.8% one-star, Nov 2017 12.4%, Mar 2018 19.0%,
  RJ 1,495 late, AL 21.4%, carrier 3.8% -> 15.5%). New: median transit 7.10 days; Feb-Mar 2018 =
  34.5% of all late orders. One tiny difference: Q5 "other months" 81,776 vs 81,777 in exploration
  - the pipeline correctly excludes the 1 order with no carrier date (approved KPI filter).
  15 result tables in outputs/. Script exits cleanly (code 0).

- 2026-09-22: docs/findings.md drafted with user, sections 1-6 (What / Where / How large /
  Connected / Not proven / Recommendations). User wrote the core of each section; Claude tidied
  wording, added numbers, and drafted extra limits (section 5) and recommendations 2-4
  (section 6). User reviewed and APPROVED the full document. PHASE 11 COMPLETE.

- 2026-09-22: PHASE 10 (Power BI, built by user with guidance). Loaded 8 tables - all row counts
  match; zip codes fixed to Text. Added purchase_day (Date only) to fact_orders in Power Query for
  the dim_date relationship. 7 relationships (star schema), no warnings. 12 DAX measures created;
  all match Python (see docs/validation_report.md). Freight % measure = total freight / total
  order value (weighted). Cards abbreviate (96K) - display only; verified exact via Table visual.

- 2026-09-24: Power BI pages 1 (Executive Overview) and 2 (Delivery Performance) built by user;
  all numbers verified (incl. slicer 2016/2018 checks). Fixed a missing dim_date relationship
  (symptom: flat line) and year_month auto-detected as a date hierarchy.
  DECISION (Option A): added seller_id to fact_orders in 03_build_tables.py (single-seller orders
  only; blank for 1,278 multi-seller + 775 no-item orders). 97,388 orders have a seller.
  Validation now 37/37 (2 new seller_id checks). fact_orders 99,441 x 27.
  Power BI refresh then failed ("review_group not found") - schema change: the CSV source step had
  Columns=26 fixed. User fixed via Advanced Editor (26 -> 27). Relationship ambiguity
  (fact_order_items -> dim_seller vs via fact_orders) resolved by deactivating the item-level one.
  Also re-fixed dim_seller/dim_customer zip codes (type set at original Changed Type step).
- 2026-09-24: DECISION (Option A): added main_category (single-category orders only) and
  order_weight_kg (blank if any item weight unknown) at the END of fact_orders (29 columns).
  Validation 40/40 - reproduces Q7 exactly (95,690 single-category, 96,448 known weight,
  office furniture 8.15%).

- 2026-09-24: PHASE 10 COMPLETE. 5 Power BI pages built by user: Executive Overview, Delivery
  Performance, Seller and Product Analysis, Customer Experience, Investigation Detail (with
  drill-through on customer_state and seller_id; RJ drill-through -> 12,350 delivered).
  All visuals checked against Python. Fixed along the way: inactive/wrong-active seller
  relationship, stuck blank-seller selection, leftover slicer selections, date hierarchies.
  Added DAX calculated columns Weight Band and Lateness Group; measures Seller Handoff Orders,
  Late Handoffs, Reviewed Orders, Median Fulfillment Days, Median Promised Days.
  .pbix and dashboard_preview.png had been saved to OneDrive (Documents / Pictures); COPIED into
  powerbi/ and images/ (originals untouched). NOTE for Phase 12: the .pbix reads CSVs by absolute
  path - renaming the project folder will require updating Power BI's data source paths.

- 2026-09-24: PHASE 12. DECISIONS: publish on GitHub; keep exploration/ (noted in README);
  notes.md moved to docs/project_log.md (this file); no data files published (.gitignore excludes
  data/raw, interim, processed and exploration/outputs/*.csv; .gitkeep keeps the folders).
  Final README drafted for user review. Git is not installed yet.
  DECISION (Option A): upload excel/*.xlsx and powerbi/*.pbix even though they embed derived
  order-level data (no personal details), so viewers can open the real deliverables.

- 2026-09-24: Renamed project folder ecommerce-fulfillment-analysis -> olist-fulfillment-analysis
  (86 files before and after). Rename was blocked by the app's Terminal-panel shell started in
  the old folder; user approved stopping that process. Pipeline rerun from new location:
  scripts 01-04 OK, validation 40/40. Script 06 failed - BUG from adding order_weight_kg to
  fact_orders (06 recomputed it and the merge created _x/_y columns). Fixed: 06 now uses
  main_category / order_weight_kg from fact_orders (one definition, in 03). Q7 results identical.
  Removed unused dim_product load. User updated Power BI data source paths; numbers match.
  README.md reviewed and APPROVED by user.
- 2026-09-24: PHASE 12 COMPLETE. Published publicly with GitHub Desktop:
  https://github.com/tmcgrury/olist-fulfillment-analysis
  Verified: 55 files committed, 0 data CSVs; README renders with both images; all 10 linked
  files return HTTP 200; findings section-5 anchor works. ALL 12 PHASES COMPLETE.

## Definitions
- Delivery time = purchase date -> delivered-to-customer date
- Late = delivered-to-customer calendar day is after the estimated delivery day (Rule B)
- Seller late = handed to carrier after the seller's shipping_limit_date (exact times)
- Suspicious date = delivered on 2017-09-19 AND delivery time > 60 days (likely bulk record update)

## Answered questions
- Orders link to customers through `customer_id` (not order_id).
