# NOVA — Excel data-cleaning QA demonstrator

**Synthetic data only.** This is a public skills demonstration, **not client work**, not a customer testimonial, and not proof that any paid assignment was accepted.

## What this demonstrates

A reviewable spreadsheet-cleanup workflow that avoids inventing missing input values.

- Keep original exported values and row references intact.
- Detect duplicate SKUs with `COUNTIF` (only later occurrences flagged).
- Identify records with missing SKU, product name, or status.
- Flag missing, nonnumeric or nonpositive prices.
- Distinguish rows that pass all checks from rows requiring human review.
- Return an Excel QA summary. Cleaned data is **never silently assumed correct**.

## Ten sample rows (fictional)

| Row | SKU | Product | Status | Price (GBP) | Duplicate SKU | Missing essential | Price validation | Outcome |
|---:|---|---|---|---:|---|---|---|---|
| 1 | A-101 | Basic Shirt | Active | £14.00 | OK | OK | OK | PASS |
| 2 | A-102 | Heavy Hoodie | Active | £29.00 | OK | OK | OK | PASS |
| 3 | A-102 | Heavy Hoodie | Active | £29.00 | DUPLICATE | OK | OK | REVIEW |
| 4 | A-103 | Mug | Active | — | OK | OK | MISSING_PRICE | REVIEW |
| 5 | — | Sticker Set | Active | £6.00 | NEEDS_REVIEW | MISSING_FIELDS | OK | REVIEW |
| 6 | A-104 | Notebook | Active | £9.50 | OK | OK | OK | PASS |
| 7 | A-105 | Canvas Tote | Inactive | £0.00 | OK | OK | NONPOSITIVE_PRICE | REVIEW |
| 8 | A-106 | Cap | Active | £11.00 | OK | OK | OK | PASS |
| 9 | A-107 | Crew Hoodie | Active | £29.00 | OK | OK | OK | PASS |
| 10 | A-108 | Socks | Active | £5.00 | OK | OK | OK | PASS |

**Validation totals:** 10 source records, 1 duplicate SKU, 1 row missing essential fields, 2 rows with missing or nonpositive prices, **6 passed**.

## Example Excel formulas

Suppose the audit table begins at row 5, where column B is SKU, C product, D status, E price, F duplicate status, G missing-field status, H price validation, I overall outcome.

```excel
=IF(B5="","NEEDS_REVIEW",IF(COUNTIF($B$5:B5,B5)>1,"DUPLICATE","OK"))
=IF(OR(B5="",C5="",D5=""),"MISSING_FIELDS","OK")
=IF(OR(E5="",NOT(ISNUMBER(E5))),"MISSING_PRICE",IF(E5<=0,"NONPOSITIVE_PRICE","OK"))
=IF(AND(F5="OK",G5="OK",H5="OK"),"PASS","REVIEW")
```

## Paid-project workflow

1. Agree on the input file size and permitted processing.
2. Preserve untouched source data.
3. Apply transparent normalization and formula/field checks.
4. Check a sample against raw rows; mark ambiguity for client review.
5. Deliver a cleaned XLSX file with QA summary and short handoff notes.

**No guaranteed accuracy or revenue claims.** Results depend on the customer-supplied data, mutually agreed rules and final QA.

NOVA | AI-assisted, human-reviewed spreadsheet services.
