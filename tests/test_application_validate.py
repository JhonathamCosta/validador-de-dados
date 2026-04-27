import unittest

from core.application.validate import run_validation_job


class FakeAdapter:
    def __init__(self, bundle):
        self.bundle = bundle

    def load(self, source, context=None):
        return self.bundle


class InvalidAdapter:
    pass


class TestRunValidationJob(unittest.TestCase):
    def test_runs_end_to_end_for_registered_domain(self):
        adapter = {
            "dados": FakeAdapter(
                {
                    "dados": [
                        {"codigo": ""},
                        {"codigo": "A001"},
                        {"codigo": "A999"},
                    ]
                }
            ),
            "referencias": FakeAdapter(
                {
                    "referencias": [
                        {"codigo": "A001"},
                        {"codigo": "A002"},
                    ]
                }
            ),
        }

        report = run_validation_job(
            domain_id="exemplo",
            source={"dados": "dados.csv", "referencias": "referencias.csv"},
            adapter=adapter,
            context={"user": "tester"},
        )

        self.assertEqual(report.template_id, "exemplo")
        self.assertEqual(report.total_rules, 1)
        self.assertEqual(report.total_fail, 1)
        self.assertEqual(report.results[0].rule_id, "missing_code")
        self.assertEqual(report.results[0].status, "FAIL")
        self.assertEqual(report.results[0].count, 2)

    def test_raises_for_unknown_domain(self):
        adapter = FakeAdapter({"dados": []})
        with self.assertRaises(ValueError):
            run_validation_job(
                domain_id="dominio_inexistente",
                source="fake.csv",
                adapter=adapter,
            )

    def test_raises_for_invalid_adapter(self):
        with self.assertRaises(TypeError):
            run_validation_job(
                domain_id="exemplo",
                source={"dados": "fake.csv"},
                adapter=InvalidAdapter(),
            )

    def test_raises_when_adapter_returns_non_dict(self):
        adapter = {"dados": FakeAdapter(bundle=["not", "a", "dict"])}
        with self.assertRaises(TypeError):
            run_validation_job(
                domain_id="exemplo",
                source={"dados": "fake.csv"},
                adapter=adapter,
            )

    def test_raises_when_source_key_has_no_adapter(self):
        with self.assertRaises(ValueError):
            run_validation_job(
                domain_id="exemplo",
                source={"dados": "dados.csv", "referencias": "referencias.csv"},
                adapter={"dados": FakeAdapter({"dados": []})},
            )


if __name__ == "__main__":
    unittest.main()
