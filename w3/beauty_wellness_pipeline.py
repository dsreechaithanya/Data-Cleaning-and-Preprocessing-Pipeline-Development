"""
Beauty & Wellness Product Data Cleaning Pipeline
=================================================

A standalone, dependency-free Week 3 submission. Uses only the Python standard
library, so it can run without installing pandas, NumPy, or other packages.

What it does
------------
* Reads a CSV or runs a built-in 10-row synthetic demonstration.
* Preserves raw source fields and records cleaning flags.
* Removes exact duplicate rows and saves them for audit.
* Quarantines rows missing a product name or source record ID.
* Normalizes category labels and parses product sizes, prices, ratings, and
  review counts with explicit validation.
* Writes cleaned data, quarantined rows, removed duplicates, and a JSON report.

CSV input columns (required)
---------------------------
source_record_id, product_name, category, ingredients_text, size, price,
rating, review_count

Optional columns are retained. Keep barcode/identifier values as text in the
CSV to preserve leading zeros. Price parsing recognizes $, USD, EUR, GBP, and
the symbols $, €, and £. Prices with ambiguous decimal conventions are flagged
instead of guessed. Review counts treat commas as thousands separators.

Run
---
    python beauty_wellness_pipeline.py --demo
    python beauty_wellness_pipeline.py products.csv
    python beauty_wellness_pipeline.py products.csv --output-dir results

No real external dataset is included. The demo records are invented examples;
their results must not be reported as real-world findings.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = (
    "source_record_id",
    "product_name",
    "category",
    "ingredients_text",
    "size",
    "price",
    "rating",
    "review_count",
)

CATEGORY_ALIASES = {
    "moisturizer": "moisturizer",
    "moisturiser": "moisturizer",
    "face moisturizer": "moisturizer",
    "serum": "serum",
    "sun care": "sun care",
    "suncare": "sun care",
    "sunscreen": "sun care",
    "cleanser": "cleanser",
    "body lotion": "body lotion",
}

CURRENCY_MARKERS = (
    ("USD", ("USD", "$")),
    ("EUR", ("EUR", "€")),
    ("GBP", ("GBP", "£")),
)

DEMO_ROWS = [
    {
        "source_record_id": "S001",
        "product_name": " Glow Serum ",
        "category": "Serum",
        "ingredients_text": "Aqua, Glycerin",
        "size": "30 ml",
        "price": "$18.00",
        "rating": "4.5",
        "review_count": "42",
    },
    {
        "source_record_id": "S002",
        "product_name": "Daily Cream",
        "category": "Moisturiser",
        "ingredients_text": "Aqua, Shea Butter",
        "size": "50ml",
        "price": "USD 24",
        "rating": "4.2",
        "review_count": "80",
    },
    {
        "source_record_id": "S003",
        "product_name": "Gentle Cleanser",
        "category": "Cleanser",
        "ingredients_text": "Aqua, Glycerin",
        "size": "150 ml",
        "price": "$12.00",
        "rating": "4.1",
        "review_count": "15",
    },
    {
        "source_record_id": "S004",
        "product_name": "Vitamin C Serum",
        "category": "Serum",
        "ingredients_text": "Aqua, Ascorbic Acid",
        "size": "30 ml",
        "price": "$22.00",
        "rating": "8.2",
        "review_count": "100",
    },
    {
        "source_record_id": "S005",
        "product_name": "Barrier Balm",
        "category": "Moisturizer",
        "ingredients_text": "",
        "size": "40 g",
        "price": "$16.00",
        "rating": "",
        "review_count": "0",
    },
    {
        "source_record_id": "S006",
        "product_name": "Body Lotion",
        "category": "Body Lotion",
        "ingredients_text": "Aqua, Glycerin",
        "size": "200 ml",
        "price": "-3.00",
        "rating": "4.0",
        "review_count": "9",
    },
    {
        "source_record_id": "S007",
        "product_name": "Night Oil",
        "category": "Face Oil",
        "ingredients_text": "Squalane, Tocopherol",
        "size": "30mL",
        "price": "USD 28",
        "rating": "4.7",
        "review_count": "1,200",
    },
    {
        "source_record_id": "S008",
        "product_name": "Sun Cream",
        "category": "Sun Care",
        "ingredients_text": "Aqua, Zinc Oxide",
        "size": "50 ml",
        "price": "$19.00",
        "rating": "4.3",
        "review_count": "76",
    },
    {
        "source_record_id": "S001",
        "product_name": " Glow Serum ",
        "category": "Serum",
        "ingredients_text": "Aqua, Glycerin",
        "size": "30 ml",
        "price": "$18.00",
        "rating": "4.5",
        "review_count": "42",
    },
    {
        "source_record_id": "S010",
        "product_name": "",
        "category": "Serum",
        "ingredients_text": "Aqua",
        "size": "30 ml",
        "price": "$10.00",
        "rating": "4.0",
        "review_count": "2",
    },
]


def clean_text(value: Any) -> str:
    """Strip surrounding whitespace; preserve the original in a separate field."""
    return "" if value is None else str(value).strip()


def parse_size(value: Any) -> tuple[str, str, str]:
    """Return (numeric value, normalized unit, error flag)."""
    text = clean_text(value)
    if not text:
        return "", "", "size_missing"

    match = re.fullmatch(
        r"\s*(\d+(?:\.\d+)?)\s*(ml|mL|l|L|g|kg)\s*",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return "", "", "size_unparseable"

    amount = float(match.group(1))
    unit = match.group(2).lower()
    if amount <= 0:
        return "", unit, "size_not_positive"

    normalized_unit = {"ml": "mL", "l": "L", "g": "g", "kg": "kg"}[unit]
    return format(amount, "g"), normalized_unit, ""


def parse_price(value: Any) -> tuple[str, str, str]:
    """Parse a simple decimal price and explicit recognized currency, if present."""
    text = clean_text(value)
    if not text:
        return "", "", "price_missing"

    upper = text.upper()
    currency = ""
    remainder = text
    for code, markers in CURRENCY_MARKERS:
        for marker in markers:
            if marker in upper:
                currency = code
                if marker.isalpha():
                    remainder = re.sub(
                        re.escape(marker), "", remainder, flags=re.IGNORECASE
                    )
                else:
                    remainder = remainder.replace(marker, "")
                break
        if currency:
            break

    remainder = remainder.strip().replace(" ", "")
    if not remainder:
        return "", currency, "price_unparseable"

    # Commas are accepted only as conventional three-digit grouping, e.g. 1,200.
    if "," in remainder:
        if not re.fullmatch(r"-?\d{1,3}(?:,\d{3})+(?:\.\d+)?", remainder):
            return "", currency, "price_ambiguous_or_unparseable"
        remainder = remainder.replace(",", "")

    try:
        amount = float(remainder)
    except ValueError:
        return "", currency, "price_unparseable"

    if amount < 0:
        return "", currency, "price_negative"
    return format(amount, "g"), currency, ""


def parse_rating(value: Any) -> tuple[str, str]:
    """Validate a rating on the explicitly assumed 1–5 demonstration scale."""
    text = clean_text(value)
    if not text:
        return "", "rating_missing"
    try:
        rating = float(text)
    except ValueError:
        return "", "rating_unparseable"
    if not 1 <= rating <= 5:
        return "", "rating_out_of_range"
    return format(rating, "g"), ""


def parse_review_count(value: Any) -> tuple[str, str]:
    """Parse a non-negative integer; commas are treated as thousands separators."""
    text = clean_text(value)
    if not text:
        return "", "review_count_missing"
    compact = text.replace(",", "")
    if not re.fullmatch(r"\d+", compact):
        return "", "review_count_unparseable"
    return str(int(compact)), ""


def normalize_category(value: Any) -> str:
    original = clean_text(value)
    normalized = re.sub(r"\s+", " ", original).casefold()
    return CATEGORY_ALIASES.get(normalized, normalized)


def clean_records(
    records: list[dict[str, str]], input_columns: list[str]
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    """Clean records while retaining auditable duplicate and quarantine outputs."""
    cleaned: list[dict[str, str]] = []
    quarantined: list[dict[str, str]] = []
    duplicates: list[dict[str, str]] = []
    seen: set[tuple[str, ...]] = set()
    issue_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()

    for row_number, source in enumerate(records, start=2):
        row = {
            column: "" if source.get(column) is None else str(source.get(column, ""))
            for column in input_columns
        }
        signature = tuple(row.get(column, "") for column in input_columns)
        if signature in seen:
            duplicate = dict(row)
            duplicate["pipeline_row_number"] = str(row_number)
            duplicate["duplicate_reason"] = "exact_duplicate"
            duplicates.append(duplicate)
            issue_counts["exact_duplicate_removed"] += 1
            continue
        seen.add(signature)

        record_id = clean_text(row.get("source_record_id"))
        product_name_raw = row.get("product_name", "")
        product_name = clean_text(product_name_raw)
        row["product_name_raw"] = product_name_raw
        row["product_name"] = product_name

        missing_identity = []
        if not record_id:
            missing_identity.append("missing_source_record_id")
        if not product_name:
            missing_identity.append("missing_product_name")
        if missing_identity:
            row["pipeline_row_number"] = str(row_number)
            row["quarantine_reason"] = ";".join(missing_identity)
            quarantined.append(row)
            for reason in missing_identity:
                issue_counts[reason] += 1
            continue

        category_raw = row.get("category", "")
        row["category_raw"] = category_raw
        row["category"] = normalize_category(category_raw)
        category_counts[row["category"] or "(missing)"] += 1

        ingredients_raw = row.get("ingredients_text", "")
        row["ingredients_raw"] = ingredients_raw
        ingredients_missing = not bool(clean_text(ingredients_raw))
        row["ingredients_missing"] = str(ingredients_missing).lower()
        if ingredients_missing:
            issue_counts["ingredients_missing"] += 1

        size_value, size_unit, size_issue = parse_size(row.get("size", ""))
        row["size_value"] = size_value
        row["size_unit_normalized"] = size_unit
        row["size_issue"] = size_issue
        if size_issue:
            issue_counts[size_issue] += 1

        price_value, currency, price_issue = parse_price(row.get("price", ""))
        row["price_value"] = price_value
        row["currency"] = currency
        row["price_issue"] = price_issue
        if price_issue:
            issue_counts[price_issue] += 1

        rating, rating_issue = parse_rating(row.get("rating", ""))
        row["rating_value"] = rating
        row["rating_issue"] = rating_issue
        if rating_issue:
            issue_counts[rating_issue] += 1

        review_count, count_issue = parse_review_count(row.get("review_count", ""))
        row["review_count_value"] = review_count
        row["review_count_issue"] = count_issue
        if count_issue:
            issue_counts[count_issue] += 1

        row["pipeline_row_number"] = str(row_number)
        cleaned.append(row)

    raw_count = len(records)
    report = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input_rows": raw_count,
        "exact_duplicates_removed": len(duplicates),
        "quarantined_rows": len(quarantined),
        "cleaned_rows": len(cleaned),
        "row_reconciliation_passed": (
            raw_count == len(duplicates) + len(quarantined) + len(cleaned)
        ),
        "issue_counts": dict(sorted(issue_counts.items())),
        "category_counts_after_cleaning": dict(sorted(category_counts.items())),
        "missing_ingredient_rate": (
            sum(row["ingredients_missing"] == "true" for row in cleaned)
            / len(cleaned)
            if cleaned
            else 0.0
        ),
        "rating_missing_or_invalid_rate": (
            sum(bool(row["rating_issue"]) for row in cleaned) / len(cleaned)
            if cleaned
            else 0.0
        ),
        "assumptions": [
            "Rating validation assumes the source scale is 1 through 5.",
            "Review-count commas are thousands separators.",
            "Size conversion is not performed between mass and volume.",
            "Unmapped category labels are retained after whitespace/case normalization.",
            "Prices without a currency marker retain an empty currency field.",
            "Synthetic demonstration records are invented, not real observations.",
        ],
    }
    return cleaned, quarantined, duplicates, report


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    """Write dictionaries to CSV, including a header for an empty output."""
    if rows:
        fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    else:
        fieldnames = ["pipeline_row_number", "reason"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Read a UTF-8 CSV and fail clearly for missing headers or required fields."""
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("Input CSV is empty or has no header row.")
        columns = [name.strip() for name in reader.fieldnames if name is not None]
        missing = sorted(set(REQUIRED_COLUMNS) - set(columns))
        if missing:
            raise ValueError(
                "Input CSV is missing required columns: " + ", ".join(missing)
            )
        records = []
        for row in reader:
            normalized_row = {
                (key.strip() if key else ""): (value or "")
                for key, value in row.items()
                if key is not None
            }
            records.append(normalized_row)
        return records, columns


def validate_outputs(
    cleaned: list[dict[str, str]], report: dict[str, Any]
) -> None:
    """Raise an error if core output constraints or row accounting fail."""
    if not report["row_reconciliation_passed"]:
        raise ValueError("Row accounting failed: input rows do not reconcile.")
    ids = [row["source_record_id"] for row in cleaned]
    if any(not record_id for record_id in ids):
        raise ValueError("A cleaned row has a missing source_record_id.")
    if any(not row["product_name"] for row in cleaned):
        raise ValueError("A cleaned row has a missing product_name.")
    for row in cleaned:
        if row["rating_value"]:
            rating = float(row["rating_value"])
            if not 1 <= rating <= 5:
                raise ValueError("A cleaned rating is outside the configured 1–5 scale.")
        if row["review_count_value"] and not row["review_count_value"].isdigit():
            raise ValueError("A cleaned review count is not a non-negative integer.")


def run_pipeline(input_path: Path | None, output_dir: Path, use_demo: bool) -> dict[str, Any]:
    """Run the pipeline and write all deliverables to the requested directory."""
    if use_demo:
        records = [dict(row) for row in DEMO_ROWS]
        columns = list(REQUIRED_COLUMNS)
        source_label = "built-in synthetic demonstration"
    else:
        if input_path is None:
            raise ValueError("Provide an input CSV path, or select --demo.")
        records, columns = load_csv(input_path)
        source_label = str(input_path.resolve())

    cleaned, quarantined, duplicates, report = clean_records(records, columns)
    report["source"] = source_label
    validate_outputs(cleaned, report)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "cleaned_products.csv", cleaned)
    write_csv(output_dir / "quarantined_rows.csv", quarantined)
    write_csv(output_dir / "removed_duplicates.csv", duplicates)
    with (output_dir / "quality_report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Clean beauty/wellness product data from CSV or a synthetic demo."
    )
    parser.add_argument(
        "input_csv",
        nargs="?",
        type=Path,
        help="CSV file with the required columns (not needed with --demo).",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the built-in synthetic example; no input file is required.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("beauty_wellness_output"),
        help="Directory for cleaned CSV, quarantine, duplicates, and report.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.demo and args.input_csv is not None:
        print("Error: choose either --demo or an input CSV, not both.", file=sys.stderr)
        return 2
    try:
        report = run_pipeline(args.input_csv, args.output_dir, args.demo)
    except (OSError, csv.Error, UnicodeError, ValueError) as error:
        print(f"Pipeline failed: {error}", file=sys.stderr)
        return 1

    print("Pipeline completed successfully.")
    print(f"Input rows: {report['input_rows']}")
    print(f"Exact duplicates removed: {report['exact_duplicates_removed']}")
    print(f"Quarantined rows: {report['quarantined_rows']}")
    print(f"Cleaned rows: {report['cleaned_rows']}")
    print(f"Outputs: {args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
