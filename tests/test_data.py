"""사람이 고치는 data/*.json 형식 검사 (Actions 의 Test parsers 단계에서 같이 돈다)."""
import json
import re
import unittest
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
HHMM = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")


class ManualSchedule(unittest.TestCase):
    def test_guild_schedule(self):
        m = json.loads((DATA / "manual.json").read_text(encoding="utf-8"))
        for g in m.get("guild_schedule", []):
            with self.subTest(g=g.get("name")):
                self.assertTrue(g.get("name"))
                self.assertIn(g.get("wday"), range(7))
                self.assertRegex(g.get("time", ""), HHMM)
                if "dur" in g:
                    self.assertGreater(g["dur"], 0)


class PatchBrief(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = json.loads((DATA / "patch.json").read_text(encoding="utf-8"))

    def test_header(self):
        self.assertRegex(self.p["date"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertTrue(self.p["title"])
        name, url = self.p["source"]
        self.assertTrue(url.startswith("https://forum.kakaogames.com/"))

    def test_damage(self):
        names = [d["name"] for d in self.p["damage"]]
        self.assertEqual(len(names), len(set(names)), "도술 중복")
        for d in self.p["damage"]:
            with self.subTest(d=d["name"]):
                self.assertIsInstance(d["pct"], (int, float))
                self.assertNotEqual(d["pct"], 0)
                self.assertLessEqual(abs(d["pct"]), 100)

    def test_zones(self):
        powers = [z["power"] for z in self.p.get("zones", [])]
        self.assertEqual(powers, sorted(powers), "권장 전투력 오름차순")

    def test_timeline(self):
        t = self.p.get("timeline", [])
        mins = lambda s: int(s[:2]) * 60 + int(s[3:])
        for a, b in zip(t, t[1:]):
            self.assertEqual(a["end"], b["start"], "구간이 이어져야 함")
        for b in t:
            self.assertRegex(b["start"], HHMM)
            self.assertLess(mins(b["start"]), mins(b["end"]))

    def test_breakthrough(self):
        b = self.p.get("breakthrough")
        if not b:
            return
        for x in b["stages"]:
            with self.subTest(step=x["step"]):
                self.assertTrue(0 < x["p"] <= 100)
                if x.get("ceil") is not None:
                    self.assertGreaterEqual(x["ceil"], 0)

    def test_manual_shop(self):
        for r in self.p.get("manual_shop", {}).get("rows", []):
            self.assertIn(r["per"], ("일일", "주간"))
            self.assertGreater(r["n"], 0)

    def test_decks(self):
        d = self.p.get("decks")
        if not d:
            return
        self.assertTrue(d.get("credit"), "외부 계산 결과는 출처 필수")
        for k in ("boss", "hunt"):
            if k not in d:
                continue
            for t in d[k].get("top", []):
                with self.subTest(mode=k, style=t["style"]):
                    self.assertIn(t["ult"], t["order"])


if __name__ == "__main__":
    unittest.main()
