import unittest
from backend.atc_data import ATC_DATABASE, CLASS_REGULATION_MAPPING
from backend.disease_data import DISEASE_DATABASE
from backend.atc_engine import ATCEngine
from backend.disease_engine import DiseaseEngine
from backend.indexer import NHIIndexer
from backend.server import app


class TestNHIEngineRefactoring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.indexer = NHIIndexer()
        cls.atc_engine = cls.indexer.atc_engine
        cls.disease_engine = cls.indexer.disease_engine
        cls.client = app.test_client()

    def test_backward_compatible_data_imports(self):
        from backend.atc_engine import ATC_DATABASE as atc_reexport
        from backend.disease_engine import DISEASE_DATABASE as disease_reexport
        self.assertIs(ATC_DATABASE, atc_reexport)
        self.assertIs(DISEASE_DATABASE, disease_reexport)
        self.assertIn("A02BC", CLASS_REGULATION_MAPPING)

    def test_indexed_regulations_count(self):
        self.assertEqual(len(self.indexer.regulations), 573)

    def test_heart_failure_and_class_level_ingredients(self):
        hits = self.indexer.search("heart failure")
        self.assertTrue(len(hits) >= 4)
        top_secs = [r["section_number"] for r in hits[:6]]
        self.assertIn("2.16.", top_secs)
        self.assertIn("2.14.", top_secs)

        # Verify class-level and parent regulations have representative ingredients populated
        sec_map = {r["section_number"]: r for r in self.indexer.regulations}
        for sec in ("2.8.2.", "7.1.", "3.3.1.", "10.9.", "14.1.", "14.5.", "2.6.1."):
            ings = sec_map[sec]["medications"]["ingredients"]
            self.assertTrue(len(ings) > 0, f"Expected representative ingredients on {sec}")

        # Verify 7.1. excludes concomitant background triggers (Clopidogrel, Warfarin)
        ings_7_1_str = " ".join(sec_map["7.1."]["medications"]["ingredients"]).lower()
        self.assertIn("omeprazole", ings_7_1_str)
        self.assertIn("famotidine", ings_7_1_str)
        self.assertNotIn("clopidogrel", ings_7_1_str)
        self.assertNotIn("warfarin", ings_7_1_str)

    def test_peptic_ulcer_bleeding_prevention_query(self):
        hits = self.indexer.search("peptic ulcer bleeding prevention")
        self.assertTrue(len(hits) > 0)
        self.assertEqual(hits[0]["section_number"], "7.1.")

        comma_hits = self.indexer.search("peptic ulcer, bleeding, prevention")
        self.assertTrue(len(comma_hits) > 0)
        self.assertEqual(comma_hits[0]["section_number"], "7.1.")

    def test_multi_segment_order_independence(self):
        q1 = self.indexer.search("Forxiga, 心衰竭")
        q2 = self.indexer.search("心衰竭, Forxiga")
        self.assertTrue(len(q1) > 0)
        self.assertEqual(
            [r["section_number"] for r in q1],
            [r["section_number"] for r in q2]
        )
        self.assertEqual(q1[0]["section_number"], "2.16.")

    def test_highlight_terms_priority_ordering(self):
        terms = self.indexer.get_highlight_terms("metastatic non small cell carcinoma")
        self.assertTrue(len(terms) >= 2)
        self.assertEqual(terms[0], "非小細胞肺癌")
        self.assertIn("轉移性", terms)
        self.assertLess(terms.index("非小細胞肺癌"), terms.index("轉移性"))

        combo_terms = self.indexer.get_highlight_terms("Forxiga, 心衰竭")
        self.assertIn("心臟衰竭", combo_terms)
        self.assertTrue(any("dapagliflozin" in t.lower() or "forxiga" in t.lower() for t in combo_terms))

    def test_adenocarcinoma_of_lung_and_histologic_subtypes(self):
        hits = self.indexer.search("adenocarcinoma of lung")
        self.assertTrue(len(hits) >= 6)
        returned_secs = [r["section_number"] for r in hits]
        for expected_sec in ("9.24.", "9.29.", "9.45.", "9.80.", "9.83.", "9.138.", "9.69.", "9.26."):
            self.assertIn(expected_sec, returned_secs)
        # Ensure loose "lung" token does not pull in unrelated pulmonary fibrosis (6.2.7.) or RSV/heart failure (8.2.8.)
        self.assertNotIn("6.2.7.", returned_secs)
        self.assertNotIn("8.2.8.", returned_secs)

        hl = self.indexer.get_highlight_terms("adenocarcinoma of lung")
        self.assertEqual(hl[0], "肺腺癌")
        self.assertIn("非鱗狀非小細胞肺癌", hl)
        self.assertIn("Lung Adenocarcinoma", hl)

        # Verify Chinese negation guard: "small cell lung cancer" matches SCLC (小細胞肺癌), not NSCLC (非小細胞肺癌)
        sclc_hits = self.indexer.search("small cell lung cancer")
        sclc_secs = [r["section_number"] for r in sclc_hits]
        self.assertIn("9.69.", sclc_secs)
        self.assertNotIn("9.24.", sclc_secs)

    def test_api_endpoints_and_shared_assets(self):
        res_ver = self.client.get("/api/version")
        self.assertEqual(res_ver.status_code, 200)
        self.assertEqual(res_ver.get_json()["total_regulations"], 573)

        res_search = self.client.get("/api/search?q=metastatic+non+small+cell+carcinoma")
        self.assertEqual(res_search.status_code, 200)
        payload = res_search.get_json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["highlight_terms"][0], "非小細胞肺癌")
        self.assertTrue(len(payload["results"]) > 0)

        for asset in ("/", "/mobile", "/shared.js", "/shared.css", "/app.js", "/mobile.js"):
            r = self.client.get(asset)
            self.assertEqual(r.status_code, 200, f"Asset {asset} failed to load")
            r.close()


if __name__ == "__main__":
    unittest.main()
