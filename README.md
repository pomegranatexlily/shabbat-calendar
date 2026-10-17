# Shabbat Calendar

Shared calendar engine for a Shabbat website, Apple Calendar feeds, and Bible-app JSON data.

## Status
This is a planning scaffold, not a verified future feast calendar. Supplied dates remain distinct from projections. Future month starts use a mean-lunation interval, NOT actual crescent visibility. The engine also projects seasonal 12- and 13-month years. Annual feasts are withheld until separately approved Abib anchors are supplied. Shavuot remains pending an explicit counting rule. Draft feast mappings and makeup switches require review.

## Run
Python 3.10+: `python generate.py`. No dependencies required. Outputs go into public/.

## Publish
In repository Settings > Pages, choose GitHub Actions as the source, then run the Build calendar workflow. Publication requires that setup; uploading the workflow alone does not guarantee a live site. The workflow rebuilds on changes and daily. Rebuilding does not discover observations or make projections confirmed.

## Outputs
- planning.ics: supplied dates and labeled projections
- supplied.ics: entries based on supplied anchors plus supplied observances
- calendar.json: shared app data and pending-year information
- calendar.csv: reviewable event table
- intercalation.csv: projected seasonal-year start dates and 12-/13-month counts

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
