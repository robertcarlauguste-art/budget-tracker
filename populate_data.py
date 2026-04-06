#!/usr/bin/env python3
"""
populate_data.py — Fill an existing 50/30/20 Budget Tracker spreadsheet
with sample data, formulas, and cell formatting (colors, fonts, number
formats, column widths, merges, conditional formatting).

Does NOT create sheets, add named ranges, or add charts.
Run build_budget_tracker.py --spreadsheet-id <ID> afterward to add those.

Usage:
    python3 populate_data.py --creds credentials.json
    python3 populate_data.py --creds credentials.json --spreadsheet-id OTHER_ID
    GOOGLE_APPLICATION_CREDENTIALS=sa.json python3 populate_data.py
"""

import argparse
import os
import sys

# ── Reuse all helpers from the main builder ───────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_budget_tracker as bbt   # noqa: E402  (path manipulation above)

DEFAULT_ID = "1QfG01iiyJDEZBZ4_GIt27H4e42XW8CufxsAA-rk2s8k"


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--creds",
                        help="Path to OAuth2 client_secrets JSON")
    parser.add_argument("--token", default="token.json",
                        help="Saved OAuth token file (default: token.json)")
    parser.add_argument("--spreadsheet-id",
                        default=DEFAULT_ID,
                        metavar="ID",
                        help=f"Target spreadsheet (default: {DEFAULT_ID})")
    args = parser.parse_args()

    service = bbt.get_service(creds_file=args.creds, token_file=args.token)
    sid = args.spreadsheet_id
    url = f"https://docs.google.com/spreadsheets/d/{sid}/edit"

    print(f"📝 Populating data in existing spreadsheet …")
    print(f"   {url}\n")

    requests = []

    print("  [1/4] Reference tab  — category→bucket lookup, month list …")
    requests.extend(bbt.build_reference_requests())

    print("  [2/4] Expense Log    — 50 sample rows, Bucket/Month formulas, "
          "column widths, conditional formatting …")
    requests.extend(bbt.build_log_requests())

    print("  [3/4] Budget Setup   — income targets, 50/30/20 ratios, "
          "12-month SUMIFS table …")
    requests.extend(bbt.build_setup_requests())

    print("  [4/4] Dashboard      — title banner, income summary, bucket "
          "cards, progress bars, top-spending QUERY, chart helper data …")
    requests.extend(bbt.build_dashboard_requests())

    total = len(requests)
    print(f"\n  Sending {total} API requests …")
    bbt.batch_update(service, sid, requests)

    print(f"\n✅  Done!  Open your tracker:")
    print(f"   {url}")
    print()
    print("   Next step — add named ranges, validation, and charts:")
    print(f"   python3 build_budget_tracker.py --creds credentials.json "
          f"--spreadsheet-id {sid}")


if __name__ == "__main__":
    main()
