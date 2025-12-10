# Data Dictionary

## Common fields (harmonized & integrated)
- `source` (string): Source system (DSLD, Amazon, Knowde, Internal).
- `source_record_id` (string): Native identifier in the source system (e.g., ASIN).
- `product_name` (string): Product title or name.
- `brand` (string): Brand as provided by the source.
- `company_name` (string): Company/manufacturer/supplier (raw).
- `company_name_final` (string, integrated only): Company name after alias mapping.
- `link` (string): Source URL when applicable.
- `on_market` (string/bool): DSLD on-market flag mapped to 1/0.
- `entry_date` (string): Timestamp or date captured by the source.
- `form` (string): Physical form or product type.
- `serving_size` (string/number): Declared serving quantity.
- `serving_unit` (string): Declared unit.
- `serving_unit_canonical` (string): Canonicalized unit (e.g., mg).
- `serving_size_mg` (number): Serving size converted to mg if possible.
- `net_quantity` / `net_unit` (string): Pack size fields when available.
- `ingredients` (string): Extracted or concatenated ingredient text.
- `ingredients_norm` (string): Normalized ingredients after synonym rules.
- `other_ingredients` (string): Other/excipients when present.
- `claims` (string): Marketing/functional claims.
- `statements` (string): Compliance/warnings/certifications text.
- `curated_id` (string, integrated only): Stable SHA-256 based identifier for de-duplication.

## UC-1 (Product list by target ingredient)
- `ingredient`, `product_name`, `brand`, `company_name`, `form`, `serving_size`, `serving_unit`, `link`, `source`.

## UC-2 (Company aggregation by target ingredient)
- `ingredient`, `company_name`, `brand_count`, `product_count`.
