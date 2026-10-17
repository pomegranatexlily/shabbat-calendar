# Shabbat Calendar

Shared calendar engine for a Shabbat website, Apple Calendar feeds, and Bible-app JSON data.

## Status
This is a planning scaffold, not a verified future feast calendar. Supplied dates remain distinct from projections. Future month starts use a mean-lunation interval, NOT actual crescent visibility. Annual feasts are withheld until Abib anchors are supplied. Shavuot remains pending an explicit counting rule. Draft feast mappings and makeup switches require review.

## Run
Python 3.10+: `python generate.py`. No dependencies required. Outputs go into public/.

## Publish
In repository Settings > Pages, choose GitHub Actions as the source, then run the Build calendar workflow. Publication requires that setup; uploading the workflow alone does not guarantee a live site. The workflow rebuilds on changes and daily. Rebuilding does not discover observations or make projections confirmed.

## Outputs
- planning.ics: supplied dates and labeled projections
- supplied.ics: entries based on supplied anchors plus supplied observances
- calendar.json: shared app data and pending-year information
- calendar.csv: reviewable event table

Apple Calendar must subscribe to the hosted ICS URL to receive future changes. One-time imports do not update.

## Rules
Day 1 is New Moon; Sabbaths are days 8, 15, 22, 29. Makeup observances use the same lunar day in the next lunar month, not a fixed 30-day addition. Abib follows the user's barley and visible-New-Moon rule; no automatic 12-month rollover is imposed.

Add approved annual anchors under abib_anchors, for example a year key with date and status fields. Its date must match a month start. Add or correct month anchors under supplied_month_starts using the existing month-index sequence. Supplied means user-established, not independently verified.

Historical calendar variants must be reconciled before merging. This initial configuration preserves the supplied October 2026-February 2027 month anchors and February 2027 Purim labels. Events are all-day markers, not sunset-time calculations.
