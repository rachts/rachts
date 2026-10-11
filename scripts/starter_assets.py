"""Create missing starter visuals only; never overwrite a live render."""
from html import escape
from pathlib import Path


def placeholder(title, note, background="#0d1117", foreground="#e6edf3"):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="180" viewBox="0 0 900 180" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(note)} No activity data has been fetched.</desc>
<rect width="900" height="180" rx="12" fill="{background}"/>
<path d="M24 40h24" stroke="#8A2BE2" stroke-width="4"/>
<g fill="{foreground}" font-family="ui-monospace,monospace"><text x="24" y="80" font-size="20">{escape(title)}</text>
<text x="24" y="120" font-size="15">{escape(note)}</text></g></svg>'''


if __name__ == "__main__":
    assets = Path("assets")
    assets.mkdir(exist_ok=True)
    for name, title, workflow in [
        ("metrics.isocalendar.svg", "~/ contribution calendar", "metrics.yml"),
        ("metrics.languages.svg", "~/ repository languages", "metrics.yml"),
        ("metrics.achievements.svg", "~/ metrics achievements", "metrics.yml"),
        ("snake.svg", "~/ contribution snake", "snake.yml"),
        ("snake-dark.svg", "~/ contribution snake", "snake.yml"),
    ]:
        target = assets / name
        if not target.exists():
            colours = ("#f6f8fa", "#1f2328") if name == "snake.svg" else ()
            target.write_text(placeholder(title, f"Awaiting first refresh — run {workflow} in Actions.", *colours))
            print(f"Created {target}")
