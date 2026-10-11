"""Offline acceptance checks for the delivered profile and local preview."""
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
from urllib.parse import parse_qs, urlsplit
import xml.etree.ElementTree as ET

from preview import render

ROOT = Path(__file__).resolve().parents[1]


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ("src", "srcset") and value.startswith("assets/"):
                self.paths.append(value)


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.readme = (ROOT / "README.md").read_text()

    def test_readme_budget_and_structure(self):
        self.assertLess(len(self.readme.splitlines()), 120)
        self.assertEqual(re.findall(r"^## `~/` (.+)$", self.readme, re.M),
                         ["whoami", "toolbox", "skill radar", "contribution calendar", "the numbers", "selected work"])
        self.assertEqual(len(re.findall(r"^\| \*\*", self.readme, re.M)), 4)
        self.assertEqual(self.readme.count("skillicons.dev/icons"), 1)
        self.assertNotIn("github-readme-stats", self.readme)

    def test_all_local_images_exist_and_parse(self):
        parser = Images()
        parser.feed(self.readme)
        self.assertEqual(len(set(parser.paths)), 8)
        for path in set(parser.paths):
            with self.subTest(path=path):
                svg = ET.parse(ROOT / path).getroot()
                self.assertEqual(svg.tag, "{http://www.w3.org/2000/svg}svg")
                self.assertIsNotNone(svg.find("{http://www.w3.org/2000/svg}title"))

    def test_banner_and_footer_binary(self):
        url = re.search(r'src="(https://readme-typing-svg[^\"]+)"', self.readme).group(1)
        lines = parse_qs(urlsplit(unescape(url)).query)["lines"][0].split(";")
        self.assertEqual(len(lines), 3)
        decode = lambda s: "".join(chr(int(byte, 2)) for byte in s.split())
        self.assertEqual(decode(lines[2]), "Rachit Kumar Tiwari")
        footer = re.search(r"<sub><code>([01 ]+)</code></sub>", self.readme).group(1)
        self.assertEqual(decode(footer), "thanks for scrolling")

    def test_preview_matches_readme(self):
        preview = (ROOT / "preview.html").read_text()
        self.assertIn(render(self.readme), preview)
        self.assertEqual(preview.count("<table>"), 1)
        self.assertEqual(preview.count("<h2>"), 6)
        self.assertIn("prefers-color-scheme:light", preview)


if __name__ == "__main__":
    unittest.main()
