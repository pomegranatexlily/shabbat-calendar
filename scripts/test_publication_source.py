"""Validate canonical calendar JSON exists at both publication roots and matches the audit."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/".nojekyll").is_file(), "Pages root must deploy static content without Jekyll"
assert (ROOT/"index.html").is_file(), "Legacy Pages needs a working root entry point"
root=json.loads((ROOT/"calendar.json").read_text(encoding="utf-8"))
public=json.loads((ROOT/"public/calendar.json").read_text(encoding="utf-8"))
assert root==public, "Legacy and custom Pages must publish exactly the same canonical feed"
audit=json.loads((ROOT/"calendar-audit.json").read_text(encoding="utf-8"))
assert audit==json.loads((ROOT/"public/calendar-audit.json").read_text(encoding="utf-8"))
assert audit==root["verification"], "Audit must match both served calendar copies"
assert root["schema_version"]==2 and audit["version"]==1
assert audit["status"]=="planning_arithmetic_checked_not_observation_verified"
assert root["tracks"]["earlier"]["years"][0]["start_date"]=="2027-03-09"
assert root["tracks"]["later"]["years"][0]["start_date"]=="2027-04-07"
for track in root["tracks"].values():
    assert any(e["date"]=="2026-10-19" and e["kind"]=="sabbath" and
               e["lunar_day"]==8 for e in track["current_events"])
    assert all(e.get("rule_status")!="approved" for e in track["events"])
print("PASS: both Pages source roots have identical canonical calendar and source audit")
