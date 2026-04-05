#!/usr/bin/env bash
# ============================================================
# 50/30/20 Personal Budget Tracker — Google Sheets Builder
# Uses: gws CLI  (https://github.com/googleworkspace/cli)
#
# SETUP (one time):
#   gws auth login --services sheets drive
#
# RUN:
#   bash build_tracker.sh
# ============================================================
set -euo pipefail

GWS="${GWS_BIN:-gws}"

# Verify gws is available and authenticated
if ! command -v "$GWS" &>/dev/null; then
  echo "Error: gws not found. Install with: npm install -g @googleworkspace/cli"
  exit 1
fi

AUTH_STATUS=$("$GWS" auth status 2>/dev/null | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('auth_method','none'))" 2>/dev/null || echo "none")

if [[ "$AUTH_STATUS" == "none" ]]; then
  echo "Error: Not authenticated. Run: gws auth login --services sheets drive"
  exit 1
fi

gws() { "$GWS" "$@"; }

echo "🚀 Building 50/30/20 Budget Tracker…"

# ── Step 1: Create spreadsheet with all 4 tabs ──────────────────────────────
echo "  [1/9] Creating spreadsheet with 4 tabs…"

SPREADSHEET=$(gws sheets spreadsheets create --json '{
  "properties": {"title": "💰 50/30/20 Budget Tracker"},
  "sheets": [
    {"properties": {"sheetId": 0, "title": "Dashboard",    "index": 0,
                    "gridProperties": {"rowCount": 100, "columnCount": 26}}},
    {"properties": {"sheetId": 1, "title": "Expense Log",  "index": 1,
                    "gridProperties": {"rowCount": 1002, "columnCount": 8}}},
    {"properties": {"sheetId": 2, "title": "Budget Setup", "index": 2,
                    "gridProperties": {"rowCount": 50,  "columnCount": 8}}},
    {"properties": {"sheetId": 3, "title": "Reference",    "index": 3,
                    "gridProperties": {"rowCount": 30,  "columnCount": 6}}}
  ]
}')

SID=$(echo "$SPREADSHEET" | python3 -c "import sys,json; print(json.load(sys.stdin)['spreadsheetId'])")
URL=$(echo "$SPREADSHEET" | python3 -c "import sys,json; print(json.load(sys.stdin)['spreadsheetUrl'])")
echo "     → ID: $SID"

# Helper: run a batchUpdate
batch() {
  gws sheets spreadsheets batchUpdate \
    --params "{\"spreadsheetId\":\"$SID\"}" \
    --json "$1"
}

# Helper: update cell values
values_update() {
  local RANGE="$1"
  local BODY="$2"
  gws sheets spreadsheets values update \
    --params "{\"spreadsheetId\":\"$SID\",\"range\":\"$RANGE\",\"valueInputOption\":\"USER_ENTERED\"}" \
    --json "$BODY" > /dev/null
}

# ── Step 2: Reference tab — categories + months ─────────────────────────────
echo "  [2/9] Populating Reference tab…"

values_update "Reference!A1:D28" '{
  "values": [
    ["Category","Bucket","","Month"],
    ["Rent / Mortgage","Needs","","2026-01"],
    ["Utilities","Needs","","2026-02"],
    ["Groceries","Needs","","2026-03"],
    ["Transportation","Needs","","2026-04"],
    ["Insurance","Needs","","2026-05"],
    ["Healthcare","Needs","","2026-06"],
    ["Phone","Needs","","2026-07"],
    ["Internet","Needs","","2026-08"],
    ["Childcare","Needs","","2026-09"],
    ["Minimum Debt Payments","Needs","","2026-10"],
    ["Dining Out","Wants","","2026-11"],
    ["Entertainment","Wants","","2026-12"],
    ["Shopping","Wants","",""],
    ["Subscriptions","Wants","",""],
    ["Personal Care","Wants","",""],
    ["Gym / Fitness","Wants","",""],
    ["Travel","Wants","",""],
    ["Gifts","Wants","",""],
    ["Hobbies","Wants","",""],
    ["Coffee / Drinks","Wants","",""],
    ["Emergency Fund","Savings & Debt","",""],
    ["Retirement / 401k","Savings & Debt","",""],
    ["Extra Debt Payment","Savings & Debt","",""],
    ["Investments","Savings & Debt","",""],
    ["Sinking Funds","Savings & Debt","",""],
    ["Freelance / Gig Work","Side Income Tracking","",""],
    ["Online Sales","Side Income Tracking","",""]
  ]
}'

# ── Step 3: Expense Log — headers ───────────────────────────────────────────
echo "  [3/9] Building Expense Log headers and data…"

values_update "Expense Log!A1:G1" '{
  "values": [["Date","Description","Category","Amount","Type","Bucket","Month"]]
}'

# Sample data — dates as text; Bucket(F) and Month(G) are formulas added below
values_update "'Expense Log'!A2:E51" '{
  "values": [
    ["01/01/2026","Paycheck","Income",2600,"Income"],
    ["01/15/2026","Paycheck","Income",2600,"Income"],
    ["01/10/2026","Etsy Sales","Side Income",120,"Side Income"],
    ["01/22/2026","Freelance Design","Side Income",250,"Side Income"],
    ["01/02/2026","Rent","Rent / Mortgage",1500,"Expense"],
    ["01/04/2026","Electric Bill","Utilities",85,"Expense"],
    ["01/05/2026","Whole Foods","Groceries",210,"Expense"],
    ["01/06/2026","Spotify","Subscriptions",11,"Expense"],
    ["01/07/2026","Netflix","Subscriptions",16,"Expense"],
    ["01/08/2026","Planet Fitness","Gym / Fitness",25,"Expense"],
    ["01/10/2026","Chipotle","Dining Out",18,"Expense"],
    ["01/12/2026","T-Mobile","Phone",55,"Expense"],
    ["01/14/2026","Target","Shopping",94,"Expense"],
    ["01/16/2026","Roth IRA","Retirement / 401k",500,"Expense"],
    ["01/18/2026","Car Insurance","Insurance",120,"Expense"],
    ["01/20/2026","Starbucks","Coffee / Drinks",47,"Expense"],
    ["01/22/2026","Extra Car Payment","Extra Debt Payment",200,"Expense"],
    ["01/25/2026","Movie Tickets","Entertainment",35,"Expense"],
    ["01/28/2026","Internet","Internet",60,"Expense"],
    ["02/01/2026","Paycheck","Income",2600,"Income"],
    ["02/15/2026","Paycheck","Income",2600,"Income"],
    ["02/08/2026","Tutoring Session","Side Income",180,"Side Income"],
    ["02/20/2026","Etsy Sales","Side Income",95,"Side Income"],
    ["02/02/2026","Rent","Rent / Mortgage",1500,"Expense"],
    ["02/03/2026","Whole Foods","Groceries",185,"Expense"],
    ["02/05/2026","Gas","Transportation",62,"Expense"],
    ["02/07/2026","Amazon","Shopping",134,"Expense"],
    ["02/09/2026","Doctor Copay","Healthcare",40,"Expense"],
    ["02/11/2026","Dinner Out","Dining Out",72,"Expense"],
    ["02/13/2026","Valentines Gift","Gifts",65,"Expense"],
    ["02/15/2026","Electric Bill","Utilities",91,"Expense"],
    ["02/18/2026","Roth IRA","Retirement / 401k",500,"Expense"],
    ["02/20/2026","Sinking Fund","Sinking Funds",150,"Expense"],
    ["02/22/2026","T-Mobile","Phone",55,"Expense"],
    ["02/25/2026","Hulu","Subscriptions",18,"Expense"],
    ["03/01/2026","Paycheck","Income",2600,"Income"],
    ["03/15/2026","Paycheck","Income",2600,"Income"],
    ["03/20/2026","Bonus","Income",500,"Income"],
    ["03/05/2026","Freelance Writing","Side Income",320,"Side Income"],
    ["03/18/2026","eBay Sales","Side Income",145,"Side Income"],
    ["03/02/2026","Rent","Rent / Mortgage",1500,"Expense"],
    ["03/04/2026","Whole Foods","Groceries",220,"Expense"],
    ["03/06/2026","Gas","Transportation",55,"Expense"],
    ["03/10/2026","Clothing","Shopping",180,"Expense"],
    ["03/12/2026","Concert Tickets","Entertainment",95,"Expense"],
    ["03/15/2026","T-Mobile","Phone",55,"Expense"],
    ["03/18/2026","Roth IRA","Retirement / 401k",500,"Expense"],
    ["03/20/2026","Emergency Fund","Emergency Fund",300,"Expense"],
    ["03/22/2026","Sushi Dinner","Dining Out",88,"Expense"],
    ["03/25/2026","Internet","Internet",60,"Expense"]
  ]
}'

# Bucket + Month formulas via batchUpdate (row by row, rows 2-51)
echo "  Inserting Bucket/Month formulas…"
FORMULA_ROWS='[]'
for ROW in $(seq 2 51); do
  FORMULA_ROWS=$(echo "$FORMULA_ROWS" | python3 -c "
import sys, json
rows = json.load(sys.stdin)
r = $ROW
rows.append({
  'values': [
    {'userEnteredValue': {'formulaValue': f'=IFERROR(VLOOKUP(C{r},Reference!\$A:\$B,2,FALSE),\"\")'}},
    {'userEnteredValue': {'formulaValue': f'=IF(A{r}=\"\",\"\",TEXT(A{r},\"YYYY-MM\"))'}}
  ]
})
print(json.dumps(rows))
")
done

batch "{\"requests\":[{\"updateCells\":{
  \"rows\":$FORMULA_ROWS,
  \"fields\":\"userEnteredValue\",
  \"start\":{\"sheetId\":1,\"rowIndex\":1,\"columnIndex\":5}
}}]}" > /dev/null


# ── Step 4: Budget Setup tab ─────────────────────────────────────────────────
echo "  [4/9] Building Budget Setup tab…"

values_update "'Budget Setup'!A1:F1" '{"values":[["⚙️ Budget Setup","","","","",""]]}'
values_update "'Budget Setup'!B3:C5" '{"values":[
  ["Monthly Base Income Target",5000],
  ["Monthly Side Income Target",500],
  ["Combined Income Target","=C3+C4"]
]}'
values_update "'Budget Setup'!B7:C9" '{"values":[
  ["Needs % Target",0.5],
  ["Wants % Target",0.3],
  ["Savings & Debt % Target",0.2]
]}'
values_update "'Budget Setup'!B11:C11" '{"values":[["⚠️ Ratio Total Check","=C7+C8+C9"]]}'
values_update "'Budget Setup'!B13:E14" '{"values":[
  ["📅 Actual Monthly Income by Month","","",""],
  ["Month","Base Income","Side Income","Total"]
]}'
values_update "'Budget Setup'!B15:E26" '{"values":[
  ["2026-01","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Income\",'"'"'Expense Log'"'"'!G:G,B15),0)","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Side Income\",'"'"'Expense Log'"'"'!G:G,B15),0)","=C15+D15"],
  ["2026-02","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Income\",'"'"'Expense Log'"'"'!G:G,B16),0)","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Side Income\",'"'"'Expense Log'"'"'!G:G,B16),0)","=C16+D16"],
  ["2026-03","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Income\",'"'"'Expense Log'"'"'!G:G,B17),0)","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Side Income\",'"'"'Expense Log'"'"'!G:G,B17),0)","=C17+D17"],
  ["2026-04","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Income\",'"'"'Expense Log'"'"'!G:G,B18),0)","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Side Income\",'"'"'Expense Log'"'"'!G:G,B18),0)","=C18+D18"],
  ["2026-05","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Income\",'"'"'Expense Log'"'"'!G:G,B19),0)","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Side Income\",'"'"'Expense Log'"'"'!G:G,B19),0)","=C19+D19"],
  ["2026-06","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Income\",'"'"'Expense Log'"'"'!G:G,B20),0)","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Side Income\",'"'"'Expense Log'"'"'!G:G,B20),0)","=C20+D20"],
  ["2026-07","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Income\",'"'"'Expense Log'"'"'!G:G,B21),0)","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Side Income\",'"'"'Expense Log'"'"'!G:G,B21),0)","=C21+D21"],
  ["2026-08","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Income\",'"'"'Expense Log'"'"'!G:G,B22),0)","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Side Income\",'"'"'Expense Log'"'"'!G:G,B22),0)","=C22+D22"],
  ["2026-09","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Income\",'"'"'Expense Log'"'"'!G:G,B23),0)","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Side Income\",'"'"'Expense Log'"'"'!G:G,B23),0)","=C23+D23"],
  ["2026-10","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Income\",'"'"'Expense Log'"'"'!G:G,B24),0)","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Side Income\",'"'"'Expense Log'"'"'!G:G,B24),0)","=C24+D24"],
  ["2026-11","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Income\",'"'"'Expense Log'"'"'!G:G,B25),0)","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Side Income\",'"'"'Expense Log'"'"'!G:G,B25),0)","=C25+D25"],
  ["2026-12","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Income\",'"'"'Expense Log'"'"'!G:G,B26),0)","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Side Income\",'"'"'Expense Log'"'"'!G:G,B26),0)","=C26+D26"]
]}'

# ── Step 5: Dashboard tab ────────────────────────────────────────────────────
echo "  [5/9] Building Dashboard formulas…"

values_update "Dashboard!A1" '{"values":[["💰 50/30/20 Budget Dashboard"]]}'
values_update "Dashboard!B2:C2" '{"values":[["Select Month:","2026-01"]]}'

# Income summary (rows 4-6, 1-indexed)
values_update "Dashboard!A4:I6" '{"values":[
  ["💵 Base Income","","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Income\",'"'"'Expense Log'"'"'!G:G,C2),0)",
   "⚡ Side Income","","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Side Income\",'"'"'Expense Log'"'"'!G:G,C2),0)",
   "💰 Total Income","","=C4+F4"],
  ["🎯 Base Target","","='"'"'Budget Setup'"'"'!C3",
   "🎯 Side Target","","='"'"'Budget Setup'"'"'!C4",
   "🎯 Combined Target","","='"'"'Budget Setup'"'"'!C5"],
  ["📊 % of Combined Target","","","","","","","","=IFERROR(I4/I5,0)"]
]}'

# Bucket cards (rows 8-13, 1-indexed)
values_update "Dashboard!A8:K13" '{"values":[
  ["🏠 NEEDS","","","","🎉 WANTS","","","","💳 SAVINGS & DEBT","",""],
  ["Target Amount","=ROUND('"'"'Budget Setup'"'"'!C5*'"'"'Budget Setup'"'"'!C7,2)","","",
   "Target Amount","=ROUND('"'"'Budget Setup'"'"'!C5*'"'"'Budget Setup'"'"'!C8,2)","","",
   "Target Amount","=ROUND('"'"'Budget Setup'"'"'!C5*'"'"'Budget Setup'"'"'!C9,2)",""],
  ["Actual Spent","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Expense\",'"'"'Expense Log'"'"'!F:F,\"Needs\",'"'"'Expense Log'"'"'!G:G,C2),0)","","",
   "Actual Spent","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Expense\",'"'"'Expense Log'"'"'!F:F,\"Wants\",'"'"'Expense Log'"'"'!G:G,C2),0)","","",
   "Actual Spent","=IFERROR(SUMIFS('"'"'Expense Log'"'"'!D:D,'"'"'Expense Log'"'"'!E:E,\"Expense\",'"'"'Expense Log'"'"'!F:F,\"Savings & Debt\",'"'"'Expense Log'"'"'!G:G,C2),0)",""],
  ["Remaining","=B9-B10","","","Remaining","=F9-F10","","","Remaining","=J9-J10",""],
  ["% Used","=IFERROR(B10/B9,0)","","","% Used","=IFERROR(F10/F9,0)","","","% Used","=IFERROR(J10/J9,0)",""],
  ["Progress","=REPT(\"█\",MIN(ROUND(B12*20),20))&REPT(\"░\",MAX(20-ROUND(B12*20),0))","","",
   "Progress","=REPT(\"█\",MIN(ROUND(F12*20),20))&REPT(\"░\",MAX(20-ROUND(F12*20),0))","","",
   "Progress","=REPT(\"█\",MIN(ROUND(J12*20),20))&REPT(\"░\",MAX(20-ROUND(J12*20),0))",""]
]}'

# Top Spending Categories table (row 38+)
values_update "Dashboard!A38:D38" '{"values":[["Category","Bucket","Spent This Month","% of Total Exp."]]}'
values_update "Dashboard!A39" "{\"values\":[[\"=IFERROR(QUERY('Expense Log'!C:G,\\\"SELECT C, F, SUM(D) WHERE E='Expense' AND G='\\\"&C2&\\\"' GROUP BY C, F ORDER BY SUM(D) DESC LABEL C 'Category', F 'Bucket', SUM(D) 'Spent'\\\",0),\\\"No data\\\")\"]]}"
# Total expenses helper (col K row 38)
values_update "Dashboard!K38" "{\"values\":[[\"=IFERROR(SUMIFS('Expense Log'!D:D,'Expense Log'!E:E,\\\"Expense\\\",'Expense Log'!G:G,C2),1)\"]]}"
# % column for rows 39-50
values_update "Dashboard!D39:D50" '{"values":[
  ["=IFERROR(C39/$K$38,0)"],["=IFERROR(C40/$K$38,0)"],["=IFERROR(C41/$K$38,0)"],
  ["=IFERROR(C42/$K$38,0)"],["=IFERROR(C43/$K$38,0)"],["=IFERROR(C44/$K$38,0)"],
  ["=IFERROR(C45/$K$38,0)"],["=IFERROR(C46/$K$38,0)"],["=IFERROR(C47/$K$38,0)"],
  ["=IFERROR(C48/$K$38,0)"],["=IFERROR(C49/$K$38,0)"],["=IFERROR(C50/$K$38,0)"]
]}'

# Chart helper data (off-screen, col M+)
values_update "Dashboard!M8:N11" '{"values":[
  ["Bucket","Actual Spent"],
  ["Needs","=B10"],["Wants","=F10"],["Savings & Debt","=J10"]
]}'
values_update "Dashboard!P8:R11" '{"values":[
  ["Bucket","Target","Actual"],
  ["Needs","=B9","=B10"],["Wants","=F9","=F10"],["Savings & Debt","=J9","=J10"]
]}'
values_update "Dashboard!M19:P19" '{"values":[["Month","Base Income","Side Income","Total Expenses"]]}'

MONTHS=("2026-01" "2026-02" "2026-03" "2026-04" "2026-05" "2026-06"
        "2026-07" "2026-08" "2026-09" "2026-10" "2026-11" "2026-12")
SETUP_ROWS=(15 16 17 18 19 20 21 22 23 24 25 26)
for i in "${!MONTHS[@]}"; do
  MONTH="${MONTHS[$i]}"
  SROW="${SETUP_ROWS[$i]}"
  DROW=$((20 + i))
  values_update "Dashboard!M${DROW}:P${DROW}" "{\"values\":[[
    \"${MONTH}\",
    \"='Budget Setup'!C${SROW}\",
    \"='Budget Setup'!D${SROW}\",
    \"=IFERROR(SUMIFS('Expense Log'!D:D,'Expense Log'!E:E,\\\"Expense\\\",'Expense Log'!G:G,\\\"${MONTH}\\\"),0)\"
  ]]}"
done


# ── Step 6: Formatting — colors, fonts, merges, widths, freezes ─────────────
echo "  [6/9] Applying formatting (colors, merges, freezes, column widths)…"

batch '{
  "requests": [

    {"updateSheetProperties":{"properties":{"sheetId":3,"hidden":true},"fields":"hidden"}},

    {"updateDimensionProperties":{"range":{"sheetId":1,"dimension":"COLUMNS","startIndex":0,"endIndex":1},"properties":{"pixelSize":110},"fields":"pixelSize"}},
    {"updateDimensionProperties":{"range":{"sheetId":1,"dimension":"COLUMNS","startIndex":1,"endIndex":2},"properties":{"pixelSize":200},"fields":"pixelSize"}},
    {"updateDimensionProperties":{"range":{"sheetId":1,"dimension":"COLUMNS","startIndex":2,"endIndex":3},"properties":{"pixelSize":180},"fields":"pixelSize"}},
    {"updateDimensionProperties":{"range":{"sheetId":1,"dimension":"COLUMNS","startIndex":3,"endIndex":4},"properties":{"pixelSize":110},"fields":"pixelSize"}},
    {"updateDimensionProperties":{"range":{"sheetId":1,"dimension":"COLUMNS","startIndex":4,"endIndex":5},"properties":{"pixelSize":120},"fields":"pixelSize"}},
    {"updateDimensionProperties":{"range":{"sheetId":1,"dimension":"COLUMNS","startIndex":5,"endIndex":6},"properties":{"pixelSize":150},"fields":"pixelSize"}},
    {"updateDimensionProperties":{"range":{"sheetId":1,"dimension":"COLUMNS","startIndex":6,"endIndex":7},"properties":{"pixelSize":90},"fields":"pixelSize"}},

    {"updateSheetProperties":{"properties":{"sheetId":1,"gridProperties":{"frozenRowCount":1,"frozenColumnCount":1}},"fields":"gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}},
    {"updateSheetProperties":{"properties":{"sheetId":2,"gridProperties":{"frozenRowCount":3}},"fields":"gridProperties.frozenRowCount"}},
    {"updateSheetProperties":{"properties":{"sheetId":0,"gridProperties":{"frozenRowCount":2}},"fields":"gridProperties.frozenRowCount"}},

    {"updateDimensionProperties":{"range":{"sheetId":0,"dimension":"ROWS","startIndex":0,"endIndex":1},"properties":{"pixelSize":50},"fields":"pixelSize"}},

    {"updateCells":{"rows":[{"values":[
      {"userEnteredFormat":{"backgroundColor":{"red":0.106,"green":0.263,"blue":0.196},"textFormat":{"foregroundColor":{"red":1,"green":1,"blue":1},"bold":true,"fontSize":16},"horizontalAlignment":"CENTER","verticalAlignment":"MIDDLE"}}
    ]}],"fields":"userEnteredFormat","start":{"sheetId":0,"rowIndex":0,"columnIndex":0}}},
    {"mergeCells":{"range":{"sheetId":0,"startRowIndex":0,"endRowIndex":1,"startColumnIndex":0,"endColumnIndex":10},"mergeType":"MERGE_ALL"}},

    {"updateCells":{"rows":[{"values":[
      {"userEnteredFormat":{"backgroundColor":{"red":1.0,"green":0.973,"blue":0.878}}}
    ]}],"fields":"userEnteredFormat","start":{"sheetId":0,"rowIndex":1,"columnIndex":2}}},

    {"updateCells":{"rows":[
      {"values":[
        {"userEnteredFormat":{"backgroundColor":{"red":0.106,"green":0.263,"blue":0.196},"textFormat":{"foregroundColor":{"red":1,"green":1,"blue":1},"bold":true,"fontSize":14},"horizontalAlignment":"CENTER","verticalAlignment":"MIDDLE"}}
      ]}
    ],"fields":"userEnteredFormat","start":{"sheetId":2,"rowIndex":0,"columnIndex":0}}},
    {"mergeCells":{"range":{"sheetId":2,"startRowIndex":0,"endRowIndex":1,"startColumnIndex":0,"endColumnIndex":6},"mergeType":"MERGE_ALL"}},

    {"updateCells":{"rows":[{"values":[
      {"userEnteredFormat":{"backgroundColor":{"red":1.0,"green":0.973,"blue":0.878},"numberFormat":{"type":"CURRENCY","pattern":"$#,##0.00"}}}
    ]}],"fields":"userEnteredFormat","start":{"sheetId":2,"rowIndex":2,"columnIndex":2}}},
    {"updateCells":{"rows":[{"values":[
      {"userEnteredFormat":{"backgroundColor":{"red":1.0,"green":0.973,"blue":0.878},"numberFormat":{"type":"CURRENCY","pattern":"$#,##0.00"}}}
    ]}],"fields":"userEnteredFormat","start":{"sheetId":2,"rowIndex":3,"columnIndex":2}}},
    {"updateCells":{"rows":[{"values":[
      {"userEnteredFormat":{"backgroundColor":{"red":0.941,"green":0.965,"blue":0.957},"numberFormat":{"type":"CURRENCY","pattern":"$#,##0.00"}}}
    ]}],"fields":"userEnteredFormat","start":{"sheetId":2,"rowIndex":4,"columnIndex":2}}},

    {"updateCells":{"rows":[{"values":[
      {"userEnteredFormat":{"backgroundColor":{"red":1.0,"green":0.973,"blue":0.878},"numberFormat":{"type":"NUMBER","pattern":"0%"}}}
    ]}],"fields":"userEnteredFormat","start":{"sheetId":2,"rowIndex":6,"columnIndex":2}}},
    {"updateCells":{"rows":[{"values":[
      {"userEnteredFormat":{"backgroundColor":{"red":1.0,"green":0.973,"blue":0.878},"numberFormat":{"type":"NUMBER","pattern":"0%"}}}
    ]}],"fields":"userEnteredFormat","start":{"sheetId":2,"rowIndex":7,"columnIndex":2}}},
    {"updateCells":{"rows":[{"values":[
      {"userEnteredFormat":{"backgroundColor":{"red":1.0,"green":0.973,"blue":0.878},"numberFormat":{"type":"NUMBER","pattern":"0%"}}}
    ]}],"fields":"userEnteredFormat","start":{"sheetId":2,"rowIndex":8,"columnIndex":2}}},

    {"updateCells":{"rows":[{"values":[
      {"userEnteredFormat":{"backgroundColor":{"red":0.106,"green":0.263,"blue":0.196},"textFormat":{"foregroundColor":{"red":1,"green":1,"blue":1},"bold":true}}}
    ]}],"fields":"userEnteredFormat","start":{"sheetId":2,"rowIndex":13,"columnIndex":1}}},
    {"updateCells":{"rows":[{"values":[
      {"userEnteredFormat":{"backgroundColor":{"red":0.106,"green":0.263,"blue":0.196},"textFormat":{"foregroundColor":{"red":1,"green":1,"blue":1},"bold":true}}},
      {"userEnteredFormat":{"backgroundColor":{"red":0.106,"green":0.263,"blue":0.196},"textFormat":{"foregroundColor":{"red":1,"green":1,"blue":1},"bold":true}}},
      {"userEnteredFormat":{"backgroundColor":{"red":0.106,"green":0.263,"blue":0.196},"textFormat":{"foregroundColor":{"red":1,"green":1,"blue":1},"bold":true}}},
      {"userEnteredFormat":{"backgroundColor":{"red":0.106,"green":0.263,"blue":0.196},"textFormat":{"foregroundColor":{"red":1,"green":1,"blue":1},"bold":true}}}
    ]}],"fields":"userEnteredFormat","start":{"sheetId":2,"rowIndex":13,"columnIndex":1}}}
  ]
}' > /dev/null


# Dashboard formatting — header row, income cards, bucket card headers
batch '{
  "requests": [
    {"updateCells":{"rows":[{"values":[
      {"userEnteredFormat":{"backgroundColor":{"red":0.106,"green":0.263,"blue":0.196},"textFormat":{"foregroundColor":{"red":1,"green":1,"blue":1},"bold":true,"fontSize":11}}}
    ]}],"fields":"userEnteredFormat","start":{"sheetId":1,"rowIndex":0,"columnIndex":0}}},
    {"repeatCell":{"range":{"sheetId":1,"startRowIndex":0,"endRowIndex":1,"startColumnIndex":0,"endColumnIndex":7},"cell":{"userEnteredFormat":{"backgroundColor":{"red":0.106,"green":0.263,"blue":0.196},"textFormat":{"foregroundColor":{"red":1,"green":1,"blue":1},"bold":true,"fontSize":11}}},"fields":"userEnteredFormat"}},

    {"mergeCells":{"range":{"sheetId":0,"startRowIndex":3,"endRowIndex":4,"startColumnIndex":0,"endColumnIndex":2},"mergeType":"MERGE_ALL"}},
    {"mergeCells":{"range":{"sheetId":0,"startRowIndex":3,"endRowIndex":4,"startColumnIndex":3,"endColumnIndex":5},"mergeType":"MERGE_ALL"}},
    {"mergeCells":{"range":{"sheetId":0,"startRowIndex":3,"endRowIndex":4,"startColumnIndex":6,"endColumnIndex":8},"mergeType":"MERGE_ALL"}},
    {"mergeCells":{"range":{"sheetId":0,"startRowIndex":4,"endRowIndex":5,"startColumnIndex":0,"endColumnIndex":2},"mergeType":"MERGE_ALL"}},
    {"mergeCells":{"range":{"sheetId":0,"startRowIndex":4,"endRowIndex":5,"startColumnIndex":3,"endColumnIndex":5},"mergeType":"MERGE_ALL"}},
    {"mergeCells":{"range":{"sheetId":0,"startRowIndex":4,"endRowIndex":5,"startColumnIndex":6,"endColumnIndex":8},"mergeType":"MERGE_ALL"}},
    {"mergeCells":{"range":{"sheetId":0,"startRowIndex":5,"endRowIndex":6,"startColumnIndex":0,"endColumnIndex":8},"mergeType":"MERGE_ALL"}},

    {"mergeCells":{"range":{"sheetId":0,"startRowIndex":7,"endRowIndex":8,"startColumnIndex":0,"endColumnIndex":3},"mergeType":"MERGE_ALL"}},
    {"mergeCells":{"range":{"sheetId":0,"startRowIndex":7,"endRowIndex":8,"startColumnIndex":4,"endColumnIndex":7},"mergeType":"MERGE_ALL"}},
    {"mergeCells":{"range":{"sheetId":0,"startRowIndex":7,"endRowIndex":8,"startColumnIndex":8,"endColumnIndex":11},"mergeType":"MERGE_ALL"}},

    {"repeatCell":{"range":{"sheetId":0,"startRowIndex":7,"endRowIndex":8,"startColumnIndex":0,"endColumnIndex":3},
      "cell":{"userEnteredFormat":{"backgroundColor":{"red":0.251,"green":0.569,"blue":0.424},"textFormat":{"foregroundColor":{"red":1,"green":1,"blue":1},"bold":true,"fontSize":12},"horizontalAlignment":"CENTER"}},"fields":"userEnteredFormat"}},
    {"repeatCell":{"range":{"sheetId":0,"startRowIndex":7,"endRowIndex":8,"startColumnIndex":4,"endColumnIndex":7},
      "cell":{"userEnteredFormat":{"backgroundColor":{"red":0.831,"green":0.627,"blue":0.090},"textFormat":{"foregroundColor":{"red":1,"green":1,"blue":1},"bold":true,"fontSize":12},"horizontalAlignment":"CENTER"}},"fields":"userEnteredFormat"}},
    {"repeatCell":{"range":{"sheetId":0,"startRowIndex":7,"endRowIndex":8,"startColumnIndex":8,"endColumnIndex":11},
      "cell":{"userEnteredFormat":{"backgroundColor":{"red":0.710,"green":0.514,"blue":0.553},"textFormat":{"foregroundColor":{"red":1,"green":1,"blue":1},"bold":true,"fontSize":12},"horizontalAlignment":"CENTER"}},"fields":"userEnteredFormat"}},

    {"updateCells":{"rows":[{"values":[
      {"userEnteredFormat":{"backgroundColor":{"red":1.0,"green":0.973,"blue":0.878},"textFormat":{"bold":true}}}
    ]}],"fields":"userEnteredFormat","start":{"sheetId":0,"rowIndex":5,"columnIndex":8}}},
    {"updateCells":{"rows":[{"values":[
      {"userEnteredFormat":{"numberFormat":{"type":"CURRENCY","pattern":"$#,##0.00"},"textFormat":{"bold":true}}}
    ]}],"fields":"userEnteredFormat","start":{"sheetId":0,"rowIndex":3,"columnIndex":2}}},
    {"updateCells":{"rows":[{"values":[
      {"userEnteredFormat":{"backgroundColor":{"red":1.0,"green":0.973,"blue":0.878},"numberFormat":{"type":"CURRENCY","pattern":"$#,##0.00"},"textFormat":{"bold":true}}}
    ]}],"fields":"userEnteredFormat","start":{"sheetId":0,"rowIndex":3,"columnIndex":5}}},
    {"updateCells":{"rows":[{"values":[
      {"userEnteredFormat":{"backgroundColor":{"red":0.941,"green":0.965,"blue":0.957},"numberFormat":{"type":"CURRENCY","pattern":"$#,##0.00"},"textFormat":{"bold":true}}}
    ]}],"fields":"userEnteredFormat","start":{"sheetId":0,"rowIndex":3,"columnIndex":8}}},
    {"updateCells":{"rows":[{"values":[
      {"userEnteredFormat":{"numberFormat":{"type":"NUMBER","pattern":"0%"},"textFormat":{"bold":true}}}
    ]}],"fields":"userEnteredFormat","start":{"sheetId":0,"rowIndex":5,"columnIndex":8}}},

    {"repeatCell":{"range":{"sheetId":0,"startRowIndex":37,"endRowIndex":38,"startColumnIndex":0,"endColumnIndex":4},
      "cell":{"userEnteredFormat":{"backgroundColor":{"red":0.106,"green":0.263,"blue":0.196},"textFormat":{"foregroundColor":{"red":1,"green":1,"blue":1},"bold":true}}},"fields":"userEnteredFormat"}},

    {"repeatCell":{"range":{"sheetId":0,"startRowIndex":8,"endRowIndex":14,"startColumnIndex":1,"endColumnIndex":2},
      "cell":{"userEnteredFormat":{"numberFormat":{"type":"CURRENCY","pattern":"$#,##0.00"}}},"fields":"userEnteredFormat"}},
    {"repeatCell":{"range":{"sheetId":0,"startRowIndex":8,"endRowIndex":14,"startColumnIndex":5,"endColumnIndex":6},
      "cell":{"userEnteredFormat":{"numberFormat":{"type":"CURRENCY","pattern":"$#,##0.00"}}},"fields":"userEnteredFormat"}},
    {"repeatCell":{"range":{"sheetId":0,"startRowIndex":8,"endRowIndex":14,"startColumnIndex":9,"endColumnIndex":10},
      "cell":{"userEnteredFormat":{"numberFormat":{"type":"CURRENCY","pattern":"$#,##0.00"}}},"fields":"userEnteredFormat"}},

    {"repeatCell":{"range":{"sheetId":0,"startRowIndex":11,"endRowIndex":12,"startColumnIndex":1,"endColumnIndex":2},
      "cell":{"userEnteredFormat":{"numberFormat":{"type":"NUMBER","pattern":"0%"}}},"fields":"userEnteredFormat"}},
    {"repeatCell":{"range":{"sheetId":0,"startRowIndex":11,"endRowIndex":12,"startColumnIndex":5,"endColumnIndex":6},
      "cell":{"userEnteredFormat":{"numberFormat":{"type":"NUMBER","pattern":"0%"}}},"fields":"userEnteredFormat"}},
    {"repeatCell":{"range":{"sheetId":0,"startRowIndex":11,"endRowIndex":12,"startColumnIndex":9,"endColumnIndex":10},
      "cell":{"userEnteredFormat":{"numberFormat":{"type":"NUMBER","pattern":"0%"}}},"fields":"userEnteredFormat"}}
  ]
}' > /dev/null


# ── Step 7: Data Validation ──────────────────────────────────────────────────
echo "  [7/9] Adding data validation…"

batch '{
  "requests": [
    {"setDataValidation":{"range":{"sheetId":1,"startRowIndex":1,"endRowIndex":1000,"startColumnIndex":2,"endColumnIndex":3},
      "rule":{"condition":{"type":"ONE_OF_RANGE","values":[{"userEnteredValue":"Reference!$A$2:$A$28"}]},"showCustomUi":true,"strict":true}}},
    {"setDataValidation":{"range":{"sheetId":1,"startRowIndex":1,"endRowIndex":1000,"startColumnIndex":4,"endColumnIndex":5},
      "rule":{"condition":{"type":"ONE_OF_LIST","values":[{"userEnteredValue":"Income"},{"userEnteredValue":"Side Income"},{"userEnteredValue":"Expense"}]},"showCustomUi":true,"strict":true}}},
    {"setDataValidation":{"range":{"sheetId":0,"startRowIndex":1,"endRowIndex":2,"startColumnIndex":2,"endColumnIndex":3},
      "rule":{"condition":{"type":"ONE_OF_RANGE","values":[{"userEnteredValue":"Reference!$D$2:$D$13"}]},"showCustomUi":true,"strict":true}}},
    {"setDataValidation":{"range":{"sheetId":2,"startRowIndex":6,"endRowIndex":9,"startColumnIndex":2,"endColumnIndex":3},
      "rule":{"condition":{"type":"NUMBER_BETWEEN","values":[{"userEnteredValue":"0"},{"userEnteredValue":"1"}]},"showCustomUi":true,"strict":false}}}
  ]
}' > /dev/null

# ── Step 8: Conditional Formatting ──────────────────────────────────────────
echo "  [8/9] Adding conditional formatting…"

batch '{
  "requests": [
    {"addConditionalFormatRule":{"rule":{"ranges":[{"sheetId":1,"startRowIndex":1,"endRowIndex":1000,"startColumnIndex":5,"endColumnIndex":6}],"booleanRule":{"condition":{"type":"TEXT_EQ","values":[{"userEnteredValue":"Needs"}]},"format":{"backgroundColor":{"red":0.847,"green":0.953,"blue":0.863}}}},"index":0}},
    {"addConditionalFormatRule":{"rule":{"ranges":[{"sheetId":1,"startRowIndex":1,"endRowIndex":1000,"startColumnIndex":5,"endColumnIndex":6}],"booleanRule":{"condition":{"type":"TEXT_EQ","values":[{"userEnteredValue":"Wants"}]},"format":{"backgroundColor":{"red":1.0,"green":0.953,"blue":0.804}}}},"index":0}},
    {"addConditionalFormatRule":{"rule":{"ranges":[{"sheetId":1,"startRowIndex":1,"endRowIndex":1000,"startColumnIndex":5,"endColumnIndex":6}],"booleanRule":{"condition":{"type":"TEXT_EQ","values":[{"userEnteredValue":"Savings & Debt"}]},"format":{"backgroundColor":{"red":0.961,"green":0.902,"blue":0.918}}}},"index":0}},
    {"addConditionalFormatRule":{"rule":{"ranges":[{"sheetId":1,"startRowIndex":1,"endRowIndex":1000,"startColumnIndex":4,"endColumnIndex":5}],"booleanRule":{"condition":{"type":"TEXT_EQ","values":[{"userEnteredValue":"Side Income"}]},"format":{"backgroundColor":{"red":1.0,"green":0.973,"blue":0.878}}}},"index":0}},
    {"addConditionalFormatRule":{"rule":{"ranges":[{"sheetId":2,"startRowIndex":10,"endRowIndex":11,"startColumnIndex":2,"endColumnIndex":3}],"booleanRule":{"condition":{"type":"CUSTOM_FORMULA","values":[{"userEnteredValue":"=C11<>1"}]},"format":{"backgroundColor":{"red":1.0,"green":0.867,"blue":0.824}}}},"index":0}},
    {"addConditionalFormatRule":{"rule":{"ranges":[{"sheetId":0,"startRowIndex":10,"endRowIndex":11,"startColumnIndex":1,"endColumnIndex":2}],"booleanRule":{"condition":{"type":"NUMBER_GREATER_THAN_EQ","values":[{"userEnteredValue":"0"}]},"format":{"backgroundColor":{"red":0.847,"green":0.953,"blue":0.863}}}},"index":0}},
    {"addConditionalFormatRule":{"rule":{"ranges":[{"sheetId":0,"startRowIndex":10,"endRowIndex":11,"startColumnIndex":1,"endColumnIndex":2}],"booleanRule":{"condition":{"type":"NUMBER_LESS","values":[{"userEnteredValue":"0"}]},"format":{"backgroundColor":{"red":1.0,"green":0.867,"blue":0.824}}}},"index":0}},
    {"addConditionalFormatRule":{"rule":{"ranges":[{"sheetId":0,"startRowIndex":10,"endRowIndex":11,"startColumnIndex":5,"endColumnIndex":6}],"booleanRule":{"condition":{"type":"NUMBER_GREATER_THAN_EQ","values":[{"userEnteredValue":"0"}]},"format":{"backgroundColor":{"red":0.847,"green":0.953,"blue":0.863}}}},"index":0}},
    {"addConditionalFormatRule":{"rule":{"ranges":[{"sheetId":0,"startRowIndex":10,"endRowIndex":11,"startColumnIndex":5,"endColumnIndex":6}],"booleanRule":{"condition":{"type":"NUMBER_LESS","values":[{"userEnteredValue":"0"}]},"format":{"backgroundColor":{"red":1.0,"green":0.867,"blue":0.824}}}},"index":0}},
    {"addConditionalFormatRule":{"rule":{"ranges":[{"sheetId":0,"startRowIndex":10,"endRowIndex":11,"startColumnIndex":9,"endColumnIndex":10}],"booleanRule":{"condition":{"type":"NUMBER_GREATER_THAN_EQ","values":[{"userEnteredValue":"0"}]},"format":{"backgroundColor":{"red":0.847,"green":0.953,"blue":0.863}}}},"index":0}},
    {"addConditionalFormatRule":{"rule":{"ranges":[{"sheetId":0,"startRowIndex":10,"endRowIndex":11,"startColumnIndex":9,"endColumnIndex":10}],"booleanRule":{"condition":{"type":"NUMBER_LESS","values":[{"userEnteredValue":"0"}]},"format":{"backgroundColor":{"red":1.0,"green":0.867,"blue":0.824}}}},"index":0}},
    {"addConditionalFormatRule":{"rule":{"ranges":[{"sheetId":0,"startRowIndex":5,"endRowIndex":6,"startColumnIndex":8,"endColumnIndex":9}],"booleanRule":{"condition":{"type":"NUMBER_GREATER_THAN_EQ","values":[{"userEnteredValue":"1"}]},"format":{"backgroundColor":{"red":0.847,"green":0.953,"blue":0.863}}}},"index":0}},
    {"addConditionalFormatRule":{"rule":{"ranges":[{"sheetId":0,"startRowIndex":5,"endRowIndex":6,"startColumnIndex":8,"endColumnIndex":9}],"booleanRule":{"condition":{"type":"NUMBER_LESS","values":[{"userEnteredValue":"0.8"}]},"format":{"backgroundColor":{"red":1.0,"green":0.867,"blue":0.824}}}},"index":0}}
  ]
}' > /dev/null

# ── Step 9: Named Ranges ─────────────────────────────────────────────────────
echo "  [9/9] Adding named ranges and charts…"

batch '{
  "requests": [
    {"addNamedRange":{"namedRange":{"name":"INCOME_TARGET",      "range":{"sheetId":2,"startRowIndex":2,"endRowIndex":3,"startColumnIndex":2,"endColumnIndex":3}}}},
    {"addNamedRange":{"namedRange":{"name":"SIDE_INCOME_TARGET", "range":{"sheetId":2,"startRowIndex":3,"endRowIndex":4,"startColumnIndex":2,"endColumnIndex":3}}}},
    {"addNamedRange":{"namedRange":{"name":"NEEDS_PCT",          "range":{"sheetId":2,"startRowIndex":6,"endRowIndex":7,"startColumnIndex":2,"endColumnIndex":3}}}},
    {"addNamedRange":{"namedRange":{"name":"WANTS_PCT",          "range":{"sheetId":2,"startRowIndex":7,"endRowIndex":8,"startColumnIndex":2,"endColumnIndex":3}}}},
    {"addNamedRange":{"namedRange":{"name":"SAVINGS_PCT",        "range":{"sheetId":2,"startRowIndex":8,"endRowIndex":9,"startColumnIndex":2,"endColumnIndex":3}}}},
    {"addNamedRange":{"namedRange":{"name":"SELECTED_MONTH",     "range":{"sheetId":0,"startRowIndex":1,"endRowIndex":2,"startColumnIndex":2,"endColumnIndex":3}}}}
  ]
}' > /dev/null

# Charts
batch '{
  "requests": [
    {"addChart":{"chart":{"spec":{"title":"Spending by Bucket","pieChart":{"legendPosition":"RIGHT_LEGEND","pieHole":0.5,
      "domain":{"sourceRange":{"sources":[{"sheetId":0,"startRowIndex":8,"endRowIndex":11,"startColumnIndex":12,"endColumnIndex":13}]}},
      "series":{"sourceRange":{"sources":[{"sheetId":0,"startRowIndex":8,"endRowIndex":11,"startColumnIndex":13,"endColumnIndex":14}]}}}}},
      "position":{"overlayPosition":{"anchorCell":{"sheetId":0,"rowIndex":16,"columnIndex":0},"widthPixels":400,"heightPixels":300}}}}},
    {"addChart":{"chart":{"spec":{"title":"Target vs Actual by Bucket","basicChart":{"chartType":"COLUMN","legendPosition":"BOTTOM_LEGEND",
      "axis":[{"position":"BOTTOM_AXIS","title":"Bucket"},{"position":"LEFT_AXIS","title":"Amount ($)"}],
      "domains":[{"domain":{"sourceRange":{"sources":[{"sheetId":0,"startRowIndex":8,"endRowIndex":11,"startColumnIndex":15,"endColumnIndex":16}]}}}],
      "series":[
        {"series":{"sourceRange":{"sources":[{"sheetId":0,"startRowIndex":8,"endRowIndex":11,"startColumnIndex":16,"endColumnIndex":17}]}},"targetAxis":"LEFT_AXIS","color":{"red":0.176,"green":0.416,"blue":0.310}},
        {"series":{"sourceRange":{"sources":[{"sheetId":0,"startRowIndex":8,"endRowIndex":11,"startColumnIndex":17,"endColumnIndex":18}]}},"targetAxis":"LEFT_AXIS","color":{"red":0.251,"green":0.569,"blue":0.424}}
      ],"headerCount":1}},
      "position":{"overlayPosition":{"anchorCell":{"sheetId":0,"rowIndex":16,"columnIndex":4},"widthPixels":450,"heightPixels":300}}}}},
    {"addChart":{"chart":{"spec":{"title":"Income vs Expenses by Month","basicChart":{"chartType":"LINE","legendPosition":"TOP_LEGEND",
      "axis":[{"position":"BOTTOM_AXIS","title":"Month"},{"position":"LEFT_AXIS","title":"Amount ($)"}],
      "domains":[{"domain":{"sourceRange":{"sources":[{"sheetId":0,"startRowIndex":19,"endRowIndex":31,"startColumnIndex":12,"endColumnIndex":13}]}}}],
      "series":[
        {"series":{"sourceRange":{"sources":[{"sheetId":0,"startRowIndex":19,"endRowIndex":31,"startColumnIndex":13,"endColumnIndex":14}]}},"targetAxis":"LEFT_AXIS","color":{"red":0.106,"green":0.263,"blue":0.196}},
        {"series":{"sourceRange":{"sources":[{"sheetId":0,"startRowIndex":19,"endRowIndex":31,"startColumnIndex":14,"endColumnIndex":15}]}},"targetAxis":"LEFT_AXIS","color":{"red":0.914,"green":0.769,"blue":0.416}},
        {"series":{"sourceRange":{"sources":[{"sheetId":0,"startRowIndex":19,"endRowIndex":31,"startColumnIndex":15,"endColumnIndex":16}]}},"targetAxis":"LEFT_AXIS","color":{"red":0.710,"green":0.514,"blue":0.553}}
      ],"headerCount":1}},
      "position":{"overlayPosition":{"anchorCell":{"sheetId":0,"rowIndex":34,"columnIndex":0},"widthPixels":600,"heightPixels":280}}}}}
  ]
}' > /dev/null

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "✅ Build complete!"
echo "   Open your tracker: $URL"
echo ""
echo "   Default month shown: 2026-01"
echo "   Change in Dashboard!C2 to switch months."
