# PC Builder Phase 5 — Initial estimated prices (AUD)

**Created 25 October 2026.** This package was generated from `null_prices_comopnents.csv` (2,478 records), exported from your existing `pc_building_system.component` table.

## Important: what these prices are

These are **synthetic demonstration estimates** generated using **AI-assisted, rule-based heuristics**, not quotes verified individually from online retailers. The estimates are intended to make initial PC build budgets and filters usable before your planned live price-check feature is implemented. **Never label these values as "live prices", "verified prices" or actual offers.** A component's BuildCores `source` URL identifies its technical specification record; it is **not a price source**.

Model-specific and category-level rules estimate approximate AUD prices using GPU chipset tiers, CPU families, motherboard chipsets, RAM generation/capacity/speed, SSD capacity/interface, and PSU wattage/certification. Some indicative anchor ranges were cross-checked against Australian retailer/price-comparison examples, but **no per-component price verification occurred**. Used/older GPU prices are particularly uncertain. The price estimate does not imply a current sale, stock availability, or consistent new-versus-used condition.

## Files

- `price_seed_review.csv` — 2,478 estimated AUD prices; includes IDs, categories, names, release years, explanation of each estimate, validation flags, original *specification* source URLs.
- `validation_flags_review.csv` — entries requiring extra attention. Flags are warnings and not necessarily errors.
- `price_seed_summary.txt` — quantity, price distributions and flag counts.
- `price_seed_review_then_apply.sql` — a transaction with 2,478 guarded `UPDATE` statements. **Ends in `ROLLBACK` by default**.
- `generate_price_seed.py` — reproducible local script, using only Python's standard library, to regenerate the CSV and SQL from your supplied export. It does not call any external APIs.

## Before updating MySQL

1. Back up the **structure AND data** of `pc_building_system` in MySQL Workbench.
2. Review `price_seed_review.csv`, especially `validation_flags_review.csv`. Adjust any unacceptable estimates in the **generator** and regenerate the files, or update the corresponding SQL statements manually (keeping the price as an estimate).
3. Open `price_seed_review_then_apply.sql` in MySQL Workbench. Make sure your connection is to the correct server and schema.
4. Execute the SQL once with its original last line: `ROLLBACK;` — this will show the pending aggregate results **without saving** any changes.
5. Once you approve the data, change the final `ROLLBACK;` to `COMMIT;` and execute the entire script again.
6. Run:

```sql
USE pc_building_system;
SELECT category,
       COUNT(*) AS components,
       SUM(price IS NULL) AS missing_prices,
       SUM(JSON_UNQUOTE(JSON_EXTRACT(specifications, '$.price_metadata.type')) = 'synthetic_estimate') AS seeded_estimates
FROM component
GROUP BY category;
```

The SQL will only update rows whose `component_id`, `category`, `manufacturer`, and `model` **still match your export** and whose `price IS NULL`. It does **not** change the existing schema, delete components, overwrite non-NULL prices, or remove existing specification fields. It **adds** `price_metadata` to each updated component's existing JSON specifications. If your database changed since the CSV export, unmatched rows will be skipped.

## How to label the price in your UI

In the FastAPI response, read `specifications.price_metadata.type`:

- `synthetic_estimate`: show **Estimated A$X — demo price, not verified**. No retailer link; `estimated_at` is the seed date, **not** a live check timestamp.
- A later confirmed online price: store `type: verified_online`, the validated URL and an actual `checked_at` timestamp; show **Price checked on ...**.
- No metadata: show **Stored price — provenance unknown** (relevant to the original 25 Phase 3 records) until you can verify its origin.

Only a user-initiated, independently validated online search should replace the estimate with a verified price; use the current price-cache/quota rules we discussed. **Do not charge quota for displaying seeded prices.**

## Data-quality observations

- The original CSV output had invalid CSV quoting in the `specifications` JSON field. The generator recovered all 2,478 JSON objects by parsing their literal source text; the resulting `price_seed_review.csv` is valid CSV.
- All exported `release_date` values were NULL. Release year was taken from the nested JSON field `release_year`; no exact release date was invented.
- Some BuildCores release years appear inconsistent with processor generations. These have flags; the underlying JSON was not silently rewritten.
- Very large RAM kits, specialised workstation GPUs and high-end model variants have highly uncertain prices. Review these if they appear in your product catalogue or recommendation outputs.
- All estimates are fixed at seed generation time and will go stale; your planned shared AI online lookup is the appropriate way to upgrade those values.

## A few category price anchors inspected (25 Oct 2026)

These are examples used only to sanity-check the general magnitude of some heuristics; no row in the generated CSV claims its individual price was sourced from one of these pages.

- Australian CPU product prices: https://www.umart.com.au/pc-parts/computer-parts/cpu-processors/amd-cpu-646
- Australian PC component comparison examples (RTX 5070, 5070 Ti, RTX 5090, 7800X3D, motherboards, PSUs, etc.): https://www.priceroo.com.au/en/category/computing/components/
- Australian AM5 motherboard listing examples: https://www.umart.com.au/pc-parts/computer-parts/motherboards/amd-am5-1115
- DDR5 RAM listing examples: https://www.staticice.com.au/cgi-bin/search.cgi?q=ddr5+32gb+kit+6000

For documentation and assessment, describe this as **"synthetic initial price data, produced by AI-assisted estimation rules and separately labelled from web-checked prices."**
