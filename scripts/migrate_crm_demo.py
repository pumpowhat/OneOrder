"""Convert a local Dataverse Account export to Salesforce CSV.

Run: python -m scripts.migrate_crm_demo samples/crm-migration/dynamics-accounts.json /tmp/salesforce-accounts.csv
"""

import argparse
import csv
import json
from pathlib import Path
from unicodedata import normalize

from backend.services.orders.phone import normalize_phone


FIELD_MAP = {
    "name": "Name",
    "telephone1": "Phone",
    "address1_line1": "BillingStreet",
    "address1_city": "BillingCity",
    "address1_country": "BillingCountry",
}


def convert(rows: list[object]) -> tuple[list[dict[str, str]], int, int]:
    accounts = []
    seen = {}
    merged = errors = 0

    for row in rows:
        if not isinstance(row, dict) or any(
            row.get(field) is not None and not isinstance(row[field], str)
            for field in FIELD_MAP
        ):
            errors += 1
            continue

        account = {
            target: (row.get(source) or "").strip()
            for source, target in FIELD_MAP.items()
        }
        if not account["Name"]:
            errors += 1
            continue
        if not account["Phone"]:
            accounts.append(account)
            continue
        try:
            account["Phone"] = normalize_phone(account["Phone"])
        except ValueError:
            errors += 1
            continue

        name = " ".join(normalize("NFKC", account["Name"]).casefold().split())
        key = (name, account["Phone"])
        previous = seen.get(key)
        if previous is None:
            seen[key] = account
            accounts.append(account)
        else:
            merged += 1
            for field, value in account.items():
                if not previous[field]:
                    previous[field] = value

    return accounts, merged, errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.destination.resolve():
        parser.error("source and destination must be different files")

    try:
        document = json.loads(args.source.read_text(encoding="utf-8-sig"))
        rows = document.get("value") if isinstance(document, dict) else document
        if not isinstance(rows, list):
            parser.error("expected a JSON array or a Dataverse object with a value array")
        accounts, merged, errors = convert(rows)
        with args.destination.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=list(FIELD_MAP.values()))
            writer.writeheader()
            writer.writerows(accounts)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    print(f"Read {len(rows)} | Exported {len(accounts)} | Duplicates merged {merged} | Invalid records {errors}")


if __name__ == "__main__":
    main()
