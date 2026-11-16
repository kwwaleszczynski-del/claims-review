"""Unit tests for skills/claims-review/scripts/trace_numbers.py.

Run from the repository root:
    python -m unittest discover -s tests -v
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "claims-review" / "scripts"))

import trace_numbers as tn  # noqa: E402


def texts(markdown, **kwargs):
    return [n["text"] for n in tn.extract_numbers(markdown, **kwargs)]


class ExtractTests(unittest.TestCase):
    def test_plain_decimal_percent_and_line_numbers(self):
        found = tn.extract_numbers("intro\nRecall is 0.90 and MAPE 6.2%.\n")
        self.assertEqual([(n["line"], n["text"]) for n in found],
                         [(2, "0.90"), (2, "6.2%")])
        self.assertEqual(found[0]["decimals"], 2)
        self.assertFalse(found[0]["percent"])
        self.assertTrue(found[1]["percent"])
        self.assertEqual(found[1]["value"], 6.2)

    def test_percent_word_and_thousands_separator(self):
        found = tn.extract_numbers("We used 12,345 rows and saved 15 percent.")
        self.assertEqual(found[0]["value"], 12345.0)
        self.assertTrue(found[1]["percent"])

    def test_negative_number_and_range(self):
        found = tn.extract_numbers("Bias was -3.2 units, within 5-10 units.")
        self.assertEqual([n["value"] for n in found], [-3.2, 5.0, 10.0])

    def test_fenced_code_skipped_unless_asked(self):
        md = "Score 0.8\n```\npip install pkg==2.5\nvalue 7.7\n```\nafter 3.3\n"
        self.assertEqual(texts(md), ["0.8", "3.3"])
        self.assertIn("7.7", texts(md, include_code=True))

    def test_noise_is_masked(self):
        md = ("1. First item scored 0.75\n"
              "## 2. Heading\n"
              "Released 2024-03-15 as v1.2.3 at 12:30, see https://example.org/a/42\n"
              "[link 9.9](docs/page7.md) and model h5 or utf8\n")
        self.assertEqual(texts(md), ["0.75", "9.9"])

    def test_number_with_unit_suffix_is_kept(self):
        self.assertEqual(texts("A 2x speed-up on a 50MW unit."), ["2", "50"])

    def test_sentence_final_number(self):
        self.assertEqual(texts("The error is 4.5."), ["4.5"])


class TraceTests(unittest.TestCase):
    VALUES = [(0.9, "r.json:recall"), (8.6712, "r.json:mape_pct"),
              (-0.1234, "r.json:delta"), (0.876, "r.json:f1"), (7, "r.json:n_sites")]

    def one(self, markdown):
        return tn.trace(tn.extract_numbers(markdown)[0], self.VALUES)

    def test_rounding_match(self):
        row = self.one("MAPE 8.7%")
        self.assertEqual(row["status"], "traced")
        self.assertEqual(row["sources"][0]["where"], "r.json:mape_pct")

    def test_percent_matches_fraction(self):
        self.assertEqual(self.one("detects 90% of faults")["status"], "traced")

    def test_plain_number_does_not_match_scaled_fraction(self):
        self.assertEqual(self.one("score of 90 points")["status"], "UNTRACED")

    def test_sign_is_ignored(self):
        self.assertEqual(self.one("cut by 12.3%")["status"], "traced")

    def test_truncated_number_is_near(self):
        self.assertEqual(self.one("F1 0.87")["status"], "near")

    def test_stale_number_is_untraced(self):
        self.assertEqual(self.one("MAPE 6.2%")["status"], "UNTRACED")

    def test_small_integer_needs_exact_match(self):
        self.assertEqual(self.one("across 7 sites")["status"], "traced")
        self.assertEqual(self.one("across 9 sites")["status"], "minor")
        # 0.9 must not round up to back the bare integer 1
        self.assertEqual(self.one("in 1 region")["status"], "minor")

    def test_year_is_skipped(self):
        self.assertEqual(self.one("tested on 2023 data")["status"], "skipped")


class EndToEndTests(unittest.TestCase):
    def make_repo(self, tmp, with_results=True):
        repo = Path(tmp)
        (repo / "README.md").write_text(
            "# Demo\n\nRecall 0.90, MAPE 6.2%, RMSE 12.5 on 2023.\n", encoding="utf-8")
        if with_results:
            (repo / "results" / "sub").mkdir(parents=True)
            (repo / "results" / "summary.json").write_text(
                json.dumps({"metrics": {"recall": 0.9, "mape": [0.087], "ok": True}}),
                encoding="utf-8")
            (repo / "results" / "sub" / "table.csv").write_text(
                "model,rmse,note\nbase,12.49,x\nnew,n/a,y\n", encoding="utf-8")
        return repo

    def test_json_and_csv_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = tn.run(self.make_repo(tmp))
        by_text = {n["text"]: n for n in report["numbers"]}
        self.assertEqual(by_text["0.90"]["status"], "traced")
        self.assertEqual(by_text["0.90"]["sources"][0]["where"],
                         "results/summary.json:metrics.recall")
        self.assertEqual(by_text["6.2%"]["status"], "UNTRACED")
        self.assertEqual(by_text["12.5"]["sources"][0]["where"],
                         "results/sub/table.csv:row 2:rmse")
        self.assertEqual(by_text["2023"]["status"], "skipped")
        self.assertEqual(report["counts"], {"traced": 2, "UNTRACED": 1, "skipped": 1})
        self.assertEqual(report["n_result_values"], 3)  # booleans and n/a excluded

    def test_missing_results_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = tn.run(self.make_repo(tmp, with_results=False))
        self.assertEqual(report["results_files"], [])
        self.assertIn("No results files found", tn.format_text(report))

    def test_cli_text_and_json(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(tmp)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = tn.main([str(repo)])
            self.assertEqual(code, 0)
            self.assertIn("UNTRACED", out.getvalue())
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                tn.main([str(repo), "--json"])
            self.assertEqual(len(json.loads(out.getvalue())["numbers"]), 4)

    def test_missing_readme_returns_2(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(tn.main([tmp]), 2)


if __name__ == "__main__":
    unittest.main()
