# Publish `rachts/rachts`

This folder is the repository root: upload its **contents**, not a nested `rachts` directory. No repository has been created or pushed for you.

## Setup

1. **Create the profile repository.** While signed into GitHub as `rachts`, create a public repository named exactly `rachts`. Keep its default branch named `main` (the workflows also support other default names except `output`). Add the contents of this folder, including `.github/workflows/`, `scripts/`, `assets/`, README, and this guide. If that repository already exists, review and merge these files rather than replacing unrelated work.

2. **Enable Actions and write access.** In the repository's **Settings → Actions → General**, allow the actions used below. Under Workflow permissions, select **Read and write permissions** if your organisation permits it. All workflows explicitly request `contents: write`. Branch rules must allow the workflow token to commit generated assets; don't disable unrelated protection rules. These workflows do not create PRs.

3. **Add `METRICS_TOKEN`.** Create an expiring classic personal access token belonging to `rachts`, with **`read:user` and `repo`** scopes. Add it under **Settings → Secrets and variables → Actions → New repository secret**, named `METRICS_TOKEN`. Never put the value in files, workflow YAML, screenshots or chat. `repo` is broad and can read private repositories: review that access and the third-party Metrics action before enabling it. A public-only profile may work with narrower scopes; the requested configuration uses the scopes above. Rotate the token before expiry. Other workflows use the automatically provided `GITHUB_TOKEN`; do not create that secret yourself.

4. **Run each workflow once on the default branch.** Open **Actions**, select the named workflow, then **Run workflow**. Run them one at a time and wait for completion:

   | Workflow | Result |
   | --- | --- |
   | Update radar charts (`radar.yml`) | `assets/radar-skills.svg`, `assets/radar-languages.svg` |
   | Update stats card (`stats-cards.yml`) | `assets/stats.svg` |
   | Update profile metrics (`metrics.yml`) | `assets/metrics.isocalendar.svg`, `assets/metrics.languages.svg` |
   | Update contribution snakes (`snake.yml`) | `assets/snake.svg`, `assets/snake-dark.svg`; also `snake.svg` and `snake-dark.svg` on `output` |

   Verify successful runs, generated-asset commits, and the README on your profile. Starter SVGs deliberately say “awaiting first refresh”, not zero contributions. GitHub caches image renders, so a successful commit may take time to appear. Metrics achievements are inferred by that plugin, **not official GitHub achievement badges**.

5. **Swap in your data.** Edit `scripts/skills.json`: labels already reflect your supplied interests and languages; replace each `null` with your own rating from `0` to `5`. Each chart stays unconfigured until all its ratings are present; missing is not zero. These are self-ratings, not GitHub language usage. In README, replace the learning and fun-fact TODOs, add confirmed repository links around project names, and replace live-link TODOs only when you have real URLs. Re-run radar after committing JSON changes. Update radar alt text and remove the configuration note once complete. Update the stats alt text after its first refresh.

6. **Optionally add your portrait.** Install Python 3.12 and run from this repository root:

   ```bash
   python3 -m venv .venv
   .venv/bin/python -m pip install -r scripts/requirements.txt
   # Drop your own photo at assets/photo.jpg, then:
   .venv/bin/python scripts/make_portrait.py
   ```

   Add `<img src="assets/portrait.svg" width="260" alt="Rachit Kumar Tiwari, dot-matrix portrait">` inside the top centred README block. The generator uses purple circles on a transparent background; adjust `--grid 80` or `--size 480` if desired. The original photo is gitignored; commit only the generated portrait if you want it public. No photo or fabricated portrait is included.

7. **Preview and check locally.** Core generators have no third-party dependencies. Pillow is only for the optional portrait.

   ```bash
   python3 scripts/radar.py
   python3 -m unittest discover -s scripts -v
   python3 scripts/preview.py
   python3 -m http.server 8000 --bind 127.0.0.1
   ```

   Open `http://localhost:8000/preview.html`, or open `preview.html` directly. Rebuild it after editing README. Browser/system light and dark settings exercise the `<picture>` snake variants. The HTML preview approximates the layout; check the actual GitHub README before publishing. Run tests with `.venv/bin/python` to include the Pillow test. To regenerate a stats placeholder deliberately, run `python3 scripts/stats_cards.py --placeholder` (this replaces `assets/stats.svg`). `python3 scripts/starter_assets.py` only fills missing calendar/language/achievement/snake placeholders, never overwrites live renders.

## Daily refresh and action versions

GitHub workflow cron uses **UTC**, not your computer's time zone. Schedules only run from the default branch and can be delayed; GitHub may disable scheduled runs after 60 days of inactivity in public repositories.

| Workflow | UTC daily | Kolkata daily |
| --- | --- | --- |
| Metrics | 03:17 | 08:47 |
| Snake | 04:19 | 09:49 |
| Stats | 05:23 | 10:53 |
| Radar | 05:41 | 11:11 |

- `actions/checkout@v4`, `actions/setup-python@v5`, and `Platane/snk@v3` use major-version pins.
- **Necessary exception:** `lowlighter/metrics` publishes no `@v3` major tag. `@v3.34` is an existing release tag; using `@v3` would fail. Neither a fabricated tag nor the moving `@latest` branch is used. Reassess this exception if upstream introduces a major tag. Release/major tags are mutable, not immutable supply-chain pins; reviewed commit SHAs are stronger if you later relax the major-pin rule.
- All publishers share a concurrency group and do not cancel an active run. GitHub can replace an older *pending* run when several queue, so dispatch initial runs sequentially; re-dispatch any pending run that was cancelled.
- Metrics writes into `/metrics_renders` with `output_action: none`; the final step copies only the three intended SVGs into a fresh checkout and commits with the repository token. It does not use your PAT for pushing. Explicit target lists prevent accidental commits of private files or logs.
- Fresh worktrees keep generated files isolated and use the newest default branch. Bounded rebase/retry handles a concurrent human push; no force pushes are used. The snake's first `output` publication creates an orphan branch inside an isolated worktree, removing tracked source files **only in that temporary worktree**. Existing output history is preserved.
- Metrics plugin errors fail the job before publishing either supported file. The achievements plugin is intentionally disabled because its current implementation queries deprecated GitHub Projects (classic). API/stat errors preserve the previous cards instead of replacing them with fabricated values. Inspect the Actions logs and token expiry/permissions if images remain stale. Some third-party plugins can break as GitHub APIs change.

## Visual and data notes

- Palette: primary `#A89B8C`, secondary `#C9BFAE`. Generated cards use opaque `#0d1117` panels and light labels so they remain readable in both GitHub themes. Snake uses explicit light/dark variants. Metrics calendar contribution colours are mapped to warm taupe shades; technology icons and Metrics language artwork retain upstream semantic colours.
- GitHub strips custom README CSS, so global monospace fonts and a dark page background cannot be enforced. Headings, command blocks and labels give the README its terminal feel; the standalone preview uses monospace throughout. Badges form one inline row on wide screens and wrap naturally on mobile.
- The banner cycles through the supplied full name, an internship-seeking role, and the full name encoded as UTF-8/ASCII binary. That last line is 170 characters, so the SVG uses a wide viewBox and scales down. The static name directly underneath stays legible on small screens. You can shorten the binary line if you prefer larger animated text, but that changes the full-name requirement.
- Banner (`readme-typing-svg`), badges (Shields), and the single toolbox strip (skillicons.dev) remain external by design. Radar, calendar, stats, languages, achievements and snake are **repository-hosted**, not public Vercel stats endpoints. External services still need network access and can be unavailable.
- Stats are a timestamped public REST snapshot: profile public repository count (including forks), followers, following, owned public non-fork repository count, and stars on those non-forks. Pagination is supported. No commit total, streak, rank or skill level is guessed.
- Metrics receives a potentially private-capable PAT. Review the resulting language/achievement summaries before keeping them public; remove the `repo` scope if you choose public-only access and re-test. Do not infer that an SVG contains only public data merely because the repository is public.
- This is a layout-inspired original profile, not a copy of the reference person's bio or projects. No licence is assumed for your repository; add one explicitly if desired.
