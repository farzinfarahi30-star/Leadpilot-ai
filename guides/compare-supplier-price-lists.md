# How to compare supplier price lists without manual spreadsheet checks

Supplier price lists change in ways that are easy to miss when rows move or product codes are formatted differently. A safer workflow is to compare by a stable product key, preserve both source files, calculate absolute and percentage changes, and keep additions/removals separate from price changes.

## Practical workflow

1. Keep the original old and new files unchanged.
2. Choose a stable key such as SKU, supplier product code, EAN or another identifier.
3. Normalize harmless formatting such as surrounding whitespace before matching.
4. Flag duplicate keys instead of silently choosing one.
5. Compare numeric price columns only after confirming units and pack sizes.
6. Separate new, removed, increased, decreased and unchanged records.
7. Export a review file before changing an ERP, store or catalogue.

## Nova local-first option

The **Nova Supplier Price Change Checker** compares two CSV exports locally in the browser. It flags new/removed keys, price increases/decreases and duplicate identifiers, then exports a change report.

**£12 one-time checkout:**  
https://buy.stripe.com/00w14n5ru7yu0Qr3tT9Zm0P

For recurring workflows:

- **Monthly — £79/month:** https://buy.stripe.com/5kQ4gz07a3iecz91lL9Zm1w
- **Weekly — £149/week:** https://buy.stripe.com/dRm4gz5ruf0W7ePfcB9Zm1x

For XLSX, export the relevant worksheet to CSV before using the local browser version.

## Safety principle

Do not silently merge ambiguous records or overwrite supplier source files. Any uncertain match should remain reviewable.
