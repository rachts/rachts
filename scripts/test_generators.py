"""Run from repository root: python3 -m unittest discover -s scripts -v."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError
import xml.etree.ElementTree as ET

import radar
import stats_cards
import make_portrait


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(Path(__file__).with_name("skills.json").read_text())

    def test_configured_ratings_render_shapes(self):
        radar.validate_config(self.config)
        svg = radar.render_chart(self.config["skills"], 5)
        ET.fromstring(svg)
        self.assertNotIn("TODO", svg)
        self.assertIn('fill-opacity="0.3"', svg)
        self.assertTrue(all(c["rating"] == 3 for key in ("skills", "languages") for c in self.config[key]["categories"]))

    def test_validation(self):
        for invalid in (True, -1, 6, float("nan"), float("inf"), "4"):
            config = copy.deepcopy(self.config)
            config["skills"]["categories"][0]["rating"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                radar.validate_config(config)

    def test_svg_escapes_injection(self):
        chart = self.config["skills"]
        chart["title"] = '<script>alert("x")</script>&'
        for category in chart["categories"]:
            category.update(name="<script>&", rating=0)
        for svg in (radar.render_chart(chart, 5), stats_cards.render_stats("<script>&", {"<script>": "</text><script/>"}, "<&")):
            root = ET.fromstring(svg)
            self.assertFalse(any(node.tag.endswith("script") for node in root.iter()))
            self.assertIn("&lt;script&gt;", svg)

    def test_placeholder_never_reads_token_or_network(self):
        original_get = stats_cards.os.environ.get

        def guarded_get(key, default=None):
            if key == "GITHUB_TOKEN":
                raise AssertionError("token read in offline mode")
            return original_get(key, default)

        with tempfile.TemporaryDirectory() as directory, patch.object(stats_cards, "urlopen", side_effect=AssertionError("network")), patch.object(stats_cards.os.environ, "get", side_effect=guarded_get):
            output = Path(directory) / "stats.svg"
            self.assertEqual(stats_cards.main(["--placeholder", "--output", str(output)]), 0)
            svg = output.read_text()
            ET.fromstring(svg)
            self.assertIn("not fetched", svg)

    def test_pagination_filters_and_deduplicates(self):
        def repo(identifier, stars=2, **overrides):
            return dict(id=identifier, stargazers_count=stars, owner={"login": "rachts"}, private=False, fork=False, **overrides)
        first = [repo(i) for i in range(100)]
        first[0]["fork"] = True
        first[1]["private"] = True
        first[2]["owner"] = {"login": "other"}
        with patch.object(stats_cards, "request_json", side_effect=[{"public_repos": 102, "followers": 4, "following": 3}, first, [repo(99), repo(100, 7)]]) as request:
            stats = stats_cards.fetch_stats("rachts", None, 20)
        self.assertEqual(stats["Owned public non-fork repositories"], 98)
        self.assertEqual(stats["Stars on owned public non-fork repos"], 201)
        self.assertIn("page=2", request.call_args.args[0])

    def test_network_error_does_not_leak_token_or_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "stats.svg"
            output.write_text("previous")
            stderr = io.StringIO()
            with patch.dict("os.environ", {"GITHUB_TOKEN": "secret-token"}), patch.object(stats_cards, "urlopen", side_effect=URLError("secret-token")), contextlib.redirect_stderr(stderr):
                self.assertEqual(stats_cards.main(["--output", str(output)]), 1)
            self.assertNotIn("secret-token", stderr.getvalue())
            self.assertEqual(output.read_text(), "previous")

    def test_timeout_and_authorization(self):
        response = io.StringIO('{"followers": 1}')
        with patch.object(stats_cards, "urlopen", return_value=response) as opened:
            stats_cards.request_json("/users/rachts", "test-token", 7)
        self.assertEqual(opened.call_args.kwargs["timeout"], 7)
        self.assertEqual(opened.call_args.args[0].get_header("Authorization"), "Bearer test-token")

    def test_missing_portrait_is_clear(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(make_portrait.main(["--input", str(Path(directory) / "missing.jpg")]), 1)
        self.assertIn("photo not found", stderr.getvalue())

    def test_binary_portrait_if_pillow_available(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("optional Pillow not installed")
        with tempfile.TemporaryDirectory() as directory:
            photo = Path(directory) / "photo.png"
            output = Path(directory) / "portrait.svg"
            Image.new("RGBA", (8, 8), (0, 0, 0, 128)).save(photo)
            self.assertEqual(make_portrait.main(["--input", str(photo), "--output", str(output), "--grid", "8"]), 0)
            root = ET.fromstring(output.read_text())
            self.assertEqual(len(root.findall(".//{http://www.w3.org/2000/svg}circle")), 64)
            self.assertFalse(root.findall(".//{http://www.w3.org/2000/svg}rect"))


if __name__ == "__main__":
    unittest.main()
