import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from normalize_hosts import is_hostname, normalize_hosts  # noqa: E402


class HostsNormalizationTests(unittest.TestCase):
    def test_expand_hosts_without_losing_alternate_ips(self):
        text = "1.2.3.4 a.example b.example\n5.6.7.8 a.example\n"
        output, bad = normalize_hosts(text)
        self.assertEqual(output, "1.2.3.4 a.example\n1.2.3.4 b.example\n5.6.7.8 a.example\n")
        self.assertEqual(bad, 0)

    def test_ipv6_comments_and_duplicates(self):
        text = "# Note\n::1 localhost ip6-localhost # inline\n::1 localhost\n\n"
        output, bad = normalize_hosts(text)
        self.assertEqual(output, "::1 localhost\n::1 ip6-localhost\n")
        self.assertEqual(bad, 0)

    def test_whitespace_case_and_trailing_dot(self):
        output, bad = normalize_hosts("  8.8.8.8  EXAMPLE.COM.\twww.example.com  \n")
        self.assertEqual(output, "8.8.8.8 example.com\n8.8.8.8 www.example.com\n")
        self.assertEqual(bad, 0)

    def test_invalid_entries_do_not_create_injections(self):
        output, bad = normalize_hosts("not-an-ip bad.example\n1.2.3.4 valid.test *.invalid.test exa_mple.com\n")
        self.assertEqual(output, "1.2.3.4 valid.test\n")
        self.assertEqual(bad, 3)
        self.assertFalse(is_hostname("bad..example"))

    def test_empty_or_invalid_source_fails(self):
        with self.assertRaises(ValueError):
            normalize_hosts("<html>error</html>\n# empty\n")


if __name__ == "__main__":
    unittest.main()
