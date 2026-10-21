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
        text = (
            "# Note\n"
            "::1 localhost ip6-localhost # inline\n"
            "ff02::1 ip6-allnodes\n"
            "2606:4700:4700::1111 dns.example other.example\n"
            "2606:4700:4700::1111 dns.example\n"
        )
        output, bad = normalize_hosts(text)
        self.assertEqual(
            output,
            "2606:4700:4700::1111 dns.example\n"
            "2606:4700:4700::1111 other.example\n",
        )
        self.assertEqual(bad, 2)

    def test_filter_non_global_ipv4_ipv6_and_multicast(self):
        local_entries = [
            "127.0.0.1 localhost",
            "::1 localhost ip6-localhost ip6-loopback",
            "ff02::1 ip6-allnodes",
            "ff02::2 ip6-allrouters",
            "10.10.10.10 private.example",
            "192.168.1.100 lan.example",
            "172.16.0.1 private-router.example",
            "169.254.1.1 linklocal.example",
            "100.64.0.1 shared.example",
            "224.0.0.1 multicast.example",
            "fc00::1 private-ipv6.example",
            "fe80::1 local-ipv6.example",
            "2001:db8::1 reserved-ipv6.example",
            "0.0.0.0 blocked.example",
        ]
        source = "\n".join(local_entries + [
            "8.8.8.8 public.example second.example",
            "2606:4700:4700::1111 public-ipv6.example",
        ])
        output, rejected = normalize_hosts(source)
        self.assertEqual(
            output,
            "8.8.8.8 public.example\n"
            "8.8.8.8 second.example\n"
            "2606:4700:4700::1111 public-ipv6.example\n",
        )
        self.assertEqual(rejected, len(local_entries))

    def test_only_local_entries_preserve_existing_output(self):
        with self.assertRaises(ValueError):
            normalize_hosts("127.0.0.1 localhost\n::1 localhost\nff02::2 ip6-allrouters\n")

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
