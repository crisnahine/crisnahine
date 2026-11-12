#!/usr/bin/env python3
"""Writes every SVG in assets/. Run: python3 tools/gen_assets.py"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"
INK, PAPER, MUTED, LINE, LIME = "#0c0c0e", "#f2eee3", "#8f8f98", "#2a2a2f", "#d9ff3d"
SANS = '-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif'
MONO = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'
MONO_W = 0.6  # monospace advance per em, so widths of mono text are predictable

BASE_CSS = f""".s{{font-family:{SANS}}} .m{{font-family:{MONO}}} .pre{{white-space:pre}}
@media (prefers-reduced-motion: reduce) {{ .mv {{ animation: none !important; }} }}"""


def svg(name, w, h, title, desc, body, css=""):
    doc = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-labelledby="t d">\n'
        f"<!-- written by tools/gen_assets.py; edit that, not this file -->\n"
        f'<title id="t">{escape(title)}</title>\n<desc id="d">{escape(desc)}</desc>\n'
        f"<style>\n{BASE_CSS}\n{css}\n</style>\n{body}\n</svg>\n"
    )
    (OUT / name).write_text(doc)


def text(x, y, s, size, fill, cls="s", weight=400, extra=""):
    return (
        f'<text x="{x}" y="{y}" class="{cls} pre" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" {extra}>{escape(s)}</text>'
    )


WIPE_CSS = """.wipe{transform-box:fill-box;transform-origin:left center;animation:wipe 7s cubic-bezier(.6,0,.25,1) infinite}
@keyframes wipe { 0% {transform:scaleX(0)} 12% {transform:scaleX(0)} 22% {transform:scaleX(1)} 92% {transform:scaleX(1)} 100% {transform:scaleX(0)} }
.blink{animation:blink 1.1s steps(1,end) infinite}
@keyframes blink { 0% {opacity:1} 50% {opacity:0} }"""


def hero(name, w, h, lay):
    """lay: list of (kind, x, y, payload) rows so the wide and phone heroes share one renderer."""
    body = [f'<rect width="{w}" height="{h}" rx="16" fill="{INK}"/>']
    for kind, x, y, p in lay:
        if kind == "label":
            body.append(text(x, y, p, 12, MUTED, "m", 400, 'letter-spacing="1.8"'))
        elif kind == "name":
            body.append(text(x, y, p, lay_size(lay, "name"), PAPER, "s", 800, 'letter-spacing="-1"'))
        elif kind == "tag":
            size, lead, mark, tail = p
            cw = size * MONO_W
            mx = x + len(lead) * cw
            body.append(text(x, y, lead, size, PAPER, "m", 500))
            body.append(
                f'<rect class="mv wipe" x="{mx - 4:.1f}" y="{y - size * 0.86:.1f}" '
                f'width="{len(mark) * cw + 8:.1f}" height="{size * 1.16:.1f}" fill="{LIME}"/>'
            )
            body.append(text(round(mx, 1), y, mark, size, INK, "m", 700))
            body.append(text(round(mx + len(mark) * cw, 1), y, tail, size, PAPER, "m", 500))
            cx = mx + (len(mark) + len(tail)) * cw + 4
            body.append(
                f'<rect class="mv blink" x="{cx:.1f}" y="{y - size * 0.8:.1f}" width="{size * 0.5:.1f}" '
                f'height="{size:.1f}" fill="{LIME}"/>'
            )
        elif kind == "body":
            body.append(text(x, y, p, lay_size(lay, "body"), MUTED, "s", 400))
        elif kind == "rule":
            body.append(f'<path d="M{x} {y} H{p}" stroke="{LINE}"/>')
        elif kind == "foot":
            body.append(text(x, y, p, 12, MUTED, "m", 400, 'letter-spacing="1.2"'))
    svg(
        name, w, h,
        "Cris Nahine: AI engineer building tools for coding agents",
        "Cris Nahine. AI engineer and senior Ruby on Rails developer, building for the agent era: "
        "MCP servers, Claude Code plugins and code search that give AI coding agents real context "
        "about a codebase. A highlighter marks the words 'agent era'.",
        "\n".join(body), WIPE_CSS,
    )


def lay_size(lay, kind):
    return next(p for k, _, _, p in lay if k == kind + "_size")


def strip(n, title):
    w, h = 880, 56
    tx = 72
    end_title = tx + len(title) * (15 * MONO_W + 1.6)
    x0 = end_title + 24
    css = """.run{animation:run 4.8s cubic-bezier(.6,0,.25,1) infinite}
@keyframes run { 0% {stroke-dashoffset:8} 8% {stroke-dashoffset:8} 30% {stroke-dashoffset:-100} 100% {stroke-dashoffset:-100} }"""
    body = (
        f'<rect width="{w}" height="{h}" rx="10" fill="{INK}"/>'
        + text(32, 33, f"{n:02d}", 14, MUTED, "m", 500)
        + text(tx, 33, title.upper(), 15, PAPER, "m", 700, 'letter-spacing="1.6"')
        + f'<path d="M{x0:.1f} 28 H812" stroke="{LINE}"/>'
        + f'<path class="mv run" d="M{x0:.1f} 28 H812" pathLength="100" fill="none" stroke="{LIME}" '
        f'stroke-width="3" stroke-dasharray="8 300" stroke-dashoffset="8"/>'
        + f'<rect x="822" y="24" width="8" height="8" fill="{LIME}"/>'
    )
    slug = title.lower().replace(" ", "-").replace("&", "and")
    svg(f"strip-{slug}.svg", w, h, f"{n:02d}: {title}", f"Section {n:02d} of the profile: {title}.", body, css)


def badge(slug, label, value, accent=False):
    lw = 10 + len(label) * (11 * MONO_W + 1.32) + 10
    vw = len(value) * 12 * MONO_W + 20
    w, h = round(lw + vw), 24
    fill = LIME if accent else INK
    vcol = INK if accent else PAPER
    body = (
        f'<rect width="{w}" height="{h}" fill="{INK}"/>'
        f'<rect x="{lw:.1f}" width="{vw:.1f}" height="{h}" fill="{fill}"/>'
        + ("" if accent else f'<path d="M{lw:.1f} 6 V18" stroke="{LINE}"/>')
        + text(10, 16, label.upper(), 11, MUTED, "m", 400, 'letter-spacing="1.32"')
        + text(round(lw + 10, 1), 16.5, value, 12, vcol, "m", 600 if accent else 400)
    )
    svg(f"badge-{slug}.svg", w, h, f"{label}: {value}", f"Badge: {label} {value}.", body)


ICONS = {
    # 24x24 stroke paths, drawn in the scrutate icon style
    "mcp": '<rect x="4" y="4" width="16" height="7" rx="2"/><rect x="4" y="13" width="16" height="7" rx="2"/><path d="M8 7.5h.01M8 16.5h.01M12 7.5h4M12 16.5h4"/>',
    "plugin": '<path d="M9 3v4M15 3v4M6 7h12v4a6 6 0 0 1-12 0z M12 17v4"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/>',
    "rails": '<path d="M12 3 3 8l9 5 9-5z M3 13l9 5 9-5 M3 18l9 5 9-5" transform="translate(0 -1.5) scale(1 .92)"/>',
}


def icon(slug, paths):
    body = (
        f'<rect width="32" height="32" rx="6" fill="{INK}"/>'
        f'<g transform="translate(4 4)" stroke="{PAPER}" stroke-width="1.9" stroke-linecap="round" '
        f'stroke-linejoin="round" fill="none">{paths}</g>'
        f'<rect x="24" y="24" width="4" height="4" fill="{LIME}"/>'
    )
    svg(f"icon-{slug}.svg", 32, 32, slug, f"Icon: {slug}.", body)


def main():
    OUT.mkdir(exist_ok=True)
    hero("hero.svg", 880, 300, [
        ("label", 48, 58, "@CRISNAHINE  /  AI ENGINEER"),
        ("name_size", 0, 0, 58), ("name", 46, 126, "Cris Nahine"),
        ("tag", 48, 182, (26, "> building for the ", "agent era", ".")),
        ("body_size", 0, 0, 17),
        ("body", 48, 226, "AI engineer and senior Ruby on Rails developer. I build MCP servers, Claude Code"),
        ("body", 48, 250, "plugins and code search that give coding agents real context about your code."),
        ("rule", 48, 270, 832),
        ("foot", 48, 288, "rails-ai-context  ·  anatomiya  ·  chameleon"),
    ])
    hero("hero-phone.svg", 400, 330, [
        ("label", 24, 46, "@CRISNAHINE / AI ENGINEER"),
        ("name_size", 0, 0, 44), ("name", 22, 104, "Cris Nahine"),
        ("tag", 24, 152, (18, "> building for the ", "agent era", ".")),
        ("body_size", 0, 0, 15),
        ("body", 24, 196, "AI engineer and senior Ruby on Rails"),
        ("body", 24, 218, "developer. I build MCP servers, Claude"),
        ("body", 24, 240, "Code plugins and code search that give"),
        ("body", 24, 262, "coding agents real context about code."),
        ("rule", 24, 290, 376),
        ("foot", 24, 312, "rails-ai-context · anatomiya"),
    ])
    for i, t in enumerate(
        ["What I build", "Open source", "Contributions", "Shipped in production",
         "Stack", "Activity", "FAQ", "Work with me"], 1):
        strip(i, t)
    badge("now", "now", "AI engineer", accent=True)
    badge("focus", "focus", "agents, MCP, code intelligence")
    badge("base", "base", "Ruby on Rails")
    for slug, paths in ICONS.items():
        icon(slug, paths)


if __name__ == "__main__":
    main()
