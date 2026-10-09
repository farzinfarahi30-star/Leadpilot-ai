#!/usr/bin/env python3
"""NOVA read-only Shopify CSV quality audit. No upload, web calls or dependencies."""
import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

ALIASES = {
    "handle": ("URL handle", "Handle"),
    "title": ("Title",),
    "sku": ("SKU", "Variant SKU"),
    "price": ("Price", "Variant Price"),
    "status": ("Status",),
    "image": ("Product image URL", "Image Src"),
    "option_name": ("Option1 name", "Option1 Name"),
    "option_value": ("Option1 value", "Option1 Value"),
    "seo_title": ("SEO title", "SEO Title"),
    "seo_description": ("SEO description", "SEO Description"),
}

def audit(path):
    issues = []
    def report(row, severity, field, description):
        issues.append(dict(row=row, severity=severity, field=field, message=description))
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        if not columns:
            raise ValueError("The CSV header row is missing.")
        for col, count in Counter(columns).items():
            if count > 1:
                report(1, "error", col, "Duplicate CSV column header.")
        alias = {k: next((x for x in variants if x in columns), None)
                 for k, variants in ALIASES.items()}
        if not alias["title"]:
            report(1, "error", "Title", "A Title column is required.")
        if not alias["handle"]:
            report(1, "warning", "URL handle", "Missing handle, needed for variants and updates.")
        rows = list(reader)
        all_handles = defaultdict(list)
        sku_handles = defaultdict(set)
        for lineno, row in enumerate(rows, start=2):
            def value(field):
                return str(row.get(alias[field]) or "").strip() if alias[field] else ""
            if None in row:
                report(lineno, "error", "CSV", "More values than headers; inspect quoting.")
            handle = value("handle")
            title = value("title")
            sku = value("sku")
            price = value("price")
            if handle:
                all_handles[handle].append((lineno, title))
                if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9-]*", handle):
                    report(lineno, "warning", "URL handle", "Unusual handle; check allowed characters in Shopify.")
            if sku:
                sku_handles[sku].add(handle or "[row " + str(lineno) + "]")
            if price:
                try:
                    if Decimal(price) < 0:
                        report(lineno, "error", "Price", "Negative product price.")
                except InvalidOperation:
                    report(lineno, "error", "Price", "Price must be a number without a currency symbol.")
            elif alias["price"] and value("status").lower() == "active":
                report(lineno, "warning", "Price", "Blank price on active product may default to zero.")
            if alias["status"] and value("status") and value("status").lower() not in {"active", "draft", "archived"}:
                report(lineno, "error", "Status", "Use active, draft or archived.")
            if alias["image"] and value("image") and not value("image").startswith(("http://", "https://")):
                report(lineno, "warning", "Product image URL", "Image URL is not absolute http(s).")
            if alias["option_value"] and value("option_value") and not value("option_name"):
                report(lineno, "warning", "Option1", "Option name missing for nonempty value.")
            if alias["seo_title"] and len(value("seo_title")) > 70:
                report(lineno, "warning", "SEO title", "Over Shopify's 70-character guidance.")
            if alias["seo_description"] and len(value("seo_description")) > 320:
                report(lineno, "warning", "SEO description", "Over Shopify's 320-character guidance.")
        for handle, entries in all_handles.items():
            if not any(title for _, title in entries):
                report(entries[0][0], "error", "Title", "No product title for handle: " + handle)
        if not alias["handle"]:
            for lineno, row in enumerate(rows, start=2):
                if not str(row.get("Title") or "").strip():
                    report(lineno, "warning", "Title", "Blank title with no handle.")
        for sku, handles in sku_handles.items():
            if len(handles) > 1:
                report("multiple", "warning", "SKU", "SKU reused across distinct handles: " + sku)
        return {
            "tool": "NOVA Shopify CSV Preflight v1",
            "file": Path(path).name,
            "rows": len(rows),
            "errors": sum(i["severity"] == "error" for i in issues),
            "warnings": sum(i["severity"] == "warning" for i in issues),
            "issues": issues,
            "disclaimer": "Read-only heuristic. Review in Shopify's own import preview. No import or commercial outcome guaranteed.",
        }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", help="Local Shopify product CSV (never uploaded)")
    parser.add_argument("--json", action="store_true", help="Machine-readable report")
    args = parser.parse_args()
    try:
        result = audit(args.csv_file)
    except (OSError, ValueError, UnicodeError, csv.Error) as error:
        parser.exit(2, "CSV error: " + str(error) + "\n")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("NOVA preflight: {rows} rows, {errors} errors, {warnings} warnings".format(**result))
        for issue in result["issues"]:
            print("{severity}: row {row}, {field}: {message}".format(**issue))
        print(result["disclaimer"])
    return 2 if result["errors"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
