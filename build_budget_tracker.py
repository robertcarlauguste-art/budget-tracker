#!/usr/bin/env python3
"""
50/30/20 Monthly Budget Tracker — Google Sheets Builder
Requires: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

Usage:
  python3 build_budget_tracker.py --creds path/to/credentials.json
  python3 build_budget_tracker.py --token path/to/token.json
  GOOGLE_APPLICATION_CREDENTIALS=path/to/sa.json python3 build_budget_tracker.py
"""

import argparse
import json
import os
import sys

# ─── Auth ────────────────────────────────────────────────────────────────────

def get_service(creds_file=None, token_file=None):
    """Return an authenticated Google Sheets service object."""
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        from googleapiclient.discovery import build
        import google.auth
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
    except ImportError:
        sys.exit("Missing deps. Run: pip install -r requirements.txt")

    creds = None
    if token_file and os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif creds_file:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
            if token_file:
                with open(token_file, "w") as f:
                    f.write(creds.to_json())
        else:
            try:
                creds, _ = google.auth.default(scopes=SCOPES)
            except Exception as e:
                sys.exit(f"No credentials found: {e}\nRun with --creds path/to/credentials.json")
    return build("sheets", "v4", credentials=creds)


# ─── Color helpers ───────────────────────────────────────────────────────────

def hex_to_rgb(h):
    """Convert '#RRGGBB' to Sheets API color dict {red, green, blue}."""
    h = h.lstrip("#")
    return {
        "red":   int(h[0:2], 16) / 255,
        "green": int(h[2:4], 16) / 255,
        "blue":  int(h[4:6], 16) / 255,
    }

# Palette
C = {
    "darkGreen":    "#1B4332",
    "medGreen":     "#2D6A4F",
    "emerald":      "#40916C",
    "gold":         "#D4A017",
    "rose":         "#B5838D",
    "mintBg":       "#D8F3DC",
    "coralBg":      "#FFDDD2",
    "paleGreen":    "#F0F7F4",
    "amberInput":   "#FFF8E1",
    "nearBlack":    "#081C15",
    "softGold":     "#E9C46A",
    "wantsBg":      "#FFF3CD",
    "savingsBg":    "#F5E6EA",
    "white":        "#FFFFFF",
    "black":        "#000000",
}


def color(key):
    return hex_to_rgb(C[key])


# ─── Format helpers ───────────────────────────────────────────────────────────

def cell_fmt(bg=None, fg=None, bold=False, italic=False, size=None,
             font="Arial", h_align=None, v_align="MIDDLE",
             number_format=None, wrap=None, borders=None):
    fmt = {
        "textFormat": {
            "fontFamily": font,
            "bold": bold,
            "italic": italic,
        }
    }
    if size:
        fmt["textFormat"]["fontSize"] = size
    if fg:
        fmt["textFormat"]["foregroundColor"] = hex_to_rgb(fg)
    if bg:
        fmt["backgroundColor"] = hex_to_rgb(bg)
    if h_align:
        fmt["horizontalAlignment"] = h_align
    if v_align:
        fmt["verticalAlignment"] = v_align
    if number_format:
        fmt["numberFormat"] = number_format
    if wrap:
        fmt["wrapStrategy"] = wrap
    if borders:
        fmt["borders"] = borders
    return fmt


MONEY_FMT   = {"type": "CURRENCY", "pattern": '$#,##0.00'}
PCT_FMT     = {"type": "NUMBER",   "pattern": '0%'}
DATE_FMT    = {"type": "DATE",     "pattern": 'MM/DD/YYYY'}


def range_a1(sheet_id, r1, c1, r2, c2):
    """GridRange dict (0-indexed)."""
    return {"sheetId": sheet_id,
            "startRowIndex": r1, "endRowIndex": r2,
            "startColumnIndex": c1, "endColumnIndex": c2}


def update_cells_req(sheet_id, row, col, rows_data):
    """
    rows_data: list of lists of CellData dicts.
    Returns an UpdateCells request.
    """
    return {
        "updateCells": {
            "rows": [
                {"values": row_vals}
                for row_vals in rows_data
            ],
            "fields": "userEnteredValue,userEnteredFormat",
            "start": {"sheetId": sheet_id, "rowIndex": row, "columnIndex": col},
        }
    }


def date_serial(date_str):
    """Convert 'MM/DD/YYYY' to Google Sheets date serial number."""
    from datetime import date
    m, d, y = date_str.split("/")
    dt = date(int(y), int(m), int(d))
    base = date(1899, 12, 30)
    return (dt - base).days


def cell(value=None, formula=None, fmt=None, note=None, is_date=False):
    """Build a CellData dict."""
    cd = {}
    if formula is not None:
        cd["userEnteredValue"] = {"formulaValue": formula}
    elif value is not None:
        if is_date and isinstance(value, str):
            cd["userEnteredValue"] = {"numberValue": date_serial(value)}
        elif isinstance(value, (int, float)):
            cd["userEnteredValue"] = {"numberValue": value}
        elif isinstance(value, bool):
            cd["userEnteredValue"] = {"boolValue": value}
        else:
            cd["userEnteredValue"] = {"stringValue": str(value)}
    if fmt:
        cd["userEnteredFormat"] = fmt
    if note:
        cd["note"] = note
    return cd


def blank(fmt=None):
    return cell(value="", fmt=fmt)


def merge_req(sheet_id, r1, c1, r2, c2, merge_type="MERGE_ALL"):
    return {"mergeCells": {"range": range_a1(sheet_id, r1, c1, r2, c2),
                           "mergeType": merge_type}}


def freeze_req(sheet_id, rows=0, cols=0):
    return {
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {"frozenRowCount": rows, "frozenColumnCount": cols},
            },
            "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
        }
    }


def col_width_req(sheet_id, col_idx, width_px):
    return {
        "updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS",
                      "startIndex": col_idx, "endIndex": col_idx + 1},
            "properties": {"pixelSize": width_px},
            "fields": "pixelSize",
        }
    }


def row_height_req(sheet_id, row_idx, height_px):
    return {
        "updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "ROWS",
                      "startIndex": row_idx, "endIndex": row_idx + 1},
            "properties": {"pixelSize": height_px},
            "fields": "pixelSize",
        }
    }


def hide_sheet_req(sheet_id):
    return {
        "updateSheetProperties": {
            "properties": {"sheetId": sheet_id, "hidden": True},
            "fields": "hidden",
        }
    }


def named_range_req(name, sheet_id, r1, c1, r2, c2):
    return {
        "addNamedRange": {
            "namedRange": {
                "name": name,
                "range": range_a1(sheet_id, r1, c1, r2, c2),
            }
        }
    }


def cond_fmt_req(sheet_id, r1, c1, r2, c2, condition_type, values, bg_color):
    return {
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [range_a1(sheet_id, r1, c1, r2, c2)],
                "booleanRule": {
                    "condition": {"type": condition_type, "values": values},
                    "format": {"backgroundColor": hex_to_rgb(bg_color)},
                },
            },
            "index": 0,
        }
    }


def cond_fmt_formula_req(sheet_id, r1, c1, r2, c2, formula, bg_color):
    return {
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [range_a1(sheet_id, r1, c1, r2, c2)],
                "booleanRule": {
                    "condition": {"type": "CUSTOM_FORMULA",
                                  "values": [{"userEnteredValue": formula}]},
                    "format": {"backgroundColor": hex_to_rgb(bg_color)},
                },
            },
            "index": 0,
        }
    }


def data_validation_req(sheet_id, r1, c1, r2, c2, values=None,
                        range_source=None, strict=True):
    if range_source:
        # Sheets API requires ONE_OF_RANGE values to start with "="
        src = range_source if range_source.startswith("=") else f"={range_source}"
        condition = {"type": "ONE_OF_RANGE",
                     "values": [{"userEnteredValue": src}]}
    else:
        condition = {"type": "ONE_OF_LIST",
                     "values": [{"userEnteredValue": v} for v in values]}
    return {
        "setDataValidation": {
            "range": range_a1(sheet_id, r1, c1, r2, c2),
            "rule": {
                "condition": condition,
                "showCustomUi": True,
                "strict": strict,
            },
        }
    }


# ─── Sheet IDs ───────────────────────────────────────────────────────────────

SID = {
    "dashboard":  0,
    "log":        1,
    "setup":      2,
    "reference":  3,
}


# ─── Reference tab ───────────────────────────────────────────────────────────

CATEGORIES = [
    ("Rent / Mortgage",       "Needs"),
    ("Utilities",             "Needs"),
    ("Groceries",             "Needs"),
    ("Transportation",        "Needs"),
    ("Insurance",             "Needs"),
    ("Healthcare",            "Needs"),
    ("Phone",                 "Needs"),
    ("Internet",              "Needs"),
    ("Childcare",             "Needs"),
    ("Minimum Debt Payments", "Needs"),
    ("Dining Out",            "Wants"),
    ("Entertainment",         "Wants"),
    ("Shopping",              "Wants"),
    ("Subscriptions",         "Wants"),
    ("Personal Care",         "Wants"),
    ("Gym / Fitness",         "Wants"),
    ("Travel",                "Wants"),
    ("Gifts",                 "Wants"),
    ("Hobbies",               "Wants"),
    ("Coffee / Drinks",       "Wants"),
    ("Emergency Fund",        "Savings & Debt"),
    ("Retirement / 401k",     "Savings & Debt"),
    ("Extra Debt Payment",    "Savings & Debt"),
    ("Investments",           "Savings & Debt"),
    ("Sinking Funds",         "Savings & Debt"),
    ("Freelance / Gig Work",  "Side Income Tracking"),
    ("Online Sales",          "Side Income Tracking"),
]

MONTHS_2026 = [f"2026-{m:02d}" for m in range(1, 13)]

hdr_cat_fmt = cell_fmt(bg=C["darkGreen"], fg=C["white"], bold=True)
hdr_mnth_fmt = cell_fmt(bg=C["medGreen"], fg=C["white"], bold=True)


def build_reference_requests():
    reqs = []
    sid = SID["reference"]

    # Headers row 0
    rows = [[
        cell("Category", fmt=hdr_cat_fmt),
        cell("Bucket",   fmt=hdr_cat_fmt),
        cell("",         fmt=hdr_cat_fmt),
        cell("Month",    fmt=hdr_mnth_fmt),
    ]]
    # Data rows
    for i, (cat, bucket) in enumerate(CATEGORIES):
        row_bg = C["paleGreen"] if i % 2 == 0 else C["white"]
        month_val = MONTHS_2026[i] if i < len(MONTHS_2026) else ""
        rows.append([
            cell(cat,    fmt=cell_fmt(bg=row_bg)),
            cell(bucket, fmt=cell_fmt(bg=row_bg)),
            cell("",     fmt=cell_fmt(bg=row_bg)),
            cell(month_val, fmt=cell_fmt(bg=C["paleGreen"] if i % 2 == 0 else C["white"])),
        ])
    reqs.append(update_cells_req(sid, 0, 0, rows))

    # Column widths
    reqs.append(col_width_req(sid, 0, 180))
    reqs.append(col_width_req(sid, 1, 150))
    reqs.append(col_width_req(sid, 3, 90))
    # Hide
    reqs.append(hide_sheet_req(sid))
    return reqs


# ─── Expense Log tab ─────────────────────────────────────────────────────────

SAMPLE_DATA = [
    # date, description, category, amount, type
    ("01/01/2026","Paycheck",         "Income",                2600, "Income"),
    ("01/15/2026","Paycheck",         "Income",                2600, "Income"),
    ("01/10/2026","Etsy Sales",       "Side Income",            120, "Side Income"),
    ("01/22/2026","Freelance Design", "Side Income",            250, "Side Income"),
    ("01/02/2026","Rent",             "Rent / Mortgage",       1500, "Expense"),
    ("01/04/2026","Electric Bill",    "Utilities",               85, "Expense"),
    ("01/05/2026","Whole Foods",      "Groceries",              210, "Expense"),
    ("01/06/2026","Spotify",          "Subscriptions",           11, "Expense"),
    ("01/07/2026","Netflix",          "Subscriptions",           16, "Expense"),
    ("01/08/2026","Planet Fitness",   "Gym / Fitness",           25, "Expense"),
    ("01/10/2026","Chipotle",         "Dining Out",              18, "Expense"),
    ("01/12/2026","T-Mobile",         "Phone",                   55, "Expense"),
    ("01/14/2026","Target",           "Shopping",                94, "Expense"),
    ("01/16/2026","Roth IRA",         "Retirement / 401k",      500, "Expense"),
    ("01/18/2026","Car Insurance",    "Insurance",              120, "Expense"),
    ("01/20/2026","Starbucks",        "Coffee / Drinks",         47, "Expense"),
    ("01/22/2026","Extra Car Payment","Extra Debt Payment",     200, "Expense"),
    ("01/25/2026","Movie Tickets",    "Entertainment",           35, "Expense"),
    ("01/28/2026","Internet",         "Internet",                60, "Expense"),
    # February
    ("02/01/2026","Paycheck",         "Income",                2600, "Income"),
    ("02/15/2026","Paycheck",         "Income",                2600, "Income"),
    ("02/08/2026","Tutoring Session", "Side Income",            180, "Side Income"),
    ("02/20/2026","Etsy Sales",       "Side Income",             95, "Side Income"),
    ("02/02/2026","Rent",             "Rent / Mortgage",       1500, "Expense"),
    ("02/03/2026","Whole Foods",      "Groceries",              185, "Expense"),
    ("02/05/2026","Gas",              "Transportation",          62, "Expense"),
    ("02/07/2026","Amazon",           "Shopping",               134, "Expense"),
    ("02/09/2026","Doctor Copay",     "Healthcare",              40, "Expense"),
    ("02/11/2026","Dinner Out",       "Dining Out",              72, "Expense"),
    ("02/13/2026","Valentines Gift",  "Gifts",                   65, "Expense"),
    ("02/15/2026","Electric Bill",    "Utilities",               91, "Expense"),
    ("02/18/2026","Roth IRA",         "Retirement / 401k",      500, "Expense"),
    ("02/20/2026","Sinking Fund",     "Sinking Funds",          150, "Expense"),
    ("02/22/2026","T-Mobile",         "Phone",                   55, "Expense"),
    ("02/25/2026","Hulu",             "Subscriptions",           18, "Expense"),
    # March
    ("03/01/2026","Paycheck",         "Income",                2600, "Income"),
    ("03/15/2026","Paycheck",         "Income",                2600, "Income"),
    ("03/20/2026","Bonus",            "Income",                 500, "Income"),
    ("03/05/2026","Freelance Writing","Side Income",            320, "Side Income"),
    ("03/18/2026","eBay Sales",       "Side Income",            145, "Side Income"),
    ("03/02/2026","Rent",             "Rent / Mortgage",       1500, "Expense"),
    ("03/04/2026","Whole Foods",      "Groceries",              220, "Expense"),
    ("03/06/2026","Gas",              "Transportation",          55, "Expense"),
    ("03/10/2026","Clothing",         "Shopping",               180, "Expense"),
    ("03/12/2026","Concert Tickets",  "Entertainment",           95, "Expense"),
    ("03/15/2026","T-Mobile",         "Phone",                   55, "Expense"),
    ("03/18/2026","Roth IRA",         "Retirement / 401k",      500, "Expense"),
    ("03/20/2026","Emergency Fund",   "Emergency Fund",         300, "Expense"),
    ("03/22/2026","Sushi Dinner",     "Dining Out",              88, "Expense"),
    ("03/25/2026","Internet",         "Internet",                60, "Expense"),
]


def build_log_requests():
    reqs = []
    sid = SID["log"]

    # ── Headers (row 0) ──────────────────────────────────────────────────────
    hdr_fmt = cell_fmt(bg=C["darkGreen"], fg=C["white"], bold=True, size=11)
    headers = ["Date", "Description", "Category", "Amount", "Type", "Bucket", "Month"]
    reqs.append(update_cells_req(sid, 0, 0, [[
        cell(h, fmt=hdr_fmt) for h in headers
    ]]))

    # ── Sample data rows ──────────────────────────────────────────────────────
    data_rows = []
    for i, (date, desc, cat, amt, typ) in enumerate(SAMPLE_DATA):
        row_num = i + 2  # 1-indexed, row 1 is header
        row_bg = C["paleGreen"] if i % 2 == 0 else C["white"]
        type_bg = C["amberInput"] if typ == "Side Income" else row_bg

        bucket_formula = f'=IFERROR(VLOOKUP(C{row_num},Reference!$A:$B,2,FALSE),"")'
        month_formula  = f'=IF(A{row_num}="","",TEXT(A{row_num},"YYYY-MM"))'

        # Determine if date is a real date string — store as string for now
        data_rows.append([
            cell(date, fmt=cell_fmt(bg=row_bg, number_format=DATE_FMT), is_date=True),
            cell(desc, fmt=cell_fmt(bg=row_bg)),
            cell(cat,  fmt=cell_fmt(bg=row_bg)),
            cell(amt,  fmt=cell_fmt(bg=row_bg, number_format=MONEY_FMT)),
            cell(typ,  fmt=cell_fmt(bg=type_bg)),
            cell(formula=bucket_formula,
                 fmt=cell_fmt(bg=row_bg)),
            cell(formula=month_formula,
                 fmt=cell_fmt(bg=row_bg)),
        ])
    reqs.append(update_cells_req(sid, 1, 0, data_rows))

    # ── Freeze row 1, col A ───────────────────────────────────────────────────
    reqs.append(freeze_req(sid, rows=1, cols=1))

    # ── Column widths ─────────────────────────────────────────────────────────
    for col, w in enumerate([110, 200, 180, 110, 120, 150, 90]):
        reqs.append(col_width_req(sid, col, w))

    # ── Data Validation: Category (C2:C1000) ──────────────────────────────────
    reqs.append(data_validation_req(sid, 1, 2, 1000, 3,
                                    range_source="Reference!$A$2:$A$28"))

    # ── Data Validation: Type (E2:E1000) ──────────────────────────────────────
    reqs.append(data_validation_req(sid, 1, 4, 1000, 5,
                                    values=["Income", "Side Income", "Expense"]))

    # ── Conditional formatting: Bucket column F ───────────────────────────────
    for val, bg in [("Needs", C["mintBg"]),
                    ("Wants", C["wantsBg"]),
                    ("Savings & Debt", C["savingsBg"])]:
        reqs.append(cond_fmt_req(sid, 1, 5, 1000, 6,
                                 "TEXT_EQ", [{"userEnteredValue": val}], bg))

    # ── Conditional formatting: Side Income type ──────────────────────────────
    reqs.append(cond_fmt_req(sid, 1, 4, 1000, 5,
                             "TEXT_EQ", [{"userEnteredValue": "Side Income"}],
                             C["amberInput"]))

    return reqs


# ─── Budget Setup tab ────────────────────────────────────────────────────────

def build_setup_requests():
    reqs = []
    sid = SID["setup"]

    title_fmt    = cell_fmt(bg=C["nearBlack"], fg=C["white"], bold=True, size=14, h_align="CENTER")
    section_fmt  = cell_fmt(bg=C["darkGreen"], fg=C["white"], bold=True, size=11)
    label_fmt    = cell_fmt(bold=True)
    label_i_fmt  = cell_fmt(bold=True, italic=True)
    input_fmt    = cell_fmt(bg=C["amberInput"], number_format=MONEY_FMT)
    pct_input    = cell_fmt(bg=C["amberInput"], number_format=PCT_FMT)
    sum_fmt      = cell_fmt(bg=C["paleGreen"], number_format=MONEY_FMT, italic=True, bold=True)
    pct_sum_fmt  = cell_fmt(bg=C["paleGreen"], number_format=PCT_FMT)
    tbl_hdr_fmt  = cell_fmt(bg=C["darkGreen"], fg=C["white"], bold=True)
    money_fmt    = cell_fmt(number_format=MONEY_FMT)
    even_fmt     = cell_fmt(bg=C["paleGreen"], number_format=MONEY_FMT)

    # Row 0: Title merged A1:F1
    reqs.append(update_cells_req(sid, 0, 0, [[
        cell("⚙️ Budget Setup", fmt=title_fmt),
        blank(fmt=title_fmt), blank(fmt=title_fmt),
        blank(fmt=title_fmt), blank(fmt=title_fmt), blank(fmt=title_fmt),
    ]]))
    reqs.append(merge_req(sid, 0, 0, 1, 6))
    reqs.append(row_height_req(sid, 0, 40))

    # Row 1: blank spacer
    # Row 2 (idx): Base Income Target
    reqs.append(update_cells_req(sid, 2, 1, [[
        cell("Monthly Base Income Target", fmt=label_fmt),
        cell(5000, fmt=input_fmt),
    ]]))

    # Row 3: Side Income Target (with gold left border)
    gold_border = {"left": {"style": "SOLID_MEDIUM",
                            "color": hex_to_rgb(C["softGold"])}}
    reqs.append(update_cells_req(sid, 3, 1, [[
        cell("Monthly Side Income Target", fmt=label_fmt),
        cell(500,  fmt=cell_fmt(bg=C["amberInput"], number_format=MONEY_FMT,
                                borders=gold_border)),
    ]]))

    # Row 4: Combined Income Target (formula)
    reqs.append(update_cells_req(sid, 4, 1, [[
        cell("Combined Income Target", fmt=label_i_fmt),
        cell(formula="=C3+C4", fmt=sum_fmt),
    ]]))

    # Row 6: Needs %
    reqs.append(update_cells_req(sid, 6, 1, [[
        cell("Needs % Target", fmt=label_fmt),
        cell(0.50, fmt=pct_input),
    ]]))
    # Row 7: Wants %
    reqs.append(update_cells_req(sid, 7, 1, [[
        cell("Wants % Target", fmt=label_fmt),
        cell(0.30, fmt=pct_input),
    ]]))
    # Row 8: Savings %
    reqs.append(update_cells_req(sid, 8, 1, [[
        cell("Savings & Debt % Target", fmt=label_fmt),
        cell(0.20, fmt=pct_input),
    ]]))

    # Row 10: Ratio check
    reqs.append(update_cells_req(sid, 10, 1, [[
        cell("⚠️ Ratio Total Check", fmt=cell_fmt(bold=True)),
        cell(formula="=C7+C8+C9", fmt=pct_sum_fmt),
    ]]))

    # Conditional: C11 != 1 → coral
    reqs.append(cond_fmt_formula_req(sid, 10, 2, 11, 3, "=C11<>1", C["coralBg"]))

    # Data Validation: C7:C9 NUMBER_BETWEEN 0 and 1
    reqs.append({
        "setDataValidation": {
            "range": range_a1(sid, 6, 2, 9, 3),
            "rule": {
                "condition": {
                    "type": "NUMBER_BETWEEN",
                    "values": [{"userEnteredValue": "0"},
                               {"userEnteredValue": "1"}],
                },
                "showCustomUi": True,
                "strict": False,
            },
        }
    })

    # Row 12: Section label
    reqs.append(update_cells_req(sid, 12, 1, [[
        cell("📅 Actual Monthly Income by Month", fmt=cell_fmt(bold=True)),
    ]]))

    # Row 13: Table headers
    reqs.append(update_cells_req(sid, 13, 1, [[
        cell("Month",       fmt=tbl_hdr_fmt),
        cell("Base Income", fmt=tbl_hdr_fmt),
        cell("Side Income", fmt=tbl_hdr_fmt),
        cell("Total",       fmt=tbl_hdr_fmt),
    ]]))

    # Rows 14–25: one row per month 2026-01 → 2026-12
    month_rows = []
    for i, month in enumerate(MONTHS_2026):
        row_num = 15 + i   # 1-indexed: data starts at row 15 (headers at row 14)
        bg = C["paleGreen"] if i % 2 == 0 else C["white"]
        base_f = (f"=IFERROR(SUMIFS('Expense Log'!D:D,"
                  f"'Expense Log'!E:E,\"Income\","
                  f"'Expense Log'!G:G,B{row_num}),0)")
        side_f = (f"=IFERROR(SUMIFS('Expense Log'!D:D,"
                  f"'Expense Log'!E:E,\"Side Income\","
                  f"'Expense Log'!G:G,B{row_num}),0)")
        total_f = f"=C{row_num}+D{row_num}"
        month_rows.append([
            cell(month,              fmt=cell_fmt(bg=bg)),
            cell(formula=base_f,     fmt=cell_fmt(bg=bg, number_format=MONEY_FMT)),
            cell(formula=side_f,     fmt=cell_fmt(bg=bg, number_format=MONEY_FMT)),
            cell(formula=total_f,    fmt=cell_fmt(bg=bg, number_format=MONEY_FMT, bold=True)),
        ])
    reqs.append(update_cells_req(sid, 14, 1, month_rows))

    # Freeze rows 1-3
    reqs.append(freeze_req(sid, rows=3, cols=0))

    # Named ranges (absolute references — created after spreadsheet exists)
    # We'll pass sheet_id and cell positions — handled in named_ranges section

    # Column widths
    for col, w in enumerate([20, 220, 140, 140, 120]):
        reqs.append(col_width_req(sid, col, w))

    return reqs


# ─── Dashboard tab ────────────────────────────────────────────────────────────

def build_dashboard_requests():
    reqs = []
    sid = SID["dashboard"]

    title_fmt   = cell_fmt(bg=C["nearBlack"], fg=C["white"], bold=True, size=16,
                           h_align="CENTER", v_align="MIDDLE")
    lbl_fmt     = cell_fmt(bold=True)
    amber_lbl   = cell_fmt(bg=C["amberInput"], bold=True)
    amber_val   = cell_fmt(bg=C["amberInput"], number_format=MONEY_FMT, bold=True)
    pale_val    = cell_fmt(bg=C["paleGreen"],  number_format=MONEY_FMT, bold=True)
    pale_lbl    = cell_fmt(bg=C["paleGreen"],  bold=True)
    money_bold  = cell_fmt(number_format=MONEY_FMT, bold=True)
    pct_fmt_c   = cell_fmt(number_format=PCT_FMT)
    sec_lbl_fmt = cell_fmt(bg=C["medGreen"], fg=C["white"], bold=True, size=11)

    # ── Row 0: Title banner A1:J1 ──────────────────────────────────────────
    reqs.append(update_cells_req(sid, 0, 0, [[
        cell("💰 50/30/20 Budget Dashboard", fmt=title_fmt),
        *[blank(fmt=title_fmt) for _ in range(9)],
    ]]))
    reqs.append(merge_req(sid, 0, 0, 1, 10))
    reqs.append(row_height_req(sid, 0, 50))

    # ── Row 1: Month Selector ─────────────────────────────────────────────
    reqs.append(update_cells_req(sid, 1, 1, [[
        cell("Select Month:", fmt=lbl_fmt),
        cell("2026-01", fmt=cell_fmt(bg=C["amberInput"])),
    ]]))

    # Data validation on C2 (row=1, col=2)
    reqs.append(data_validation_req(sid, 1, 2, 2, 3,
                                    range_source="Reference!$D$2:$D$13"))

    # ── Row 3: Income Summary labels ─────────────────────────────────────
    # A4:B4 merge "💵 Base Income", C4 value
    # D4:E4 merge "⚡ Side Income", F4 value
    # G4:H4 merge "💰 Total Income", I4 value
    label_rows_3 = [
        cell("💵 Base Income",    fmt=lbl_fmt),
        blank(fmt=lbl_fmt),
        cell(formula="=IFERROR(SUMIFS('Expense Log'!D:D,'Expense Log'!E:E,\"Income\",'Expense Log'!G:G,C2),0)",
             fmt=money_bold),
        cell("⚡ Side Income",    fmt=amber_lbl),
        blank(fmt=amber_lbl),
        cell(formula="=IFERROR(SUMIFS('Expense Log'!D:D,'Expense Log'!E:E,\"Side Income\",'Expense Log'!G:G,C2),0)",
             fmt=amber_val),
        cell("💰 Total Income",   fmt=pale_lbl),
        blank(fmt=pale_lbl),
        cell(formula="=C4+F4",    fmt=pale_val),
    ]
    reqs.append(update_cells_req(sid, 3, 0, [label_rows_3]))
    reqs.append(merge_req(sid, 3, 0, 4, 2))   # A4:B4
    reqs.append(merge_req(sid, 3, 3, 4, 5))   # D4:E4
    reqs.append(merge_req(sid, 3, 6, 4, 8))   # G4:H4

    # ── Row 4: Targets ────────────────────────────────────────────────────
    tgt_rows_4 = [
        cell("🎯 Base Target",     fmt=lbl_fmt),
        blank(fmt=lbl_fmt),
        cell(formula="='Budget Setup'!C3", fmt=cell_fmt(number_format=MONEY_FMT)),
        cell("🎯 Side Target",     fmt=lbl_fmt),
        blank(fmt=lbl_fmt),
        cell(formula="='Budget Setup'!C4", fmt=cell_fmt(number_format=MONEY_FMT)),
        cell("🎯 Combined Target", fmt=lbl_fmt),
        blank(fmt=lbl_fmt),
        cell(formula="='Budget Setup'!C5", fmt=cell_fmt(number_format=MONEY_FMT)),
    ]
    reqs.append(update_cells_req(sid, 4, 0, [tgt_rows_4]))
    reqs.append(merge_req(sid, 4, 0, 5, 2))
    reqs.append(merge_req(sid, 4, 3, 5, 5))
    reqs.append(merge_req(sid, 4, 6, 5, 8))

    # ── Row 5: % of Combined Target ───────────────────────────────────────
    pct_row = [
        cell("📊 % of Combined Target", fmt=cell_fmt(bold=True)),
        *[blank() for _ in range(7)],
        cell(formula="=IFERROR(I4/I5,0)",
             fmt=cell_fmt(number_format=PCT_FMT, bold=True)),
    ]
    reqs.append(update_cells_req(sid, 5, 0, [pct_row]))
    reqs.append(merge_req(sid, 5, 0, 6, 8))   # A6:H6
    reqs.append(cond_fmt_req(sid, 5, 8, 6, 9, "NUMBER_GREATER_THAN_EQ",
                             [{"userEnteredValue": "1"}], C["mintBg"]))
    reqs.append(cond_fmt_req(sid, 5, 8, 6, 9, "NUMBER_LESS",
                             [{"userEnteredValue": "0.8"}], C["coralBg"]))

    # ── Bucket Cards (rows 7–12) ──────────────────────────────────────────
    def bucket_card(start_col, header_text, hdr_bg, bucket_name, target_pct_cell):
        """
        Build 6 rows of card data starting at col `start_col`.
        Returns list-of-lists of CellData.
        """
        hdr_fmt_c = cell_fmt(bg=hdr_bg, fg=C["white"], bold=True, size=12,
                             h_align="CENTER")
        lbl_c   = cell_fmt(bold=True)
        val_c   = cell_fmt(number_format=MONEY_FMT)
        remain_green = cell_fmt(bg=C["mintBg"], number_format=MONEY_FMT, bold=True)
        remain_red   = cell_fmt(bg=C["coralBg"], number_format=MONEY_FMT, bold=True)
        pct_c   = cell_fmt(number_format=PCT_FMT)
        bar_c   = cell_fmt(font="Courier New",
                           fg=hdr_bg, bold=True)

        sc = start_col
        # row offsets within the card block (absolute row indices):
        # card header row = 7 (idx), data rows 8–12 (idx)
        return [
            # Row 7 (idx): header
            [cell(header_text, fmt=hdr_fmt_c),
             blank(fmt=hdr_fmt_c), blank(fmt=hdr_fmt_c)],
            # Row 8: Target Amount
            [cell("Target Amount", fmt=lbl_c),
             cell(formula=f"=ROUND('Budget Setup'!C5*'Budget Setup'!{target_pct_cell},2)",
                  fmt=val_c),
             blank()],
            # Row 9: Actual Spent
            [cell("Actual Spent", fmt=lbl_c),
             cell(formula=(f"=IFERROR(SUMIFS('Expense Log'!D:D,"
                           f"'Expense Log'!E:E,\"Expense\","
                           f"'Expense Log'!F:F,\"{bucket_name}\","
                           f"'Expense Log'!G:G,C2),0)"),
                  fmt=val_c),
             blank()],
            # Row 10: Remaining
            [cell("Remaining", fmt=lbl_c),
             cell(formula=f"=B9-B10" if sc == 0 else
                          (f"=F9-F10" if sc == 4 else f"=J9-J10"),
                  fmt=val_c),
             blank()],
            # Row 11: % Used
            [cell("% Used", fmt=lbl_c),
             cell(formula=f"=IFERROR(B10/B9,0)" if sc == 0 else
                          (f"=IFERROR(F10/F9,0)" if sc == 4 else f"=IFERROR(J10/J9,0)"),
                  fmt=pct_c),
             blank()],
            # Row 12: Progress bar
            [cell("Progress", fmt=lbl_c),
             cell(formula=(
                 f'=REPT("█",MIN(ROUND(B12*20),20))&REPT("░",MAX(20-ROUND(B12*20),0))'
                 if sc == 0 else
                 (f'=REPT("█",MIN(ROUND(F12*20),20))&REPT("░",MAX(20-ROUND(F12*20),0))'
                  if sc == 4 else
                  f'=REPT("█",MIN(ROUND(J12*20),20))&REPT("░",MAX(20-ROUND(J12*20),0))')
             ), fmt=bar_c),
             blank()],
        ]

    # Card 1: Needs (cols A–C = 0–2)
    needs_rows = bucket_card(0,  "🏠 NEEDS",          C["emerald"], "Needs",        "C7")
    # Card 2: Wants (cols E–G = 4–6)
    wants_rows = bucket_card(4,  "🎉 WANTS",          C["gold"],    "Wants",        "C8")
    # Card 3: Savings (cols I–K = 8–10)
    savng_rows = bucket_card(8,  "💳 SAVINGS & DEBT", C["rose"],    "Savings & Debt","C9")

    # Merge card headers
    reqs.append(merge_req(sid, 7, 0,  8, 3))   # Needs  A8:C8
    reqs.append(merge_req(sid, 7, 4,  8, 7))   # Wants  E8:G8
    reqs.append(merge_req(sid, 7, 8,  8, 11))  # Savings I8:K8

    # Fix cell formulas — rewrite with absolute column refs
    # Needs card: B col = col 1; Wants card: F col = col 5; Savings: J col = col 9
    def fix_card_formulas(card_rows, b_col_letter, pct_row_letter):
        """
        The bucket_card function has hardcoded column letters that need fixing
        for Wants and Savings cards.
        We'll just re-generate with correct letters.
        """
        return card_rows  # already correct per card

    # Assemble combined rows for the 6 card rows (rows 7–12 = idx 7–12)
    # We interleave all 3 cards side-by-side:
    # Each row has [Needs_col0, Needs_col1, Needs_col2, gap_col3,
    #               Wants_col4, Wants_col5, Wants_col6, gap_col7,
    #               Sav_col8, Sav_col9, Sav_col10]

    gap = blank()
    for row_offset in range(6):
        n_row = needs_rows[row_offset]
        w_row = wants_rows[row_offset]
        s_row = savng_rows[row_offset]
        # Fix Wants and Savings formulas for remaining/pct/progress
        if row_offset == 3:  # Remaining row
            w_row[1] = cell(formula="=F9-F10", fmt=cell_fmt(number_format=MONEY_FMT))
            s_row[1] = cell(formula="=J9-J10", fmt=cell_fmt(number_format=MONEY_FMT))
        elif row_offset == 4:  # % Used row
            w_row[1] = cell(formula="=IFERROR(F10/F9,0)", fmt=cell_fmt(number_format=PCT_FMT))
            s_row[1] = cell(formula="=IFERROR(J10/J9,0)", fmt=cell_fmt(number_format=PCT_FMT))
        elif row_offset == 5:  # Progress bar
            w_bar_col = C["gold"]
            s_bar_col = C["rose"]
            w_row[1] = cell(
                formula='=REPT("█",MIN(ROUND(F12*20),20))&REPT("░",MAX(20-ROUND(F12*20),0))',
                fmt=cell_fmt(font="Courier New", fg=C["gold"], bold=True))
            s_row[1] = cell(
                formula='=REPT("█",MIN(ROUND(J12*20),20))&REPT("░",MAX(20-ROUND(J12*20),0))',
                fmt=cell_fmt(font="Courier New", fg=C["rose"], bold=True))

        combined_row = n_row + [gap] + w_row + [gap] + s_row
        reqs.append(update_cells_req(sid, 7 + row_offset, 0, [combined_row]))

    # Conditional formatting: Remaining cells (B11, F11, J11)
    for r_col in [1, 5, 9]:
        reqs.append(cond_fmt_req(sid, 10, r_col, 11, r_col+1,
                                 "NUMBER_GREATER_THAN_EQ",
                                 [{"userEnteredValue": "0"}], C["mintBg"]))
        reqs.append(cond_fmt_req(sid, 10, r_col, 11, r_col+1,
                                 "NUMBER_LESS",
                                 [{"userEnteredValue": "0"}], C["coralBg"]))

    # ── Rows 37–38: Top Spending Categories Table ──────────────────────────
    tbl_hdr_fmt = cell_fmt(bg=C["darkGreen"], fg=C["white"], bold=True)
    reqs.append(update_cells_req(sid, 37, 0, [[
        cell("Category",         fmt=tbl_hdr_fmt),
        cell("Bucket",           fmt=tbl_hdr_fmt),
        cell("Spent This Month", fmt=tbl_hdr_fmt),
        cell("% of Total Exp.",  fmt=tbl_hdr_fmt),
    ]]))

    # QUERY formula for top spending
    query_formula = (
        "=IFERROR(QUERY('Expense Log'!C:G,"
        "\"SELECT C, F, SUM(D) WHERE E='Expense' AND G='\"&C2&\"' "
        "GROUP BY C, F ORDER BY SUM(D) DESC "
        "LABEL C 'Category', F 'Bucket', SUM(D) 'Spent'\",0),\"No data\")"
    )
    reqs.append(update_cells_req(sid, 38, 0, [[
        cell(formula=query_formula, fmt=cell_fmt(number_format=MONEY_FMT)),
    ]]))

    # % of total column (D39 onward) — formula referencing C39 / total
    # Total expenses for month
    total_exp_formula = (
        "=IFERROR(SUMIFS('Expense Log'!D:D,"
        "'Expense Log'!E:E,\"Expense\","
        "'Expense Log'!G:G,C2),1)"
    )
    # We'll put the total in a helper cell (col K row 38) and reference it
    reqs.append(update_cells_req(sid, 37, 10, [[
        cell(formula=total_exp_formula,
             fmt=cell_fmt(number_format=MONEY_FMT)),
    ]]))
    # % formulas for rows 39–50
    pct_rows = []
    for i in range(12):
        row_num = 40 + i
        pct_rows.append([
            cell(formula=f"=IFERROR(C{row_num}/$K$38,0)",
                 fmt=cell_fmt(number_format=PCT_FMT)),
        ])
    reqs.append(update_cells_req(sid, 39, 3, pct_rows))

    # ── Freeze rows 1-2 ───────────────────────────────────────────────────
    reqs.append(freeze_req(sid, rows=2, cols=0))

    # ── Column widths ─────────────────────────────────────────────────────
    for col, w in enumerate([140, 140, 140, 140, 140, 140, 140, 140, 140]):
        reqs.append(col_width_req(sid, col, w))

    return reqs


# ─── Charts ──────────────────────────────────────────────────────────────────

def build_chart_requests(spreadsheet_id):
    """
    Charts are embedded in the Dashboard sheet.
    Data for charts is sourced from helper data blocks placed off-screen.
    """
    sid = SID["dashboard"]
    reqs = []

    # ── Chart helper data (placed starting col M = 12, row 7) ────────────
    # Block 1: Bucket spending for donut (rows 7-10, cols 12-13 = M:N)
    # Header + 3 bucket rows — formulas pull from dashboard card values
    reqs.append(update_cells_req(sid, 7, 12, [
        [cell("Bucket",         fmt=cell_fmt(bold=True)),
         cell("Actual Spent",   fmt=cell_fmt(bold=True))],
        [cell("Needs"),
         cell(formula="=B10",  fmt=cell_fmt(number_format=MONEY_FMT))],
        [cell("Wants"),
         cell(formula="=F10",  fmt=cell_fmt(number_format=MONEY_FMT))],
        [cell("Savings & Debt"),
         cell(formula="=J10",  fmt=cell_fmt(number_format=MONEY_FMT))],
    ]))

    # Block 2: Target vs Actual (rows 7-10, cols 15-17 = P:R)
    reqs.append(update_cells_req(sid, 7, 15, [
        [cell("Bucket",         fmt=cell_fmt(bold=True)),
         cell("Target",         fmt=cell_fmt(bold=True)),
         cell("Actual",         fmt=cell_fmt(bold=True))],
        [cell("Needs"),
         cell(formula="=B9",   fmt=cell_fmt(number_format=MONEY_FMT)),
         cell(formula="=B10",  fmt=cell_fmt(number_format=MONEY_FMT))],
        [cell("Wants"),
         cell(formula="=F9",   fmt=cell_fmt(number_format=MONEY_FMT)),
         cell(formula="=F10",  fmt=cell_fmt(number_format=MONEY_FMT))],
        [cell("Savings & Debt"),
         cell(formula="=J9",   fmt=cell_fmt(number_format=MONEY_FMT)),
         cell(formula="=J10",  fmt=cell_fmt(number_format=MONEY_FMT))],
    ]))

    # Block 3: Monthly income/expense trend (rows 19-31, cols 12-15 = M:P)
    # Pull from Budget Setup monthly table
    reqs.append(update_cells_req(sid, 18, 12, [
        [cell("Month", fmt=cell_fmt(bold=True)),
         cell("Base Income", fmt=cell_fmt(bold=True)),
         cell("Side Income", fmt=cell_fmt(bold=True)),
         cell("Total Expenses", fmt=cell_fmt(bold=True))],
    ]))
    for i, month in enumerate(MONTHS_2026):
        setup_row = 15 + i  # 1-indexed row in Budget Setup (C col = base, D = side)
        exp_formula = (
            f"=IFERROR(SUMIFS('Expense Log'!D:D,"
            f"'Expense Log'!E:E,\"Expense\","
            f"'Expense Log'!G:G,\"{month}\"),0)"
        )
        reqs.append(update_cells_req(sid, 19 + i, 12, [[
            cell(month),
            cell(formula=f"='Budget Setup'!C{setup_row}",
                 fmt=cell_fmt(number_format=MONEY_FMT)),
            cell(formula=f"='Budget Setup'!D{setup_row}",
                 fmt=cell_fmt(number_format=MONEY_FMT)),
            cell(formula=exp_formula,
                 fmt=cell_fmt(number_format=MONEY_FMT)),
        ]]))

    # ── Chart 1: Donut — Spending by Bucket ──────────────────────────────
    reqs.append({
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Spending by Bucket",
                    "pieChart": {
                        "legendPosition": "RIGHT_LEGEND",
                        "pieHole": 0.5,
                        "domain": {
                            "sourceRange": {
                                "sources": [range_a1(sid, 8, 12, 11, 13)]
                            }
                        },
                        "series": {
                            "sourceRange": {
                                "sources": [range_a1(sid, 8, 13, 11, 14)]
                            }
                        },
                    },
                    "backgroundColor": hex_to_rgb(C["white"]),
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": sid,
                            "rowIndex": 16,
                            "columnIndex": 0,
                        },
                        "widthPixels": 400,
                        "heightPixels": 300,
                    }
                },
            }
        }
    })

    # ── Chart 2: Grouped Column — Target vs Actual ────────────────────────
    reqs.append({
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Target vs Actual by Bucket",
                    "basicChart": {
                        "chartType": "COLUMN",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {"position": "BOTTOM_AXIS",
                             "title": "Bucket"},
                            {"position": "LEFT_AXIS",
                             "title": "Amount ($)"},
                        ],
                        "domains": [{
                            "domain": {
                                "sourceRange": {
                                    "sources": [range_a1(sid, 8, 15, 11, 16)]
                                }
                            }
                        }],
                        "series": [
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [range_a1(sid, 8, 16, 11, 17)]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "color": hex_to_rgb(C["medGreen"]),
                            },
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [range_a1(sid, 8, 17, 11, 18)]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "color": hex_to_rgb(C["emerald"]),
                            },
                        ],
                        "headerCount": 1,
                    },
                    "backgroundColor": hex_to_rgb(C["white"]),
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": sid,
                            "rowIndex": 16,
                            "columnIndex": 4,
                        },
                        "widthPixels": 450,
                        "heightPixels": 300,
                    }
                },
            }
        }
    })

    # ── Chart 3: Line — Monthly Income vs Expenses ────────────────────────
    reqs.append({
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Income vs Expenses by Month",
                    "basicChart": {
                        "chartType": "LINE",
                        "legendPosition": "TOP_LEGEND",
                        "axis": [
                            {"position": "BOTTOM_AXIS", "title": "Month"},
                            {"position": "LEFT_AXIS",   "title": "Amount ($)"},
                        ],
                        "domains": [{
                            "domain": {
                                "sourceRange": {
                                    "sources": [range_a1(sid, 19, 12, 31, 13)]
                                }
                            }
                        }],
                        "series": [
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [range_a1(sid, 19, 13, 31, 14)]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "color": hex_to_rgb(C["darkGreen"]),
                            },
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [range_a1(sid, 19, 14, 31, 15)]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "color": hex_to_rgb(C["softGold"]),
                            },
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [range_a1(sid, 19, 15, 31, 16)]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "color": hex_to_rgb(C["rose"]),
                            },
                        ],
                        "headerCount": 1,
                    },
                    "backgroundColor": hex_to_rgb(C["white"]),
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": sid,
                            "rowIndex": 34,
                            "columnIndex": 0,
                        },
                        "widthPixels": 600,
                        "heightPixels": 280,
                    }
                },
            }
        }
    })

    return reqs


# ─── Named ranges ─────────────────────────────────────────────────────────────

def build_named_range_requests():
    return [
        named_range_req("INCOME_TARGET",      SID["setup"],     2, 2, 3, 3),
        named_range_req("SIDE_INCOME_TARGET", SID["setup"],     3, 2, 4, 3),
        named_range_req("NEEDS_PCT",          SID["setup"],     6, 2, 7, 3),
        named_range_req("WANTS_PCT",          SID["setup"],     7, 2, 8, 3),
        named_range_req("SAVINGS_PCT",        SID["setup"],     8, 2, 9, 3),
        named_range_req("SELECTED_MONTH",     SID["dashboard"], 1, 2, 2, 3),
    ]


# ─── Main build function ──────────────────────────────────────────────────────

def create_spreadsheet(service):
    """Create a blank spreadsheet with the 4 required sheets."""
    body = {
        "properties": {"title": "50/30/20 Budget Tracker"},
        "sheets": [
            {
                "properties": {
                    "sheetId": SID["dashboard"],
                    "title":   "Dashboard",
                    "index":   0,
                    "gridProperties": {"rowCount": 100, "columnCount": 26},
                }
            },
            {
                "properties": {
                    "sheetId": SID["log"],
                    "title":   "Expense Log",
                    "index":   1,
                    "gridProperties": {"rowCount": 1002, "columnCount": 7},
                }
            },
            {
                "properties": {
                    "sheetId": SID["setup"],
                    "title":   "Budget Setup",
                    "index":   2,
                    "gridProperties": {"rowCount": 50, "columnCount": 8},
                }
            },
            {
                "properties": {
                    "sheetId": SID["reference"],
                    "title":   "Reference",
                    "index":   3,
                    "gridProperties": {"rowCount": 30, "columnCount": 5},
                }
            },
        ],
    }
    result = service.spreadsheets().create(body=body).execute()
    return result["spreadsheetId"], result["spreadsheetUrl"]


def batch_update(service, spreadsheet_id, requests):
    """Execute a batchUpdate, chunking into groups of 50."""
    CHUNK = 50
    for i in range(0, len(requests), CHUNK):
        chunk = requests[i:i+CHUNK]
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": chunk},
        ).execute()
        print(f"  → Batch {i//CHUNK + 1}/{(len(requests)-1)//CHUNK + 1} done "
              f"({len(chunk)} requests)")


def build_patch_requests():
    """
    Requests for the patch path: validation, conditional formatting, named
    ranges.  Does NOT write cell data — safe to run against an already-
    populated spreadsheet.
    """
    reqs = []
    log_sid   = SID["log"]
    dash_sid  = SID["dashboard"]
    setup_sid = SID["setup"]

    # ── Data validation ───────────────────────────────────────────────────────
    reqs.append(data_validation_req(log_sid, 1, 2, 1000, 3,
                                    range_source="Reference!$A$2:$A$28"))
    reqs.append(data_validation_req(log_sid, 1, 4, 1000, 5,
                                    values=["Income", "Side Income", "Expense"]))
    reqs.append(data_validation_req(dash_sid, 1, 2, 2, 3,
                                    range_source="Reference!$D$2:$D$13"))
    reqs.append({
        "setDataValidation": {
            "range": range_a1(setup_sid, 6, 2, 9, 3),
            "rule": {
                "condition": {
                    "type": "NUMBER_BETWEEN",
                    "values": [{"userEnteredValue": "0"},
                               {"userEnteredValue": "1"}],
                },
                "showCustomUi": True,
                "strict": False,
            },
        }
    })

    # ── Conditional formatting ────────────────────────────────────────────────
    for val, bg in [("Needs",          C["mintBg"]),
                    ("Wants",          C["wantsBg"]),
                    ("Savings & Debt", C["savingsBg"])]:
        reqs.append(cond_fmt_req(log_sid, 1, 5, 1000, 6,
                                 "TEXT_EQ", [{"userEnteredValue": val}], bg))
    reqs.append(cond_fmt_req(log_sid, 1, 4, 1000, 5,
                             "TEXT_EQ", [{"userEnteredValue": "Side Income"}],
                             C["amberInput"]))
    reqs.append(cond_fmt_formula_req(setup_sid, 10, 2, 11, 3,
                                     "=C11<>1", C["coralBg"]))
    for r_col in [1, 5, 9]:
        reqs.append(cond_fmt_req(dash_sid, 10, r_col, 11, r_col + 1,
                                 "NUMBER_GREATER_THAN_EQ",
                                 [{"userEnteredValue": "0"}], C["mintBg"]))
        reqs.append(cond_fmt_req(dash_sid, 10, r_col, 11, r_col + 1,
                                 "NUMBER_LESS",
                                 [{"userEnteredValue": "0"}], C["coralBg"]))
    reqs.append(cond_fmt_req(dash_sid, 5, 8, 6, 9,
                             "NUMBER_GREATER_THAN_EQ",
                             [{"userEnteredValue": "1"}], C["mintBg"]))
    reqs.append(cond_fmt_req(dash_sid, 5, 8, 6, 9,
                             "NUMBER_LESS",
                             [{"userEnteredValue": "0.8"}], C["coralBg"]))

    # ── Named ranges ─────────────────────────────────────────────────────────
    reqs.extend(build_named_range_requests())

    return reqs


def build(service, existing_id=None):
    if existing_id:
        spreadsheet_id = existing_id
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
        print(f"Using existing spreadsheet: {url}")
        print("Skipping steps 1–5 (data already populated) …")

        print("Applying validation, conditional formatting, named ranges …")
        batch_update(service, spreadsheet_id, build_patch_requests())
    else:
        print("Creating spreadsheet …")
        spreadsheet_id, url = create_spreadsheet(service)
        print(f"  → Created: {url}")

        all_requests = []
        print("Building Reference tab …")
        all_requests.extend(build_reference_requests())
        print("Building Expense Log tab …")
        all_requests.extend(build_log_requests())
        print("Building Budget Setup tab …")
        all_requests.extend(build_setup_requests())
        print("Building Dashboard tab …")
        all_requests.extend(build_dashboard_requests())
        print("Adding named ranges …")
        all_requests.extend(build_named_range_requests())
        print(f"Executing {len(all_requests)} API requests …")
        batch_update(service, spreadsheet_id, all_requests)

    print("Adding charts …")
    batch_update(service, spreadsheet_id,
                 build_chart_requests(spreadsheet_id))

    print("\n✅ Done!")
    print(f"   Spreadsheet URL: {url}")
    print(f"   Spreadsheet ID:  {spreadsheet_id}")
    return spreadsheet_id, url


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Build the 50/30/20 Budget Tracker in Google Sheets."
    )
    parser.add_argument("--creds", help="Path to OAuth2 client_secrets JSON file")
    parser.add_argument("--token", default="token.json",
                        help="Path to saved OAuth token (default: token.json)")
    parser.add_argument(
        "--spreadsheet-id",
        metavar="ID",
        help=(
            "Patch an existing spreadsheet instead of creating a new one. "
            "Skips data-population steps and runs only validation, "
            "conditional formatting, named ranges, and charts."
        ),
    )
    args = parser.parse_args()

    service = get_service(creds_file=args.creds, token_file=args.token)
    build(service, existing_id=args.spreadsheet_id)


if __name__ == "__main__":
    main()
