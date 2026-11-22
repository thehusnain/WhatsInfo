import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from WhatsInfo import print_colored_json, save_report, validate_phone_number


class PhoneNumberValidationTests(unittest.TestCase):
    def test_formats_valid_international_number_as_e164(self):
        self.assertEqual(validate_phone_number("+1 (650) 253-0000"), "+16502530000")

    def test_accepts_international_prefix_00(self):
        self.assertEqual(validate_phone_number("0044 20 7031 3000"), "+442070313000")

    def test_rejects_invalid_number(self):
        self.assertIsNone(validate_phone_number("12345"))


class OutputPrivacyTests(unittest.TestCase):
    def test_redacts_network_identifiers_recursively_by_default(self):
        with patch("builtins.print") as print_mock:
            print_colored_json({"profile": {"ip": "192.0.2.1"}, "items": [{"last_ip": "192.0.2.2"}]})

        output = "\n".join(str(call.args[0]) for call in print_mock.call_args_list)
        self.assertNotIn("192.0.2.1", output)
        self.assertNotIn("192.0.2.2", output)
        self.assertEqual(output.count("[redacted]"), 2)

    def test_can_show_network_identifiers_explicitly(self):
        with patch("builtins.print") as print_mock:
            print_colored_json({"ip": "192.0.2.1"}, show_network_identifiers=True)

        self.assertIn("192.0.2.1", str(print_mock.call_args))

    def test_saved_report_redacts_network_identifiers_by_default(self):
        response_data = {"profile": {"name": "Example", "ip": "192.0.2.1"}}
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "reports" / "report.json"
            save_report(
                report_path,
                "+16502530000",
                "provider.example",
                response_data,
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(report["phone_number"], "+16502530000")
        self.assertEqual(report["data"]["profile"]["name"], "Example")
        self.assertEqual(report["data"]["profile"]["ip"], "[redacted]")
        self.assertIn("generated_at", report)


if __name__ == "__main__":
    unittest.main()
