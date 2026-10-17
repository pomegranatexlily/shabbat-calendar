"""Read-only calendar integrity audit — tests mathematics, NEVER certifies sightings.

Calendar planning inputs:
- supplied month starts are founder-provided civil dates, NOT verified observations
- projected starts are a mean-lunation model
- 2027 year starts are founder-designated planning anchors
- all configured festival mappings are draft, pending adjudication
"""
from datetime import date

def _d(s):
    return date.fromisoformat(s)

def audit_calendar(calendar, cfg):
    tracks = calendar["tracks"]
    if set(tracks) != {"earlier", "later"}:
        raise ValueError("Both calendar tracks required")
    supplied = {int(k):v for k,v in cfg["supplied_month_starts"].items()}
    lunar = {m["index"]:m for m in calendar["months"]}
    if any(lunar.get(k,{}).get("date") != v or lunar[k]["status"] != "supplied" for k,v in supplied.items()):
        raise ValueError("An original founder-supplied new moon changed")
    years_checked = 0
    months_checked = 0
    events_checked = 0
    for track_id,track in tracks.items():
        index = {m["month_index"]:m for m in track["months"]+track["current_months"]}
        all_events = track["events"] + track["current_events"]
        ids=set()
        for month in index.values():
            days=(_d(month["end"])-_d(month["start"])).days+1
            if days not in (29,30) or days!=month["days"]:
                raise ValueError(f"{track_id}: invalid month length")
            months_checked+=1
        for event in all_events:
            if event["id"] in ids:
                raise ValueError(f"{track_id}: duplicate event ID")
            ids.add(event["id"])
            moon=index.get(event["month_index"])
            if moon is None:
                raise ValueError(f"{track_id}: missing month for event")
            expected=(_d(event["date"])-_d(moon["start"])).days+1
            if expected!=event["lunar_day"] or not 1<=expected<=moon["days"]:
                raise ValueError(f"{track_id}: impossible event lunar day")
            if event["kind"]=="sabbath" and expected not in (8,15,22,29):
                raise ValueError(f"{track_id}: Shabbat outside lunar Sabbath days")
            if event["kind"]=="new_moon" and expected!=1:
                raise ValueError(f"{track_id}: New Moon not day 1")
            if event["kind"]=="feast" and event.get("rule_status")!="unapproved_draft":
                raise ValueError("Track feast appears approved without founder ruling")
            events_checked+=1
        for year in track["years"]:
            length=sum(m["year"]==year["year"] for m in track["months"])
            if length!=year["month_count"] or length not in (12,13) or year["has_13th_month"]!=(length==13):
                raise ValueError(f"{track_id}: intercalation classification mismatch")
            years_checked+=1
        if not any(e["date"]=="2026-10-19" and e["kind"]=="sabbath" and e["lunar_day"]==8
                   for e in track["current_events"]):
            raise ValueError("Current supplied October 19 Shabbat missing")
    a=tracks["earlier"]["years"][0]["start_date"]
    b=tracks["later"]["years"][0]["start_date"]
    designated=cfg.get("track_year_starts",{}).get("2027",{})
    if designated.get("earlier")!=a or designated.get("later")!=b:
        raise ValueError("Founder-designated 2027 start dates changed")
    if (a,b)!=("2027-03-09","2027-04-07"):
        raise ValueError("Unexpected 2027 approved planning anchor pair")
    return {
        "version":1,
        "status":"planning_arithmetic_checked_not_observation_verified",
        "verified_2027_planning_year_starts":{"earlier":a,"later":b},
        "2027_year_starts_observed":False,
        "source_start_dates":"founder_supplied_date_not_independently_observed",
        "future_dates":"mean_lunation_and_equinox_planning_model_not_ephemeris",
        "checks":{"lunar_months_checked":months_checked,
                  "year_span_classifications_checked":years_checked,
                  "event_positions_checked":events_checked,
                  "supplied_start_dates_preserved":len(supplied),
                  "parallel_tracks_month_offset":1,
                  "2026_10_19_day8_shabbat":True},
        "unresolved":{
            "local_crescent_visibility":"not_verified",
            "local_sunset_boundaries":"not_established",
            "Abib_or_agricultural_evidence":"not_supplied",
            "annual_feast_rule_approval":"not_approved",
            "intercalation_policy":"provisional_seasonal_model",
            "Shavuot_counting":"not_selected",
            "makeup_rules":"not_approved_no_automatic_second_shift",
            "historical_2026_year_numbering":"not_reconciled",
        },
        "feast_rule_status":"unapproved_draft",
        "date_assurance":"Planning only; not a certified religious observance or independently verified astronomical observation.",
    }
