# Shabbat Calendar

Shared calendar engine for a Shabbat website, Apple Calendar feeds, and Bible-app JSON data.

## Status
This is a planning scaffold, not a verified future feast calendar. Supplied dates remain distinct from projections. Future month starts use a mean-lunation interval, NOT actual crescent visibility. The engine generates two independently numbered seasonal years separated by one lunar month. Its legacy event feed withholds annual feasts until separately approved Abib anchors are supplied; the two-track planning feeds include clearly labeled DRAFT feast projections from config rules, not approved observances. Shavuot remains pending an explicit counting rule. Draft feast mappings and makeup switches require review.

## Two parallel Israelite calendar tracks

As designated by the founder for the 2027 planning model:

| | Earlier track | Later track |
|---|---|---|
| Year 2027 begins (New Moon / Month 1 Day 1) | 2027-03-09 | 2027-04-07 |
| First Shabbat (Month 1 Day 8) | 2027-03-16 | 2027-04-14 |
| Passover, DRAFT Day 14 rule (unapproved) | 2027-03-22 | 2027-04-20 |
| 2028 13th month begins, projected | 2029-02-14 | 2029-03-16 |

These tracks use **the same series of astronomical month starts** but assign different Israelite **year and month numbers**. The April 7 New Moon is Earlier Month 2 Day 1 and Later Month 1 Day 1. Their feast dates are independently derived from each track's Month 1; makeup month shifts are **not added again**, which would double-count observances.

Both tracks use Day 1 = New Moon and Shabbat days 8, 15, 22, 29. The adjacent preparation days are 7, 14, 21, 28. Each 2027 anchor is user-designated as a **planning year start**, not an observed crescent. Subsequent years and 13th-month placement use the equinox/lunation planning model. No Jubilee association is inferred. The supplied October 2026–February 2027 month starts and Purim notes remain unchanged, and older 2024–2025 records have not yet been reconciled.

Annual feast labels in the dual-track feeds follow **unapproved** `config.feast_rules` for **planning only**, with `rule_status: unapproved_draft`. The original `events` feed continues to withhold unapproved annual feasts and preserves supplied dated observances. Shavuot still requires a confirmed counting rule. Do not present draft dates as religious determinations.

The daily GitHub build keeps a **rolling eight-year horizon** (via `rolling_years_ahead`) beyond the current UTC year, so the generated CSV/JSON/ICS files keep extending automatically as years pass. This does **not** turn mean-lunation forecasts into verified sightings. Historical anchors are never overwritten. Tests of the fixed 2027–2030 sample configuration remain deterministic.

The public website at https://pomegranatexlily.github.io/shabbat-calendar/ displays an interactive seven-column Gregorian month grid, a two-track toggle, lunar month/day labels, 12-/13-month summaries, and event details. The full JSON is available at https://pomegranatexlily.github.io/shabbat-calendar/calendar.json for Oustory or other apps.

Verification: `python -m unittest -v test_intercalation.py test_dual_tracks.py`.

## Release 3 verification audit

Every generated `calendar.json` now includes a machine-readable `verification` object, also exported as `public/calendar-audit.json`. It checks all published 29/30-day lunar spans, Day 1/8/15/22/29 event positions, the current October 19, 2026 Day 8 Shabbat, duplicate identifiers, the March 9/April 7, 2027 planning year starts, and 12/13-month classification. Invalid arithmetic or an unauthorized "approved" feast flag stops the build.

This is **arithmetic integrity, not astronomical or religious ratification**. `verification.unresolved` explicitly identifies crescent visibility, local sunset, Abib/barley observation, 12/13-month policy, Shavuot counting, and draft makeup/feast rules as open. Current-source dates are marked **supplied**, which means founder-provided, **not independently sighted**. Projected dates are mean-lunation/equinox approximations, not an ephemeris. The engine does not create a Shavuot event, does not assign unapproved religious year numbering to 2026, and does not treat a thirteenth month as Jubilee.

Oustory uses this audit as a transparency panel and links date-specific suggested Scripture readings without changing the underlying calendar or source verses.

## Run
Python 3.10+: `python generate.py`. No dependencies required. Outputs go into public/.

## Publish
In repository Settings > Pages, choose GitHub Actions as the source, then run the Build calendar workflow. Publication requires that setup; uploading the workflow alone does not guarantee a live site. The workflow rebuilds on changes and daily. Rebuilding does not discover observations or make projections confirmed.

## Outputs
- planning.ics: supplied dates and labeled projections
- supplied.ics: entries based on supplied anchors plus supplied observances
- calendar.json: shared app data and pending-year information
- calendar.csv: reviewable event table
- intercalation.csv: projected later-track year starts and 12-/13-month counts
- track-years.csv: both tracks, their year starts, 12-/13-month counts and extra-month starts
- track-calendar.csv: event list tagged with earlier or later, year, month, lunar day and rule status
- earlier-planning.ics / later-planning.ics: separate subscribable all-day planning feeds (draft feasts explicitly labeled)

Apple Calendar must subscribe to the hosted ICS URL to receive future changes. One-time imports do not update.

## Rules
Day 1 is New Moon; Sabbaths are days 8, 15, 22, 29. Makeup observances use the same lunar day in the next lunar month, not a fixed 30-day addition. Provisional year alignment starts at the first projected monthly Day 1 on/after the UTC civil date of the March equinox; 13 months are inserted when consecutive seasonal year starts span 13 lunations. This is not a verified crescent-visibility or barley observation. Supplied anchors are never changed and annual feast approval remains separate.

Add approved annual anchors under abib_anchors, for example a year key with date and status fields. Its date must match a month start. Add or correct month anchors under supplied_month_starts using the existing month-index sequence. Supplied means user-established, not independently verified.

Historical calendar variants must be reconciled before merging. This initial configuration preserves the supplied October 2026-February 2027 month anchors and February 2027 Purim labels. Events are all-day markers, not sunset-time calculations.

## Seasonal intercalation planning — 12 or 13 months

The projection uses a 29.530588853-day mean lunar month and a 365.2422-day mean tropical solar year, anchored to the published 2027 March equinox at 20:24 UTC. The equinox is a date-level approximation, NOT a precision ephemeris. March equinox source: https://www.timeanddate.com/calendar/seasons.html?n=1440.

| Year | First lunar month | Months | Following year starts | Extra month starts |
|---|---|---|---|---|
| 2027 | 2027-04-07 | 12 | 2028-03-26 | — |
| 2028 | 2028-03-26 | 13 | 2029-04-14 | 2029-03-16 |
| 2029 | 2029-04-14 | 12 | 2030-04-04 | — |
| 2030 | 2030-04-04 | 12 | 2031-03-24 | — |

**Planning projections only.** None of these dates is presented as an observed crescent or approved annual Abib anchor. The five user-supplied 2026–2027 monthly starts remain unchanged. The claimed older 2024–2025 history has not yet been imported into this repository, so this is not a four-year historical calibration. Annual feast mappings, Jubilee, and local sunset-time boundaries remain separate. Before finalizing dates, verify borderline equinox dates against a precision ephemeris and the founder's chosen year-start rule.

Run `python -m unittest -v test_intercalation.py` to test source-date preservation, 12/13-month classification, the extra month, and the absence of unapproved feasts.
