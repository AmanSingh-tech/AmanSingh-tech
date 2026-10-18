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
        ("PREVIOUSLY", "Google · AlgoUniversity", "applied AI & SWE intern"),
        ("NOW", "CS at MIT Bengaluru", "building AI agents"),
        ("WRITES", "Java · TypeScript · Python", "Spring AI, Next.js, FastAPI"),
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
    <text x="{w - 32}" y="44" class="mono" font-size="11" fill="{t['muted']}" text-anchor="end">BENGALURU, INDIA</text>
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


SCENE = {
    "light": {"wall": "#f4f2ee", "floor": "#e8e2d8", "sky": "#d9e8f1", "glow": "#fff4dc",
              "wood": "#c9b8a0", "chair": "#d6d1c8", "skin": "#e9b996", "hair": "#1c1c1c",
              "screen": "#16191d", "code": "#5d636b", "paper": "#ffe2dc"},
    "dark": {"wall": "#121821", "floor": "#0e131a", "sky": "#0a1a2e", "glow": "#ffcf87",
             "wood": "#3a3128", "chair": "#262c35", "skin": "#c9997a", "hair": "#0b0b0b",
             "screen": "#0b0e12", "code": "#4a525c", "paper": "#ffd3cb"},
}


def desk(name, t, current_streak):
    """A little me at my desk, seen from behind. Day in light mode, after hours in dark."""
    s, night = SCENE[name], name == "dark"
    w, h = 850, 340
    cx = 365  # the character, monitor and chair share this centre line

    lines = ["Hey! I'm Aman.", "Ex-Google, ex-AlgoUniversity.", "LeetCode 1998, top 8%.",
             "CS at MIT Bengaluru.", "Building agents that ask first."]
    if current_streak > 1:
        lines.insert(4, f"Day {current_streak} of my streak.")
    slot = 3.2
    cycle = slot * len(lines)
    edge = 100 / len(lines)
    bubble = "".join(
        f'<text x="509" y="73" text-anchor="middle" class="sans msg" font-size="15" font-weight="600" '
        f'fill="{t["fg"]}" style="animation-delay:{i * slot:.1f}s">{escape(m)}</text>'
        for i, m in enumerate(lines))

    # Monitor code: lines type in one after another, then the screen clears and starts over.
    code = ""
    widths = [96, 64, 120, 80, 52, 108, 72]
    for i, cw in enumerate(widths):
        indent = 12 if i in (1, 2, 4, 5) else 0
        fill = t["accent"] if i == 3 else s["code"]
        code += (f'<rect x="{283 + indent}" y="{112 + i * 12}" width="{cw}" height="5" rx="2.5" fill="{fill}" '
                 f'class="type" style="animation-delay:{i * 0.55:.2f}s"/>')

    window = (f"""
  <rect x="640" y="36" width="150" height="176" rx="4" fill="{s['sky']}"/>
  <circle cx="742" cy="78" r="16" fill="#f5f1e6"/><circle cx="750" cy="72" r="14" fill="{s['sky']}"/>
  {''.join(f'<circle cx="{x}" cy="{y}" r="1.6" fill="#f5f1e6" class="twinkle" style="animation-delay:{d}s"/>'
           for x, y, d in [(668, 60, 0), (700, 112, 0.8), (676, 150, 1.6), (760, 140, 2.4), (718, 50, 1.2)])}"""
              if night else f"""
  <rect x="640" y="36" width="150" height="176" rx="4" fill="{s['sky']}"/>
  <circle cx="752" cy="74" r="18" fill="#fff8e7"/>
  <polygon points="640,212 790,212 720,{h - 50} 470,{h - 50}" fill="{s['glow']}" opacity="0.55"/>""")
    window += f"""
  <rect x="640" y="36" width="150" height="176" rx="4" fill="none" stroke="{t['fg']}" stroke-opacity="0.85" stroke-width="3"/>
  <line x1="715" y1="36" x2="715" y2="212" stroke="{t['fg']}" stroke-opacity="0.85" stroke-width="3"/>
  <line x1="640" y1="124" x2="790" y2="124" stroke="{t['fg']}" stroke-opacity="0.85" stroke-width="3"/>"""

    lamp = f"""
  <circle cx="205" cy="168" r="70" fill="url(#lampglow)"/>
  <path d="M188 160 L222 160 L214 140 L196 140 Z" fill="{t['fg']}" opacity="0.9"/>
  <line x1="205" y1="160" x2="205" y2="226" stroke="{t['fg']}" stroke-width="3" opacity="0.9"/>
  <rect x="192" y="224" width="26" height="5" rx="2" fill="{t['fg']}" opacity="0.9"/>""" if night else ""

    books = "".join(
        f'<rect x="{x}" y="{96 - bh}" width="{bw}" height="{bh}" rx="1.5" fill="{c}"/>'
        for x, bw, bh, c in [(104, 12, 40, t["fg"]), (118, 10, 34, t["muted"]), (130, 14, 44, t["accent"]),
                             (146, 9, 30, t["muted"]), (157, 12, 38, t["fg"])])

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="An illustration of Aman at a desk, typing, with a speech bubble that says hello.">
<defs>
  <radialGradient id="lampglow"><stop offset="0" stop-color="{s['glow']}" stop-opacity="0.35"/><stop offset="1" stop-color="{s['glow']}" stop-opacity="0"/></radialGradient>
  <radialGradient id="screenglow"><stop offset="0" stop-color="#9fb4ff" stop-opacity="{0.18 if night else 0}"/><stop offset="1" stop-color="#9fb4ff" stop-opacity="0"/></radialGradient>
  <clipPath id="card"><rect width="{w}" height="{h}" rx="12"/></clipPath>
</defs>
<style>
  .sans {{ font-family: {SANS}; }}
  .mono {{ font-family: {MONO}; letter-spacing: 0.06em; }}
  .msg {{ opacity: 0; animation: msg {cycle:.1f}s {EASE} infinite both; }}
  .type {{ animation: type 5s steps(8, end) infinite both; }}
  .hand-l {{ animation: tap 2.4s ease-in-out infinite; }}
  .hand-r {{ animation: tap 2.4s ease-in-out 0.12s infinite; }}
  .head {{ transform-origin: {cx}px 236px; animation: glance 9s cubic-bezier(0.77, 0, 0.175, 1) infinite; }}
  .steam {{ animation: steam 3s ease-out infinite; }}
  .twinkle {{ animation: twinkle 3.2s ease-in-out infinite; }}
  @keyframes msg {{
    0% {{ opacity: 0; transform: translateY(4px); filter: blur(2px); }}
    {edge * 0.12:.2f}% {{ opacity: 1; transform: none; filter: blur(0); }}
    {edge * 0.88:.2f}% {{ opacity: 1; transform: none; filter: blur(0); }}
    {edge:.2f}%, 100% {{ opacity: 0; transform: translateY(-4px); filter: blur(2px); }}
  }}
  @keyframes type {{ 0% {{ clip-path: inset(0 100% 0 0); }} 18%, 92% {{ clip-path: inset(0 0 0 0); }} 100% {{ clip-path: inset(0 100% 0 0); }} }}
  @keyframes tap {{
    0%, 6%, 12%, 18%, 24%, 30%, 36%, 100% {{ transform: none; }}
    3%, 9%, 15%, 21%, 27%, 33% {{ transform: translateY(-2px); }}
  }}
  @keyframes glance {{ 0%, 62% {{ transform: none; }} 70%, 84% {{ transform: rotate(-5deg) translateX(-2px); }} 92%, 100% {{ transform: none; }} }}
  @keyframes steam {{ 0% {{ opacity: 0; transform: translateY(4px); }} 30% {{ opacity: 0.7; }} 100% {{ opacity: 0; transform: translateY(-10px); }} }}
  @keyframes twinkle {{ 0%, 100% {{ opacity: 0.35; }} 50% {{ opacity: 1; }} }}
  @media (prefers-reduced-motion: reduce) {{
    .type, .hand-l, .hand-r, .head, .steam, .twinkle {{ animation: none; }}
    .msg {{ animation-name: msgfade; }}
    @keyframes msgfade {{ 0%, {edge:.2f}%, 100% {{ opacity: 0; }} {edge * 0.12:.2f}%, {edge * 0.88:.2f}% {{ opacity: 1; }} }}
  }}
</style>
<g clip-path="url(#card)">
  <rect width="{w}" height="{h}" fill="{s['wall']}"/>
  <rect y="{h - 50}" width="{w}" height="50" fill="{s['floor']}"/>
  <line x1="0" y1="{h - 50}" x2="{w}" y2="{h - 50}" stroke="{t['rule']}"/>
  {window}

  <line x1="96" y1="97" x2="250" y2="97" stroke="{t['fg']}" stroke-width="3"/>
  {books}
  <rect x="196" y="72" width="22" height="24" rx="3" fill="{t['muted']}" opacity="0.5"/>
  <path d="M207 72 C200 58 192 62 196 54 M207 72 C212 56 222 60 218 50" stroke="#5f8f6a" stroke-width="3" fill="none" stroke-linecap="round"/>

  <rect x="560" y="112" width="48" height="60" fill="{t['bg']}" stroke="{t['rule']}"/>
  <rect x="569" y="121" width="14" height="14" fill="{t['accent']}"/>
  <rect x="569" y="146" width="30" height="3" fill="{t['muted']}"/><rect x="569" y="154" width="20" height="3" fill="{t['muted']}"/>
  {lamp}

  <circle cx="{cx}" cy="150" r="140" fill="url(#screenglow)"/>
  <rect x="{cx - 97}" y="96" width="194" height="122" rx="7" fill="{t['fg']}"/>
  <rect x="{cx - 91}" y="102" width="182" height="110" rx="3" fill="{s['screen']}"/>
  {code}
  <rect x="{cx - 8}" y="218" width="16" height="14" fill="{t['fg']}"/>
  <g transform="rotate(-6 {cx - 82} 190)">
    <rect x="{cx - 108}" y="170" width="50" height="40" fill="{s['paper']}"/>
    <text x="{cx - 83}" y="187" text-anchor="middle" class="mono" font-size="8" fill="#5a2a24">STREAK</text>
    <text x="{cx - 83}" y="202" text-anchor="middle" class="sans" font-size="13" font-weight="700" fill="#5a2a24">{current_streak}d</text>
  </g>

  <rect x="150" y="230" width="430" height="10" rx="2" fill="{s['wood']}"/>
  <rect x="166" y="240" width="8" height="{h - 290}" fill="{s['wood']}"/>
  <rect x="556" y="240" width="8" height="{h - 290}" fill="{s['wood']}"/>
  <path d="M506 206 h22 v18 a6 6 0 0 1 -6 6 h-10 a6 6 0 0 1 -6 -6 z" fill="{t['bg']}" stroke="{t['fg']}" stroke-width="2"/>
  <path d="M528 211 a6 6 0 0 1 0 12" fill="none" stroke="{t['fg']}" stroke-width="2"/>
  <path class="steam" d="M513 200 c-4 -6 4 -8 0 -14 M521 200 c-4 -6 4 -8 0 -14" stroke="{t['muted']}" stroke-width="1.8" fill="none" stroke-linecap="round"/>

  <path class="hand-l" d="M300 262 Q292 236 318 228" stroke="{t['accent']}" stroke-width="18" stroke-linecap="round" fill="none"/>
  <path class="hand-r" d="M430 262 Q438 236 412 228" stroke="{t['accent']}" stroke-width="18" stroke-linecap="round" fill="none"/>
  <path d="M{cx - 64} {h - 40} C{cx - 70} 262 {cx - 52} 232 {cx} 230 C{cx + 52} 232 {cx + 70} 262 {cx + 64} {h - 40} Z" fill="{t['accent']}"/>
  <path d="M{cx - 30} 236 Q{cx} 256 {cx + 30} 236" stroke="#000" stroke-opacity="0.18" stroke-width="3" fill="none"/>
  <g class="head">
    <circle cx="{cx - 47}" cy="194" r="9" fill="{s['skin']}"/>
    <circle cx="{cx + 47}" cy="194" r="9" fill="{s['skin']}"/>
    <circle cx="{cx}" cy="186" r="48" fill="{s['hair']}"/>
    <path d="M{cx - 30} 146 q8 -14 20 -8 q6 -16 22 -6 q12 -10 18 8" fill="{s['hair']}"/>
    <path d="M{cx - 20} 168 q12 -8 26 -2 M{cx - 6} 196 q14 -6 26 2" stroke="#ffffff" stroke-opacity="0.08" stroke-width="3" fill="none" stroke-linecap="round"/>
  </g>
  <rect x="{cx - 56}" y="268" width="112" height="44" rx="14" fill="{s['chair']}"/>
  <rect x="{cx - 4}" y="312" width="8" height="18" fill="{s['chair']}"/>

  <g>
    <path d="M404 82 L386 132 L428 85" fill="{t['bg']}" stroke="{t['rule']}" stroke-linejoin="round"/>
    <rect x="378" y="46" width="262" height="40" rx="20" fill="{t['bg']}" stroke="{t['rule']}"/>
    <path d="M405 85.5 L427 85.5" stroke="{t['bg']}" stroke-width="2"/>
    {bubble}
  </g>

  <text x="24" y="28" class="mono" font-size="10" fill="{t['muted']}">AT THE DESK</text>
  <text x="{w - 24}" y="28" class="mono" font-size="10" fill="{t['muted']}" text-anchor="end">BENGALURU · {"AFTER HOURS" if night else "AFTERNOON"}</text>
</g>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="none" stroke="{t['rule']}"/>
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
        with open(os.path.join(OUT, f"desk{suffix}.svg"), "w") as f:
            f.write(desk(name, t, streaks(days)[0]))
    print(f"{len(days)} days, {sum(days.values())} contributions, langs={langs}")


if __name__ == "__main__":
    main()
