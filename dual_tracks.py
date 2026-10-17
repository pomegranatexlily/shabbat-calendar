"""Two parallel Israelite-year planning tracks derived from one lunar month series.

Earlier year starts at the projected new moon immediately BEFORE the
spring-aligned later calendar's year start. Both use the same physical moon
beginnings, but name the months one lunar month apart. The user explicitly
designated 2027-03-09 and 2027-04-07 as the provisional 2027 starts.

Annual feast labels come from draft config rules: they are NOT ratified
observances. A second, automatic 'makeup' shift must NOT be applied inside
each track, or two parallel calendars would be counted four times.
"""
from datetime import date, timedelta
import uuid

SHABBAT_DAYS = (8, 15, 22, 29)
TRACKS = {
    "earlier": {
        "label": "Earlier calendar",
        "description": "Religious year begins one lunar New Moon ahead of the later spring-aligned year.",
        "relationship": "one_lunar_month_earlier",
    },
    "later": {
        "label": "Later calendar",
        "description": "Religious year begins on the first projected lunar New Moon on/after the March equinox.",
        "relationship": "first_lunar_month_after_spring_equinox",
    },
}


def _date(s):
    return date.fromisoformat(s)


def _uid(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "shabbat-calendar/v2/" + "/".join(map(str, parts))))


def create_tracks(months, later_years, config):
    """Generate independent month numbers, lunar Shabbats, and DRAFT feasts."""
    by_index = {m["index"]: m for m in months}
    if len(by_index) != len(months):
        raise ValueError("Nonunique source month indices")
    overrides = config.get("track_year_starts", {})
    if overrides:
        assert isinstance(overrides, dict)

    # Year-by-year later and earlier starts must follow the SAME lunar series.
    later = {r["year"]: r["start_month_index"] for r in later_years}
    final_year = max(later)
    # Last-year next-start comes from the last seasonal-year record.
    later[final_year + 1] = later_years[-1]["next_start_month_index"]
    tracks = {}

    for track_id, info in TRACKS.items():
        offset = -1 if track_id == "earlier" else 0
        starts = {y: idx + offset for y, idx in later.items()}
        records, numbered, events = [], [], []
        for year in range(config["start_year"], config["end_year"] + 1):
            start_idx, next_idx = starts[year], starts[year + 1]
            start, following = by_index[start_idx], by_index[next_idx]
            length = next_idx - start_idx
            if length not in (12, 13):
                raise ValueError(f"{track_id}/{year} invalid {length}-month year")

            # Store explicit designated start dates without treating them as an
            # observed crescent or silently altering the supplied lunar series.
            designated = overrides.get(str(year), {}).get(track_id)
            if designated and designated != start["date"]:
                raise ValueError(f"{track_id}/{year}: designation {designated} disagrees with lunar month {start['date']}")
            label = "user_designated_projection" if designated else "modeled_projection"
            thirteenth = by_index[next_idx - 1]["date"] if length == 13 else None
            records.append({
                "year": year,
                "start_date": start["date"],
                "next_start_date": following["date"],
                "start_month_index": start_idx,
                "next_start_month_index": next_idx,
                "month_count": length,
                "has_13th_month": length == 13,
                "thirteenth_month_start": thirteenth,
                "status": label,
                "is_observed": False,
            })
            year_months = []
            for i in range(start_idx, next_idx):
                moon, next_moon = by_index[i], by_index[i + 1]
                count = (_date(next_moon["date"]) - _date(moon["date"])).days
                if count not in (29, 30):
                    raise ValueError("Non-lunar month length")
                m = {
                    "year": year,
                    "month": i - start_idx + 1,
                    "start": moon["date"],
                    "end": (_date(next_moon["date"]) - timedelta(days=1)).isoformat(),
                    "days": count,
                    "month_index": i,
                    "status": moon["status"],
                    "is_thirteenth": i - start_idx == 12,
                }
                year_months.append(m)
                numbered.append(m)
                for day, title, kind in [
                    (1, "New Moon", "new_moon"),
                    *[(d - 1, "Preparation for Shabbat", "preparation") for d in SHABBAT_DAYS],
                    *[(d, "Shabbat", "sabbath") for d in SHABBAT_DAYS],
                ]:
                    if day > count:
                        continue
                    when = (_date(m["start"]) + timedelta(days=day - 1)).isoformat()
                    events.append({
                        "id": _uid(track_id, year, i, day, kind),
                        "date": when, "title": title, "kind": kind,
                        "track": track_id, "year": year, "month": m["month"],
                        "lunar_day": day, "month_index": i, "status": moon["status"],
                        "rule_status": "user_calendar_day_pattern",
                        "source": "projected_lunar_series" if moon["status"] == "projected" else "user_supplied_month_start",
                    })

            for rule in config.get("feast_rules", []):
                if not 1 <= rule["month"] <= length:
                    raise ValueError("Feast month not in lunar-year span")
                if not 1 <= rule["day"] <= 30 or not 1 <= rule.get("duration", 1) <= 10:
                    raise ValueError("Invalid draft feast rule")
                target = year_months[rule["month"] - 1]
                for offset_day in range(rule.get("duration", 1)):
                    when = _date(target["start"]) + timedelta(days=rule["day"] - 1 + offset_day)
                    # A multiday feast may cross a month boundary. Compute the
                    # ACTUAL lunar day rather than writing day 32 into a month.
                    actual = next((m for m in year_months if m["start"] <= when.isoformat() <= m["end"]), None)
                    if actual is None:
                        # Example: the draft ends beyond the last month of year.
                        continue
                    title = rule["name"]
                    if rule.get("duration", 1) > 1:
                        title += f" (Day {offset_day + 1})"
                    events.append({
                        "id": _uid(track_id, year, rule["name"], offset_day, "feast_draft"),
                        "date": when.isoformat(), "title": title, "kind": "feast",
                        "track": track_id, "year": year, "month": actual["month"],
                        "lunar_day": (_date(when.isoformat()) - _date(actual["start"])).days + 1,
                        "month_index": actual["month_index"], "status": "projected",
                        "rule_status": "unapproved_draft",
                        "source": "config.feast_rules",
                    })

        events.sort(key=lambda e: (e["date"], e["kind"], e["title"]))
        if len({e["id"] for e in events}) != len(events):
            raise AssertionError("Duplicate track event identifiers")
        tracks[track_id] = {
            "id": track_id, **info, "years": records, "months": numbered,
            "events": events,
            "feasts_status": "DRAFT_PROJECTIONS_NOT_APPROVED",
            "lunar_visibility": "NOT_VERIFIED",
        }

    # Track independence: identical astronomical new moons, but year names
    # and numbered lunar days differ. Every later start = earlier month 2.
    for year in range(config["start_year"], config["end_year"] + 1):
        early = tracks["earlier"]["years"][year - config["start_year"]]
        late = tracks["later"]["years"][year - config["start_year"]]
        if late["start_month_index"] != early["start_month_index"] + 1:
            raise AssertionError("Calendar tracks must be one lunar month apart")
        if early["month_count"] != late["month_count"]:
            raise AssertionError("Parallel calendar year lengths disagree")

    return tracks
