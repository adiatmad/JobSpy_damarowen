import unittest

from opportunity import build_google_research_links, build_research_brief, build_research_queries


class ResearchPackTests(unittest.TestCase):
    ROW = {
        "title": "Senior Management Trainee",
        "company": "PT Glori Investama Surabaya",
        "location": "Surabaya, East Java, Indonesia",
        "date_posted": "2026-09-09",
        "Work Type": "On-site",
        "Gaji Asli": "Gaji dirahasiakan",
        "Match Score": 72,
        "Evidence Coverage": 83,
        "Evidence Gaps": "salary",
        "Why Match": "keyword lengkap di judul; lokasi cocok",
        "job_url": "https://example.com/job/1",
        "source": "linkedin",
        "description": "Example description",
    }

    def test_queries_are_company_specific_and_deterministic(self):
        queries = build_research_queries(self.ROW)
        self.assertIn('"PT Glori Investama Surabaya" careers jobs', queries)
        self.assertIn('"Senior Management Trainee" "Surabaya, East Java, Indonesia" hiring', queries)
        self.assertEqual(queries, build_research_queries(self.ROW))

    def test_brief_preserves_unknowns_instead_of_inventing_them(self):
        brief = build_research_brief(self.ROW, "management trainee", "Surabaya")
        self.assertIn("Gaji dirahasiakan", brief)
        self.assertIn("salary", brief)
        self.assertIn("does not verify that a vacancy is genuine", brief)
        self.assertIn("Verify the listing and company evidence", brief)

    def test_google_links_are_generated_without_fetching(self):
        links = build_google_research_links(self.ROW)
        self.assertTrue(links)
        self.assertTrue(all(url.startswith("https://www.google.com/search?q=") for _, url in links))

    def test_empty_row_does_not_generate_fake_queries(self):
        self.assertEqual(build_research_queries({}), [])
        self.assertEqual(build_google_research_links({}), [])


if __name__ == "__main__":
    unittest.main()
