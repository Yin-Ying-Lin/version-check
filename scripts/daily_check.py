# -*- coding: utf-8 -*-
"""
Standalone daily entry point, meant to be run by Windows Task Scheduler.
No Claude / LLM involvement, no token cost. Runs the diff, and shows a
native Windows toast notification when the user should know something.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diff_and_update import run, PRODUCTS  # noqa: E402

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOAST_SCRIPT = os.path.join(SCRIPT_DIR, "notify_toast.ps1")


def toast(title, message):
    # PowerShell string literals: escape backticks and double quotes
    def esc(s):
        return s.replace("`", "``").replace('"', '`"')

    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", TOAST_SCRIPT,
            "-Title", esc(title),
            "-Message", esc(message),
        ],
        capture_output=True,
    )


def main():
    changed, stale, no_source = [], [], []
    for name in PRODUCTS:
        status, lines = run(name)
        if status == "CHANGED":
            changed.append((name, lines))
        elif status == "STALE":
            stale.append(name)
        elif status == "NO_SOURCE":
            no_source.append(name)

    if changed:
        parts = []
        for name, lines in changed:
            parts.append(f"{name}: " + "; ".join(lines))
        msg = " | ".join(parts)
        if len(msg) > 250:
            msg = msg[:247] + "..."
        toast("ASRock 版本有更新", msg)

    if stale or no_source:
        todo = stale + no_source
        toast(
            "ASRock 版本檢查提醒",
            "今天還沒另存網頁快照: " + ", ".join(todo) + " (見 watch/README.txt)",
        )

    # TODO: once an SMTP / Graph API credential is available, also send an
    # email here for the CHANGED case, independent of Claude connectors.


if __name__ == "__main__":
    main()
