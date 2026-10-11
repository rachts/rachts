#!/usr/bin/env python3
"""Generate honest, self-assessed radar cards using only the standard library."""
import argparse
import json
import math
from pathlib import Path
import sys
from xml.sax.saxutils import escape


def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError("configuration must be a JSON object")
    maximum = config.get("max_rating", 5)
    if isinstance(maximum, bool) or not isinstance(maximum, (int, float)) or not math.isfinite(maximum) or maximum <= 0:
        raise ValueError("max_rating must be a finite positive number")
    for key in ("skills", "languages"):
        chart = config.get(key)
        if not isinstance(chart, dict) or not isinstance(chart.get("title"), str):
            raise ValueError(f"{key} needs a text title")
        categories = chart.get("categories")
        if not isinstance(categories, list) or not 3 <= len(categories) <= 12:
            raise ValueError(f"{key} needs 3–12 categories")
        for item in categories:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"].strip():
                raise ValueError(f"{key} category names must be nonempty text")
            if "rating" not in item:
                raise ValueError("each category needs a rating (use null if unknown)")
            rating = item["rating"]
            if rating is not None and (isinstance(rating, bool) or not isinstance(rating, (int, float)) or not math.isfinite(rating) or not 0 <= rating <= maximum):
                raise ValueError(f"ratings must be null or finite numbers from 0 to {maximum}")
    return config


def render_chart(chart, maximum):
    title = escape(chart["title"])
    categories = chart["categories"]
    complete = all(item["rating"] is not None for item in categories)
    description = (f"Self-assessed ratings out of {maximum}. " + "; ".join(f'{item["name"]}: {item["rating"]}' for item in categories)
                   if complete else "TODO: configure category names and every rating in scripts/skills.json. No skill levels are displayed.")
    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="440" viewBox="0 0 640 440" role="img" aria-labelledby="title desc"><title id="title">{title}</title><desc id="desc">{escape(description)}</desc>',
                '<rect width="640" height="440" rx="16" fill="#0d1117"/>',
                 f'<g font-family="ui-monospace,monospace" fill="#e6edf3"><text x="24" y="38" font-size="22">{title}</text>']
    def point(index, radius):
        angle = -math.pi / 2 + 2 * math.pi * index / len(categories)
        return 320 + radius * math.cos(angle), 226 + radius * math.sin(angle)

    def polygon(radii):
        return " ".join(f"{x:.2f},{y:.2f}" for x, y in (point(i, r) for i, r in enumerate(radii)))

    for step in range(1, 6):
        elements.append(f'<polygon points="{polygon([step * 24] * len(categories))}" fill="none" stroke="#30363d"/>')
    for i, item in enumerate(categories):
        x, y = point(i, 120)
        lx, ly = point(i, 153)
        elements.append(f'<path d="M320 226 L{x:.2f} {y:.2f}" stroke="#30363d"/>')
        # Full labels remain in accessible description/title; bound visual width.
        label = item["name"] if len(item["name"]) <= 22 else item["name"][:19] + "…"
        elements.append(f'<text x="{lx:.2f}" y="{ly:.2f}" text-anchor="middle" dominant-baseline="middle" font-size="12"><title>{escape(item["name"])}</title>{escape(label)}</text>')
    if complete:
        elements.append(f'<polygon points="{polygon([120 * item["rating"] / maximum for item in categories])}" fill="#A89B8C" fill-opacity="0.3" stroke="#A89B8C" stroke-width="3"/>')
        caption = f"Self-assessed · scale 0–{maximum}"
    else:
        elements.append('<rect x="180" y="196" width="280" height="60" rx="8" fill="#0d1117" stroke="#A89B8C"/><text x="320" y="232" text-anchor="middle" font-size="17">Ratings unavailable</text>')
        caption = "Set every rating in scripts/skills.json"
    elements.append(f'<text x="320" y="419" text-anchor="middle" font-size="12">{escape(caption)}</text></g></svg>\n')
    return "".join(elements)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("scripts/skills.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("assets"))
    args = parser.parse_args(argv)
    try:
        config = validate_config(json.loads(args.config.read_text(encoding="utf-8")))
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for key in ("skills", "languages"):
            (args.output_dir / f"radar-{key}.svg").write_text(render_chart(config[key], config.get("max_rating", 5)), encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"radar: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
