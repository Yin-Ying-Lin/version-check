# -*- coding: utf-8 -*-
"""
Compare a freshly-saved ASRock product page against the stored baseline (state.json),
update the baseline and the Excel workbook when versions changed, and report what changed.

Usage:
    python diff_and_update.py "X870E Taichi"
    python diff_and_update.py "Z890 Taichi"
    python diff_and_update.py --all

Exit behaviour (stdout, machine-parseable "RESULT:" line at the end):
    RESULT:NO_SOURCE   -> watch/<product>/<product>.html not found yet
    RESULT:NO_CHANGE   -> parsed but identical to stored baseline
    RESULT:CHANGED     -> differences found, workbook + state.json updated
"""
import json
import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_page import parse_product_page  # noqa: E402

import openpyxl  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_PATH = os.path.join(ROOT, "scripts", "state.json")
XLSX_PATH = os.path.join(ROOT, "Taichi_Driver_Utility_BIOS_Versions.xlsx")

PRODUCTS = {
    "X870E Taichi": {
        "html": os.path.join(ROOT, "watch", "X870E Taichi", "X870E Taichi.html"),
        "sheet": "X870E Taichi",
    },
    "Z890 Taichi": {
        "html": os.path.join(ROOT, "watch", "Z890 Taichi", "Z890 Taichi.html"),
        "sheet": "Z890 Taichi",
    },
}


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def index_by_key(items):
    return {it["key"]: it for it in items}


def data_order_index(items, key):
    for i, it in enumerate(items):
        if it["key"] == key:
            return i
    return len(items)


def diff_section(old_items, new_items):
    """Return list of (change_type, key, old, new)."""
    old_idx = index_by_key(old_items)
    new_idx = index_by_key(new_items)
    changes = []
    for key, new_it in new_idx.items():
        old_it = old_idx.get(key)
        if old_it is None:
            changes.append(("added", key, None, new_it))
        elif old_it.get("version") != new_it.get("version"):
            changes.append(("version_changed", key, old_it, new_it))
    for key, old_it in old_idx.items():
        if key not in new_idx:
            changes.append(("removed", key, old_it, None))
    return changes


def _section_bounds(ws, section_title):
    """Return (header_row, data_start_row, data_end_row_exclusive) for a titled section.
    Column E (5) holds the MatchKey used for lookups; column A holds the section title
    on its own header row, then one column-header row, then data rows until a blank A cell.
    """
    header_row = None
    for row in ws.iter_rows(min_row=1, max_col=1):
        if row[0].value == section_title:
            header_row = row[0].row
            break
    if header_row is None:
        return None
    data_start = header_row + 2  # skip the section title row and the column-header row
    r = data_start
    while ws.cell(row=r, column=1).value is not None:
        r += 1
    return header_row, data_start, r  # end is exclusive


def update_xlsx_cell_by_key(ws, section_title, key, new_version=None, new_date=None):
    """Find the row under `section_title` whose MatchKey (col E) matches `key` and update it."""
    bounds = _section_bounds(ws, section_title)
    if bounds is None:
        return False
    _, data_start, data_end = bounds
    for r in range(data_start, data_end):
        if ws.cell(row=r, column=5).value == key:
            if section_title == "BIOS":
                if new_date is not None:
                    ws.cell(row=r, column=2, value=new_date)
            else:
                if new_version is not None:
                    ws.cell(row=r, column=2, value=new_version)
                if new_date is not None:
                    ws.cell(row=r, column=3, value=new_date)
            return True
    return False


def insert_new_bios_rows(ws, new_items):
    """Insert newly-released BIOS versions at the top of the BIOS data block,
    preserving the newest-first order already present in `new_items`."""
    bounds = _section_bounds(ws, "BIOS")
    if bounds is None or not new_items:
        return
    _, data_start, _ = bounds
    ws.insert_rows(data_start, amount=len(new_items))
    for offset, it in enumerate(new_items):
        r = data_start + offset
        note = "Beta" if it.get("beta") else ""
        ws.cell(row=r, column=1, value=it["version"])
        ws.cell(row=r, column=2, value=it["date"])
        ws.cell(row=r, column=3, value=it.get("size", ""))
        ws.cell(row=r, column=4, value=note)
        ws.cell(row=r, column=5, value=it["key"])


def refresh_bios_latest_note(ws):
    """Keep the '最新版' label on the first non-beta row of the BIOS block, and only there."""
    bounds = _section_bounds(ws, "BIOS")
    if bounds is None:
        return
    _, data_start, data_end = bounds
    marked = False
    for r in range(data_start, data_end):
        note = ws.cell(row=r, column=4).value or ""
        is_beta = "Beta" in note
        if not marked and not is_beta:
            ws.cell(row=r, column=4, value="最新版")
            marked = True
        elif note == "最新版":
            ws.cell(row=r, column=4, value="")


def run(product_name):
    cfg = PRODUCTS[product_name]
    if not os.path.exists(cfg["html"]):
        print(f"[{product_name}] watch file not found: {cfg['html']}")
        print("RESULT:NO_SOURCE")
        return "NO_SOURCE", []

    mtime_date = datetime.date.fromtimestamp(os.path.getmtime(cfg["html"]))
    today = datetime.date.today()
    state = load_state()
    if mtime_date != today and product_name in state:
        print(
            f"[{product_name}] 存檔不是今天存的 (檔案日期 {mtime_date.isoformat()}), "
            "尚未比對, 提醒使用者今天記得另存新檔。"
        )
        print("RESULT:STALE")
        return "STALE", []

    new_data = parse_product_page(cfg["html"])
    old_data = state.get(product_name)

    if old_data is None:
        state[product_name] = new_data
        state.setdefault("_meta", {})[product_name] = {
            "last_checked": datetime.date.today().isoformat()
        }
        save_state(state)
        print(f"[{product_name}] no baseline existed yet; stored current snapshot as baseline.")
        print("RESULT:NO_CHANGE")
        return "NO_CHANGE", []

    all_changes = []
    for section in ("utility", "driver", "bios"):
        changes = diff_section(old_data.get(section, []), new_data.get(section, []))
        for ch in changes:
            all_changes.append((section,) + ch)

    state.setdefault("_meta", {})[product_name] = {
        "last_checked": datetime.date.today().isoformat()
    }

    if not all_changes:
        save_state(state)
        print(f"[{product_name}] checked, no version changes.")
        print("RESULT:NO_CHANGE")
        return "NO_CHANGE", []

    # update workbook
    wb = openpyxl.load_workbook(XLSX_PATH)
    ws = wb[cfg["sheet"]]
    report_lines = []
    new_bios_items = []
    for section, change_type, key, old_it, new_it in all_changes:
        if section == "bios":
            if change_type == "added":
                new_bios_items.append(new_it)
                report_lines.append(f"[BIOS] 新版本 {new_it['version']} ({new_it['date']})")
            elif change_type == "version_changed":
                update_xlsx_cell_by_key(ws, "BIOS", key, new_date=new_it["date"])
                report_lines.append(f"[BIOS] {key}: 日期由 {old_it['date']} 更新為 {new_it['date']}")
            elif change_type == "removed":
                report_lines.append(f"[BIOS] 官網上已看不到版本 {key}  [表格內資料予以保留, 請手動確認]")
            continue
        label = "Utility" if section == "utility" else "Driver"
        if change_type == "version_changed":
            ok = update_xlsx_cell_by_key(ws, label, key, new_it["version"], new_it["date"])
            report_lines.append(
                f"[{label}] {new_it['name']} ({new_it['os']}): "
                f"{old_it['version']} -> {new_it['version']} ({new_it['date']})"
                + ("" if ok else "  [workbook row not matched, please check manually]")
            )
        elif change_type == "added":
            report_lines.append(
                f"[{label}] 新增項目 {new_it['name']} ({new_it['os']}) 版本 {new_it['version']}"
                "  [未自動加入表格, 請手動新增一列]"
            )
        elif change_type == "removed":
            report_lines.append(
                f"[{label}] 官網已移除 {old_it['name']} ({old_it['os']})  [表格內資料予以保留, 請手動確認]"
            )

    if new_bios_items:
        # newest-first, matching the page's own ordering
        new_bios_items.sort(key=lambda it: data_order_index(new_data["bios"], it["key"]))
        insert_new_bios_rows(ws, new_bios_items)
    if new_bios_items or any(c[0] == "bios" and c[1] == "version_changed" for c in all_changes):
        refresh_bios_latest_note(ws)

    wb.save(XLSX_PATH)
    state[product_name] = new_data
    save_state(state)

    print(f"[{product_name}] {len(all_changes)} change(s) found and workbook updated:")
    for line in report_lines:
        print("  - " + line)
    print("RESULT:CHANGED")
    return "CHANGED", report_lines


if __name__ == "__main__":
    args = sys.argv[1:]
    targets = list(PRODUCTS.keys()) if (not args or args[0] == "--all") else args
    changed, stale, no_source = [], [], []
    for name in targets:
        status, lines = run(name)
        if status == "CHANGED":
            changed.append((name, lines))
        elif status == "STALE":
            stale.append(name)
        elif status == "NO_SOURCE":
            no_source.append(name)

    print("\n=== SUMMARY ===")
    if changed:
        print("版本有更新 (CHANGED):")
        for name, lines in changed:
            print(f"{name}:")
            for l in lines:
                print("  " + l)
    if stale:
        print("今天尚未另存新檔 (STALE), 提醒: " + ", ".join(stale))
    if no_source:
        print("找不到存檔 (NO_SOURCE, 從未存過), 提醒: " + ", ".join(no_source))
    if not changed and not stale and not no_source:
        print("今天已檢查最新存檔, 沒有版本變動。")
