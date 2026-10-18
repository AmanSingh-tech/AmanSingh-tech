"""Render the profile cards as light and dark SVGs.

Stdlib only, so the workflow needs no install step. Data comes from the public
contribution calendar and the REST API (GH_TOKEN is used when present to avoid
the anonymous rate limit).

    python scripts/build_cards.py <github-user> <out-dir>
"""

import datetime as dt
import json
import os
import re
import sys
import urllib.request
from collections import Counter
from html import escape

USER = sys.argv[1] if len(sys.argv) > 1 else "AmanSingh-tech"
OUT = sys.argv[2] if len(sys.argv) > 2 else "dist"

THEMES = {
    "light": {"bg": "#ffffff", "fg": "#111111", "muted": "#6b6b6b", "rule": "#e6e6e6",
              "bar": "#111111", "bar_dim": "#d4d4d4", "accent": "#e5352b",
              "langs": ["#111111", "#4a4a4a", "#808080", "#adadad", "#d4d4d4"]},
    "dark": {"bg": "#0d1117", "fg": "#f5f5f5", "muted": "#8b8b8b", "rule": "#262a30",
             "bar": "#f5f5f5", "bar_dim": "#30353c", "accent": "#ff5a4e",
             "langs": ["#f5f5f5", "#bdbdbd", "#8a8a8a", "#5c5c5c", "#3a3f45"]},
}

# GitHub serves README SVGs as <img>, which blocks web fonts and hover. Use
# system stacks so the cards look the same on every machine.
SANS = "-apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica, 'Segoe UI', Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

# Strong ease-out: fast start, so the motion reads as responsive, not sluggish.
EASE = "cubic-bezier(0.23, 1, 0.32, 1)"


def fetch(url, api=False):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-cards"})
    token = os.environ.get("GH_TOKEN")
    if api and token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode()


def contributions():
    html = fetch(f"https://github.com/users/{USER}/contributions")
    dates = dict(re.findall(r'data-date="([\d-]+)" id="(contribution-day-component-[\d-]+)"', html))
    dates = {cell: day for day, cell in dates.items()}
    counts = {}
    for cell, label in re.findall(r'for="(contribution-day-component-[\d-]+)"[^>]*>([^<]*)</tool-tip>', html):
        m = re.match(r"([\d,]+) contribution", label)
        if cell in dates:
            counts[dt.date.fromisoformat(dates[cell])] = int(m.group(1).replace(",", "")) if m else 0
    return dict(sorted(counts.items()))


def streaks(days):
    longest = run = 0
    for n in days.values():
        run = run + 1 if n else 0
        longest = max(longest, run)
    current = 0
    items = list(days.values())
    # Today counts only once it has a contribution; an empty today doesn't break the streak yet.
    if items and items[-1] == 0:
        items = items[:-1]
    for n in reversed(items):
        if not n:
            break
        current += 1
    return current, longest


def languages():
    try:
        repos = json.loads(fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner", api=True))
    except Exception as err:
        # A rate limit shouldn't cost the whole card; it renders without the language row.
        print(f"skipping languages: {err}", file=sys.stderr)
        return []
    total = Counter()
    for repo in repos:
        if repo["fork"] or repo["name"] == USER:
            continue
        try:
            total.update(json.loads(fetch(repo["languages_url"], api=True)))
        except Exception:
            continue
    # Markup and notebooks inflate byte counts without saying much about what I write.
    for noise in ("HTML", "CSS", "SCSS", "Jupyter Notebook", "Dockerfile", "Shell", "Makefile", "Procfile"):
        total.pop(noise, None)
    top = total.most_common(5)
    whole = sum(n for _, n in top) or 1
    return [(name, n / whole) for name, n in top if n / whole >= 0.01]


def stagger(i, step=60):
    return f'style="animation-delay:{i * step}ms"'


def style(t):
    return f"""<style>
  .sans {{ font-family: {SANS}; }}
  .mono {{ font-family: {MONO}; letter-spacing: 0.06em; }}
  .in {{ opacity: 0; animation: in 700ms {EASE} forwards; }}
  .reveal {{ animation: reveal 1100ms {EASE} 250ms both; }}
  @keyframes in {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes reveal {{ from {{ clip-path: inset(0 100% 0 0); }} to {{ clip-path: inset(0 0 0 0); }} }}
  @media (prefers-reduced-motion: reduce) {{
    .in {{ animation: fade 300ms ease forwards; }}
    .reveal {{ animation: none; }}
    @keyframes fade {{ to {{ opacity: 1; }} }}
  }}
</style>"""


def hero(t):
    w, h = 850, 300
    cols = [
        ("PREVIOUSLY", "Google · AlgoUniversity", "software engineering intern"),
        ("NOW", "AI agents that ask", "before they act"),
        ("WRITES", "TypeScript · Python", "Next.js, FastAPI, Node"),
    ]
    col_svg = ""
    for i, (label, line1, line2) in enumerate(cols):
        x = 32 + i * 270
        col_svg += f"""
  <g class="in" {stagger(5 + i)}>
    <line x1="{x}" y1="206" x2="{x + 240}" y2="206" stroke="{t['fg']}" stroke-width="1.5"/>
    <text x="{x}" y="230" class="mono" font-size="11" fill="{t['muted']}">{label}</text>
    <text x="{x}" y="254" class="sans" font-size="16" font-weight="600" fill="{t['fg']}">{escape(line1)}</text>
    <text x="{x}" y="275" class="sans" font-size="16" fill="{t['muted']}">{escape(line2)}</text>
  </g>"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Aman Kumar Singh. Full-stack engineer building AI agents.">
{style(t)}
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{t['bg']}" stroke="{t['rule']}"/>
  <g class="in" {stagger(0)}>
    <text x="32" y="44" class="mono" font-size="11" fill="{t['muted']}">AMAN KUMAR SINGH</text>
    <text x="{w - 32}" y="44" class="mono" font-size="11" fill="{t['muted']}" text-anchor="end">FULL-STACK · AI AGENTS</text>
  </g>
  <g class="in" {stagger(1)}>
    <text x="28" y="124" class="sans" font-size="76" font-weight="700" letter-spacing="-3.5" fill="{t['fg']}">Aman Singh<tspan fill="{t['accent']}">.</tspan></text>
  </g>
  <text x="32" y="164" class="sans in" {stagger(3)} font-size="18" fill="{t['muted']}">I build software that does the boring part for you, then gets out of the way.</text>
{col_svg}
</svg>
"""


def stats(t, days, langs):
    w, h = 850, 330 if langs else 240
    total = sum(days.values())
    current, longest = streaks(days)
    weekday = Counter()
    for d, n in days.items():
        weekday[d.strftime("%A")] += n
    busiest = weekday.most_common(1)[0][0] if total else "—"

    # Weekly totals, oldest first. Calendar weeks start on Sunday, like GitHub's grid.
    weeks = Counter()
    for d, n in days.items():
        weeks[d - dt.timedelta(days=(d.weekday() + 1) % 7)] += n
    weekly = [weeks[k] for k in sorted(weeks)]
    peak = max(weekly) or 1
    peak_i = weekly.index(peak)

    chart_x, chart_w, base, chart_h = 32, w - 64, 214, 72
    gap = 3
    bw = (chart_w - gap * (len(weekly) - 1)) / max(len(weekly), 1)
    bars = ""
    for i, n in enumerate(weekly):
        bh = max(2, n / peak * chart_h)
        fill = t["accent"] if i == peak_i and n else (t["bar"] if n else t["bar_dim"])
        bars += f'<rect x="{chart_x + i * (bw + gap):.1f}" y="{base - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{fill}"/>'

    figures = [(f"{total:,}", "CONTRIBUTIONS, PAST YEAR"), (str(current), "DAY STREAK, CURRENT"),
               (str(longest), "DAY STREAK, LONGEST"), (busiest, "BUSIEST DAY")]
    fig_svg = ""
    for i, (value, label) in enumerate(figures):
        x = 32 + i * 202
        fig_svg += f"""
  <g class="in" {stagger(1 + i)}>
    <text x="{x}" y="96" class="sans" font-size="40" font-weight="700" letter-spacing="-1.5" fill="{t['fg']}">{escape(value)}</text>
    <text x="{x}" y="118" class="mono" font-size="10" fill="{t['muted']}">{label}</text>
  </g>"""

    lang_svg, x = "", 32.0
    lx = 32.0
    for i, (name, share) in enumerate(langs):
        seg = share * (w - 64)
        lang_svg += f'<rect x="{x:.1f}" y="262" width="{max(seg - 2, 1):.1f}" height="8" fill="{t["langs"][i]}"/>'
        x += seg
        label = f"{escape(name)} {share:.0%}"
        lang_svg += f'<rect x="{lx:.1f}" y="290" width="8" height="8" fill="{t["langs"][i]}"/>'
        lang_svg += f'<text x="{lx + 14:.1f}" y="298" class="mono" font-size="11" fill="{t["fg"]}">{label}</text>'
        lx += 14 + len(label) * 7.2 + 24

    lang_block = f"""  <g class="in" {stagger(6)}>
    <text x="32" y="250" class="mono" font-size="10" fill="{t['muted']}">LANGUAGES, BY BYTES ACROSS MY REPOS</text>
    {lang_svg}
  </g>""" if langs else ""

    updated = dt.date.today().strftime("%d %b %Y").upper()
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{total} contributions in the last year, current streak {current} days, longest {longest} days.">
{style(t)}
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{t['bg']}" stroke="{t['rule']}"/>
  <g class="in" {stagger(0)}>
    <text x="32" y="40" class="mono" font-size="11" fill="{t['muted']}">ACTIVITY</text>
    <text x="{w - 32}" y="40" class="mono" font-size="11" fill="{t['muted']}" text-anchor="end">UPDATED {updated}</text>
  </g>
{fig_svg}
  <g class="reveal">{bars}</g>
  <line x1="32" y1="{base}" x2="{w - 32}" y2="{base}" stroke="{t['rule']}"/>
{lang_block}
</svg>
"""


def main():
    os.makedirs(OUT, exist_ok=True)
    days, langs = contributions(), languages()
    if not days:
        sys.exit("No contribution data parsed; GitHub's markup may have changed.")
    for name, t in THEMES.items():
        suffix = "" if name == "light" else "-dark"
        with open(os.path.join(OUT, f"hero{suffix}.svg"), "w") as f:
            f.write(hero(t))
        with open(os.path.join(OUT, f"stats{suffix}.svg"), "w") as f:
            f.write(stats(t, days, langs))
    print(f"{len(days)} days, {sum(days.values())} contributions, langs={langs}")


if __name__ == "__main__":
    main()
