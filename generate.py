import csv
import json
import uuid
from datetime import date, timedelta, datetime, timezone
from pathlib import Path
from intercalation import seasonal_years, annotate_months
from dual_tracks import create_tracks

MEAN_LUNATION = 29.530588853

def build(c):
    lo = date(c['start_year'], 1, 1)
    hi = date(c['end_year'] + 1, 1, 1)
    planning_hi = date(c['end_year'] + 1, 6, 1)
    anchor = date.fromisoformat(c['projection_anchor'])
    known = {int(k): date.fromisoformat(v) for k, v in c['supplied_month_starts'].items()}
    months = []
    n = min(known)
    while True:
        d = known.get(n, anchor + timedelta(days=int(n * MEAN_LUNATION + 0.5)))
        if d >= planning_hi:
            break
        months.append({'index': n, 'date': d.isoformat(), 'status': 'supplied' if n in known else 'projected'})
        n += 1
    for a, b in zip(months, months[1:]):
        assert (date.fromisoformat(b['date']) - date.fromisoformat(a['date'])).days in (29, 30), 'Invalid month gap'
    yearly_intercalation = seasonal_years(months, c['start_year'], c['end_year'])
    annotate_months(months, yearly_intercalation)
    tracks = create_tracks(months, yearly_intercalation, c)
    published_months = [m for m in months if date.fromisoformat(m['date']) < hi]
    by_index = {m['index']: m for m in months}
    events = []
    pending = []
    def add(m, day, title, kind, window='primary', identity=None, status=None):
        d = date.fromisoformat(m['date']) + timedelta(days=day - 1)
        if not lo <= d < hi:
            return
        key = identity or f"month:{m['index']}:{day}:{kind}"
        events.append({'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'shabbat-calendar/' + key)), 'date': d.isoformat(), 'title': title, 'kind': kind, 'window': window, 'status': status or m['status'], 'month_index': m['index'], 'lunar_day': day})
    for m in published_months:
        add(m, 1, 'New Moon', 'new_moon')
        for day in (8, 15, 22, 29):
            add(m, day, 'Shabbat', 'sabbath')
    for year in range(c['start_year'], c['end_year'] + 1):
        annual = c.get('abib_anchors', {}).get(str(year))
        if not annual:
            pending.append({'year': year, 'reason': 'Projected season-aligned starts available; unapproved annual feast and Abib decisions remain withheld.'})
            continue
        first = next((m for m in months if m['date'] == annual['date']), None)
        if first is None:
            raise ValueError('Abib anchor must match a month start')
        for rule in c['feast_rules']:
            for shift in range(2 if rule.get('makeup') else 1):
                target = by_index.get(first['index'] + rule['month'] - 1 + shift)
                if target is None:
                    continue
                for offset in range(rule.get('duration', 1)):
                    title = rule['name']
                    if rule.get('duration', 1) > 1:
                        title += f' (Day {offset + 1})'
                    if shift:
                        title += ' - Makeup / Alternate'
                    status = 'supplied' if annual.get('status') == 'supplied' and target['status'] == 'supplied' else 'projected'
                    add(target, rule['day'] + offset, title, 'feast', 'makeup' if shift else 'primary', f"feast:{year}:{rule['name']}:{offset}:{shift}", status)
    for item in c.get('supplied_events', []):
        if lo.isoformat() <= item['date'] < hi.isoformat():
            key = 'supplied:' + item['date'] + ':' + item['title']
            events.append({'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'shabbat-calendar/' + key)), **item, 'kind': 'feast', 'window': 'primary', 'status': 'supplied', 'month_index': None, 'lunar_day': None})
    events.sort(key=lambda e: (e['date'], e['title']))
    assert len({e['id'] for e in events}) == len(events), 'Duplicate event IDs'
    return {'schema_version': 2, 'months': published_months, 'seasonal_years': yearly_intercalation, 'tracks': tracks, 'events': events, 'pending': pending, 'method': '12-/13-month equinox-aligned planning projection from mean lunar months. Neither a crescent sighting nor a finalized annual feast ruling.'}

def escape(s):
    return s.replace('\\', '\\\\').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')

def fold(s):
    parts = []
    while len(s.encode('utf-8')) > 75:
        n = 75
        while len(s[:n].encode('utf-8')) > 75:
            n -= 1
        parts.append(s[:n])
        s = ' ' + s[n:]
    return '\r\n'.join(parts + [s])

def ics(events, name):
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Shabbat Calendar//EN', 'CALSCALE:GREGORIAN', 'X-WR-CALNAME:' + escape(name)]
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for e in events:
        d = date.fromisoformat(e['date'])
        title = e['title'] + (' [DRAFT FEAST]' if e.get('rule_status') == 'unapproved_draft' else (' [Projected]' if e['status'] == 'projected' else ''))
        note = 'Draft feast calculation, not approved; do not treat as a confirmed observance.' if e.get('rule_status') == 'unapproved_draft' else ('Mean-lunation planning projection; not a visibility prediction.' if e['status'] == 'projected' else 'Based on user-supplied dates.')
        lines.extend(['BEGIN:VEVENT', 'UID:' + e['id'] + '@shabbat-calendar', 'DTSTAMP:' + stamp, f'DTSTART;VALUE=DATE:{d:%Y%m%d}', f'DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}', 'SUMMARY:' + escape(title), 'DESCRIPTION:' + escape(note + ' All-day marker; no sunset time encoded.'), 'TRANSP:TRANSPARENT', 'END:VEVENT'])
    lines.append('END:VCALENDAR')
    return ('\r\n'.join(fold(s) for s in lines) + '\r\n').encode('utf-8')

def extend_window(c, today_year=None):
    """Keep a rolling calendar horizon without rewriting supplied anchor dates.

    Called for publication, not for historical regression fixtures: a new
    year adds one future year rather than growing a never-ending physical CSV.
    """
    from datetime import datetime, timezone
    today_year = today_year if today_year is not None else datetime.now(timezone.utc).year
    horizon = int(c.get('rolling_years_ahead', 8))
    if horizon < 1 or horizon > 20:
        raise ValueError('rolling_years_ahead must be between 1 and 20')
    cfg = dict(c)
    cfg['end_year'] = max(int(cfg['end_year']), today_year + horizon)
    if cfg['end_year'] > 2098:
        raise ValueError('Rolling horizon exceeds the configured equinox approximation range')
    return cfg

def main():
    c = extend_window(json.loads(Path('config.json').read_text(encoding='utf-8')))
    data = build(c)
    out = Path('public')
    out.mkdir(exist_ok=True)
    (out / 'calendar.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
    # Parallel feeds use one lunar series; never duplicate a makeup
    # observance within one track when the other track represents it.
    with (out / 'track-years.csv').open('w', newline='', encoding='utf-8') as f:
        fields = ['track', 'year', 'start_date', 'next_start_date', 'month_count',
                  'has_13th_month', 'thirteenth_month_start', 'status']
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for track_id, track in data['tracks'].items():
            for entry in track['years']:
                w.writerow({'track': track_id, **entry})
    with (out / 'track-calendar.csv').open('w', newline='', encoding='utf-8') as f:
        fields = ['id','date','track','year','month','lunar_day','title','kind',
                  'status','rule_status','source','month_index']
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for track_id, track in data['tracks'].items():
            w.writerows(sorted(track['current_events'] + track['events'], key=lambda e: (e['date'], e['title'])))
    for track_id, track in data['tracks'].items():
        (out / (track_id + '-planning.ics')).write_bytes(
            ics(sorted(track['current_events'] + track['events'], key=lambda e: (e['date'], e['title'])), 'Shabbat Calendar - ' + track['label'] + ' (Planning)'))
    with (out / 'intercalation.csv').open('w', newline='', encoding='utf-8') as f:
        columns=['year','first_month_start','next_first_month_start','month_count','has_13th_month','thirteenth_month_start','status','march_equinox_utc_estimate']
        w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore')
        w.writeheader()
        w.writerows(data['seasonal_years'])
    with (out / 'calendar.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['id', 'date', 'title', 'kind', 'window', 'status', 'month_index', 'lunar_day'])
        w.writeheader()
        w.writerows(data['events'])
    (out / 'planning.ics').write_bytes(ics(data['events'], 'Shabbat Calendar - Planning'))
    (out / 'supplied.ics').write_bytes(ics([e for e in data['events'] if e['status'] == 'supplied'], 'Shabbat Calendar - Supplied Dates'))

if __name__ == '__main__':
    main()
