# -*- coding: utf-8 -*-
"""
Parse an ASRock product page saved locally (browser "Save As -> Webpage, Complete")
and extract Utility / Driver / BIOS version info.

Usage (as a module):
    from parse_page import parse_product_page
    data = parse_product_page(html_path)
    # data = {
    #   "utility": [{"key":..., "name":..., "os":..., "beta":..., "version":..., "date":...}, ...],
    #   "driver":  [... same shape ...],
    #   "bios":    [{"key":..., "version":..., "date":..., "size":...}, ...],
    # }
"""
import re


def _extract_table_block(html, section_id, next_id):
    start = html.find('id="%s"' % section_id)
    if start == -1:
        # try with a trailing space variant used by some pages
        start = html.find('id="%s" ' % section_id)
    if start == -1:
        return None
    end = html.find('id="%s"' % next_id, start)
    if end == -1:
        end = len(html)
    chunk = html[start:end]
    tstart = chunk.find("<table")
    if tstart == -1:
        return None
    tend = chunk.find("</table>", tstart)
    if tend == -1:
        return None
    tend += len("</table>")
    return chunk[tstart:tend]


_ROW_RE = re.compile(r"<tr\b([^>]*)>(.*?)</tr>", re.DOTALL)
_TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_VER_RE = re.compile(r"版本[:：]\s*([^\s<]+)")


def _clean(text):
    text = re.sub(r"<br\s*/?>", " | ", text)
    text = _TAG_RE.sub("", text)
    text = text.replace("&amp;", "&").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _row_classes(attrs):
    m = re.search(r'class="([^"]*)"', attrs)
    return set(m.group(1).split()) if m else set()


def parse_download_table(table_html):
    """Download section: combined Utility + Driver rows (3rd-party rows have no version)."""
    items = []
    if not table_html:
        return items
    for m in _ROW_RE.finditer(table_html):
        attrs, row_html = m.group(1), m.group(2)
        if "spechromeItem" in attrs:
            continue  # Chrome install row, not product software
        classes = _row_classes(attrs)
        tds = _TD_RE.findall(row_html)
        if len(tds) < 4:
            continue
        desc_raw = tds[0]
        desc = _clean(desc_raw)
        date = _clean(tds[3])
        # match on the raw (tag-containing) text so a following <div>/<font> tag
        # reliably terminates the version token, even with no whitespace before it
        vm = _VER_RE.search(desc_raw)
        version = vm.group(1) if vm else "N/A"
        if vm:
            name = _clean(desc_raw[: desc_raw.find(vm.group(0))]).strip()
        else:
            name = desc.split(" | ")[0].strip()
        name = re.sub(r"^\[Beta\]\s*", "", name).strip()
        name = name.split("*Third-party")[0].strip()
        os_tag = ""
        if "osW1064" in classes:
            os_tag += "Win10"
        if "osW1164" in classes:
            os_tag += "+Win11" if os_tag else "Win11"
        beta = "Beta" in classes
        key = f"{name}|{os_tag}|{'Beta' if beta else 'Stable'}"
        items.append(
            {
                "key": key,
                "name": name,
                "os": os_tag,
                "beta": beta,
                "version": version,
                "date": date,
            }
        )
    return items


# Utility vs Driver vs 3rd-party is not separable from the Download table structurally;
# classification mirrors the manual categorisation already used for the existing workbook.
UTILITY_NAME_HINTS = [
    "ASRock Motherboard", "APP Shop", "Nahimic", "Restart to UEFI",
    "Polychrome", "Blazing OC Tuner", "Norton 360", "SignalRGB",
]


def split_utility_driver(items):
    utility, driver = [], []
    for it in items:
        if any(hint in it["name"] for hint in UTILITY_NAME_HINTS):
            utility.append(it)
        else:
            driver.append(it)
    return utility, driver


def parse_bios_table(table_html):
    items = []
    if not table_html:
        return items
    for m in _ROW_RE.finditer(table_html):
        row_html = m.group(2)
        tds = _TD_RE.findall(row_html)
        if len(tds) < 3:
            continue
        version = _clean(tds[0])
        beta = "[Beta]" in tds[0]
        version = version.replace("| [Beta]", "").replace("[Beta]", "").strip()
        date = _clean(tds[1])
        size = _clean(tds[2])
        items.append(
            {
                "key": version,
                "version": version,
                "date": date,
                "size": size,
                "beta": beta,
            }
        )
    return items


def parse_product_page(html_path):
    with open(html_path, encoding="utf-8", errors="ignore") as f:
        html = f.read()

    download_html = _extract_table_block(html, "Download", "BIOS")
    bios_html = _extract_table_block(html, "BIOS", "Manual")

    dl_items = parse_download_table(download_html)
    utility, driver = split_utility_driver(dl_items)
    bios = parse_bios_table(bios_html)

    return {"utility": utility, "driver": driver, "bios": bios}


if __name__ == "__main__":
    import sys
    import json

    path = sys.argv[1]
    result = parse_product_page(path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
