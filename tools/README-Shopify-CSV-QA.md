# NOVA — Free Product CSV Preflight (Shopify)

A no-cost, **read-only** quality checker for a merchant's Shopify product CSV file. Useful for store operators preparing product listings or ecommerce data migrations, especially when the source has inconsistent SKUs, titles, handles or prices.

**No registration, upload, API key, network access or third-party AI needed.** The original CSV file is never modified. Python 3 standard library only.

Run:

```sh
python3 shopify_csv_qa.py shopify_products.csv
python3 shopify_csv_qa.py shopify_products.csv --json
```

The script flags errors/warnings including duplicate headers, missing product titles, invalid price formats, negative prices, unusual URL handles, invalid product statuses, duplicate SKUs on different products, inconsistent variant option columns, suspicious image URL formats, and overlong search metadata.

Supports Shopify's latest `URL handle`, `SKU`, `Price`, `Product image URL` columns as well as older `Handle`, `Variant SKU`, `Variant Price`, `Image Src` exports.

**Important:** This is a static preflight, not Shopify import certification. A product can contain multiple variant rows sharing a handle, and blank titles on subsequent variant rows can be valid. Shopify may accept additional columns/defaults; its own import preview is authoritative. **Back up your Shopify product catalogue first.** Never share customer records or private account access to obtain a free sample.

Official format details: https://help.shopify.com/en/manual/products/import-export/using-csv and https://help.shopify.com/en/manual/products/import-export/import-products

### Additional service

For businesses that need deeper help with messy product records, mapping catalogue fields, duplicates, or nonstandard CSV exports, NOVA already has the CleanSheet and Ecommerce Catalog Cleanup offer categories. Submit one specific request voluntarily at https://ai-business-factory.hatchable.site/free-help.html . The free utility carries no obligation to buy.
