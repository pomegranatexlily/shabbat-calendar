"""Dual-calendar invariants: two independently numbered years on shared moons."""
import json
import unittest
from pathlib import Path
from datetime import date, timedelta
from generate import build, extend_window

class ParallelTracksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads(Path("config.json").read_text(encoding="utf8"))
        cls.result=build(cls.config)
        cls.early=cls.result["tracks"]["earlier"]
        cls.late=cls.result["tracks"]["later"]
    @staticmethod
    def match(track,when,kind,year=None,title=None):
        return [e for e in track["events"]
                if e["date"]==when and e["kind"]==kind
                and (year is None or e["year"]==year)
                and (title is None or e["title"]==title)]

    def test_current_supplied_cycle_october_2026(self):
        for track in (self.early,self.late):
            starts={m["start"]:m for m in track["current_months"]}
            self.assertIn("2026-10-12",starts)
            self.assertEqual(starts["2026-10-12"]["status"],"supplied")
            self.assertIsNone(starts["2026-10-12"]["month"])
            first=[e for e in track["current_events"]
                   if e["date"]=="2026-10-19" and e["kind"]=="sabbath"]
            self.assertEqual(len(first),1)
            self.assertEqual(first[0]["lunar_day"],8)
            self.assertEqual(first[0]["status"],"supplied")
            self.assertIsNone(first[0]["year"])
            self.assertIsNone(first[0]["month"])
            self.assertEqual(len({e["id"] for e in track["events"]+track["current_events"]}),
                             len(track["events"]+track["current_events"]))

    def test_2027_two_new_years_and_first_shabbats(self):
        self.assertEqual(self.early["years"][0]["start_date"],"2027-03-09")
        self.assertEqual(self.late["years"][0]["start_date"],"2027-04-07")
        self.assertEqual(self.early["years"][0]["status"],"user_designated_projection")
        self.assertEqual(self.late["years"][0]["status"],"user_designated_projection")
        for track,moon,shabbat in [
            (self.early,"2027-03-09","2027-03-16"),
            (self.late,"2027-04-07","2027-04-14")
        ]:
            new=self.match(track,moon,"new_moon",2027)
            day8=self.match(track,shabbat,"sabbath",2027)
            self.assertEqual(len(new),1)
            self.assertEqual((new[0]["month"],new[0]["lunar_day"]),(1,1))
            self.assertEqual(len(day8),1)
            self.assertEqual((day8[0]["month"],day8[0]["lunar_day"]),(1,8))
            self.assertFalse(any(e["kind"]=="sabbath" and e["lunar_day"] not in (8,15,22,29) for e in track["events"]))

    def test_one_new_moon_two_month_names(self):
        earlier=self.match(self.early,"2027-04-07","new_moon",2027)
        later=self.match(self.late,"2027-04-07","new_moon",2027)
        self.assertEqual(len(earlier),len(later))
        self.assertEqual((earlier[0]["month"],later[0]["month"]),(2,1))
        self.assertNotEqual(earlier[0]["id"],later[0]["id"])

    def test_month_thirteen_independently_numbered(self):
        for track,extra in [(self.early,"2029-02-14"),(self.late,"2029-03-16")]:
            self.assertEqual([y["month_count"] for y in track["years"]],[12,13,12,12])
            y=track["years"][1]
            self.assertEqual(y["thirteenth_month_start"],extra)
            thirteenth=[m for m in track["months"] if m["year"]==2028 and m["is_thirteenth"]]
            self.assertEqual(len(thirteenth),1)
            self.assertEqual((thirteenth[0]["month"],thirteenth[0]["start"]),(13,extra))

    def test_draft_feasts_per_track_not_four_makeup_copies(self):
        early=self.match(self.early,"2027-03-22","feast",2027,"Passover")
        later=self.match(self.late,"2027-04-20","feast",2027,"Passover")
        self.assertEqual(len(early),1)
        self.assertEqual(len(later),1)
        for event in early+later:
            self.assertEqual(event["rule_status"],"unapproved_draft")
            self.assertEqual((event["month"],event["lunar_day"]),(1,14))
        self.assertEqual(len([e for e in self.early["events"] if e["year"]==2027 and e["title"]=="Passover"]),1)
        self.assertEqual(len([e for e in self.late["events"] if e["year"]==2027 and e["title"]=="Passover"]),1)

    def test_archived_supplied_dates_are_unchanged(self):
        supplied={int(k):v for k,v in self.config["supplied_month_starts"].items()}
        dates={m["index"]:m["date"] for m in self.result["months"] if m["status"]=="supplied"}
        self.assertEqual(dates,supplied)
        self.assertIn("2027-02-20",[e["date"] for e in self.result["events"] if e["status"]=="supplied"])

    def test_rolling_year_window(self):
        base=dict(self.config)
        self.assertEqual(extend_window(base,2026)["end_year"],2034)
        self.assertEqual(extend_window(base,2035)["end_year"],2043)
        self.assertEqual(base["end_year"],2030,"source config must not be mutated")
        with self.assertRaisesRegex(ValueError,"between 1 and 20"):
            extend_window({**base,"rolling_years_ahead":0},2026)

    def test_valid_month_counts_and_day_ranges(self):
        for track in (self.early,self.late):
            for m in track["months"]:
                self.assertIn(m["days"],(29,30))
                self.assertEqual((date.fromisoformat(m["end"])-date.fromisoformat(m["start"])).days+1,m["days"])
            for e in track["events"]:
                self.assertTrue(1<=e["month"]<=13)
                self.assertTrue(1<=e["lunar_day"]<=30)
            self.assertEqual(len({e["id"] for e in track["events"]}),len(track["events"]))

if __name__=="__main__":
    unittest.main()
