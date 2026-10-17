"""Provisional seasonal intercalation based on equinox + supplied lunar month starts.

A 13th lunar month is inserted ONLY when the next spring-aligned year start
requires 13 lunations. This is separate from Jubilee, annual feast rulings,
and a claim to have observed the first crescent or agricultural barley.

The equinox calculation is a tropical-year *approximation*, anchored to the
published 2027 astronomical March equinox at 2027-03-20 20:24 UTC, with
365.2422 days per tropical year. It is not an ephemeris. Its date-level
accuracy should be independently checked when applying a future year.
References: https://www.timeanddate.com/calendar/seasons.html?n=1440
            https://www.weather.gov/dvn/Climate_Astronomical_Seasons
"""
from datetime import date, datetime, timedelta, timezone

TROPICAL_YEAR_DAYS = 365.2422
EQUINOX_REFERENCE = datetime(2027, 3, 20, 20, 24, tzinfo=timezone.utc)


def projected_spring_equinox(year):
    if not 2000 <= year <= 2100:
        raise ValueError("Reference equinox approximation supports years 2000–2100 only")
    return EQUINOX_REFERENCE + timedelta(days=TROPICAL_YEAR_DAYS * (year - 2027))


def seasonal_years(months, start_year, end_year):
    """Return 12-/13-month lunar-year planning classifications.

    The year begins at the first recorded/projected monthly Day 1 falling on
    or after the *UTC civil date* of the March equinox. A different chosen
    sunset/location threshold may move borderline decisions; never label
    this method a verified local first-visible-crescent observation.
    """
    ordered = sorted(months, key=lambda m: m["index"])
    by_index = {m["index"]: m for m in ordered}
    if len(by_index) != len(ordered):
        raise ValueError("Duplicate lunar month index")
    for a, b in zip(ordered, ordered[1:]):
        if b["index"] != a["index"] + 1:
            raise ValueError("Missing lunar month index; refusing to infer length")
        delta = (date.fromisoformat(b["date"]) - date.fromisoformat(a["date"])).days
        if delta not in (29, 30):
            raise ValueError("Lunar month boundaries must be 29 or 30 days apart")
    chosen = {}
    for year in range(start_year, end_year + 2):
        equinox = projected_spring_equinox(year)
        threshold = equinox.date().isoformat()
        candidates = [m for m in ordered if m["date"] >= threshold]
        if not candidates:
            raise ValueError(f"Missing month following {year} equinox; extend projection horizon")
        chosen[year] = {"year": year, "start": candidates[0], "equinox": equinox}

    records = []
    for year in range(start_year, end_year + 1):
        first, next_first = chosen[year]["start"], chosen[year + 1]["start"]
        count = next_first["index"] - first["index"]
        if count not in (12, 13):
            raise ValueError(f"{year}: lunar year cannot be {count} months under the configured rule")
        intercalary = by_index.get(next_first["index"] - 1) if count == 13 else None
        rec = {
            "year": year, "first_month_start": first["date"],
            "next_first_month_start": next_first["date"],
            "month_count": count, "has_13th_month": count == 13,
            "thirteenth_month_start": intercalary["date"] if intercalary else None,
            "start_month_index": first["index"],
            "next_start_month_index": next_first["index"],
            "march_equinox_utc_estimate": chosen[year]["equinox"].isoformat().replace("+00:00", "Z"),
            "selection_rule": "first_projected_lunar_month_start_on_or_after_utc_march_equinox_date",
            "status": "planning_projection",
            "year_start_month_status": first["status"],
            "astronomical_precision": "mean_tropical_year_estimate_not_an_ephemeris",
        }
        records.append(rec)
    return records


def annotate_months(months, records):
    """Tag month number and intercalary flags; never change supplied dates."""
    for m in months:
        match = next((r for r in records if r["start_month_index"] <= m["index"] < r["next_start_month_index"]), None)
        if match is None:
            continue
        m["seasonal_year"] = match["year"]
        m["month_of_seasonal_year"] = m["index"] - match["start_month_index"] + 1
        m["is_intercalary"] = m["month_of_seasonal_year"] == 13
    return months
