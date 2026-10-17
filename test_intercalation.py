"""Python regression tests for seasonal intercalation and supplied-data integrity."""
import json
import unittest
from datetime import date
from pathlib import Path

from generate import build
from intercalation import projected_spring_equinox, seasonal_years

ROOT=Path(__file__).resolve().parent

class IntercalationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))
        cls.data=build(cls.config)
        cls.years={x["year"]:x for x in cls.data["seasonal_years"]}

    def test_equinox_reference_date(self):
        self.assertEqual(projected_spring_equinox(2027).isoformat(),"2027-03-20T20:24:00+00:00")
        for year in (2028,2029,2030):
            self.assertEqual(projected_spring_equinox(year).month,3)
            self.assertEqual(projected_spring_equinox(year).day,20)

    def test_year_starts_and_thirteenth_month(self):
        expected={
            2027:("2027-04-07",12,None),
            2028:("2028-03-26",13,"2029-03-16"),
            2029:("2029-04-14",12,None),
            2030:("2030-04-04",12,None),
        }
        self.assertEqual(set(self.years),set(expected))
        for year,(start,count,extra) in expected.items():
            y=self.years[year]
            self.assertEqual((y["first_month_start"],y["month_count"],y["thirteenth_month_start"]),(start,count,extra))
            self.assertEqual(y["has_13th_month"],bool(extra))
            self.assertEqual(y["status"],"planning_projection")

    def test_thirteenth_month_tagged(self):
        thirteenth=[m for m in self.data["months"] if m.get("is_intercalary")]
        self.assertEqual([(m["date"],m["seasonal_year"],m["month_of_seasonal_year"]) for m in thirteenth],[("2029-03-16",2028,13)])
        self.assertTrue(all(m["status"]=="projected" for m in thirteenth))

    def test_supplied_historical_starts_unchanged(self):
        actual={m["index"]:m["date"] for m in self.data["months"] if m["status"]=="supplied"}
        supplied={int(k):v for k,v in self.config["supplied_month_starts"].items()}
        self.assertEqual(actual,supplied)

    def test_daily_events_still_preserved_and_no_invented_annual_feasts(self):
        events=self.data["events"]
        self.assertTrue(any(e["date"]=="2027-02-20" and e["title"]=="Purim" and e["status"]=="supplied" for e in events))
        self.assertFalse(any("Passover" in e["title"] for e in events))
        self.assertTrue(any(e["title"]=="Shabbat" for e in events))
        self.assertEqual(len(self.data["pending"]),4)

    def test_duplicate_or_nonconsecutive_months_rejected(self):
        with self.assertRaisesRegex(ValueError,"Duplicate lunar month"):
            seasonal_years([{"index":0,"date":"2027-02-07","status":"supplied"}]*2,2027,2027)
        with self.assertRaisesRegex(ValueError,"Missing lunar month index"):
            seasonal_years([{"index":0,"date":"2027-02-07","status":"supplied"},{"index":2,"date":"2027-04-07","status":"projected"}],2027,2027)

if __name__=="__main__":
    unittest.main()
