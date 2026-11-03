#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Light-UI-UX — Original 3-Direction Interactive Style Explorer Generator (`scripts/style_explorer.py`)
Generates a standalone single-file `style-explorer.html` for side-by-side or full-stage comparison
of 3 distinct UI/UX directions (either synthesized directly from `light-arsenal.db` benchmarks
or bundled from custom HTML direction files via `--manifest`).
"""

import argparse
import base64
import html
import json
import mimetypes
import re
import sqlite3
import sys
import zlib
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = WORKSPACE_ROOT / "assets" / "light-arsenal.db"


def zdecomp(blob: bytes | str | None) -> str:
    if not blob:
        return ""
    if isinstance(blob, str):
        return blob
    return zlib.decompress(blob).decode("utf-8", errors="replace")


def zjson(blob: bytes | str | None, default):
    txt = zdecomp(blob)
    if not txt:
        return default
    try:
        return json.loads(txt)
    except Exception:
        return default


def inline_local_assets(html_str: str, base_dir: Path) -> str:
    """Inline relative local images and CSS stylesheets into Base64 data URIs."""
    def repl_attr(m):
        attr, quote, rel = m.group(1), m.group(2), m.group(3)
        if rel.startswith(("http://", "https://", "data:", "#", "//")):
            return m.group(0)
        fp = (base_dir / rel).resolve()
        if not fp.is_file() or fp.stat().st_size > 15 * 1024 * 1024:
            return m.group(0)
        mime, _ = mimetypes.guess_type(fp.name)
        mime = mime or "application/octet-stream"
        b64 = base64.b64encode(fp.read_bytes()).decode("ascii")
        return f"{attr}={quote}data:{mime};base64,{b64}{quote}"

    return re.sub(r'\b(src|poster)=(["\'])([^"\']+)\2', repl_attr, html_str)


def pick_colors(colors_list: list, theme: str) -> dict:
    hex_items = []
    if isinstance(colors_list, list):
        for c in colors_list:
            if isinstance(c, dict) and str(c.get("value", "")).startswith("#"):
                hex_items.append((c.get("name", ""), c["value"], c.get("role", "").lower()))

    is_dark = theme == "dark"
    bg = "#090a0d" if is_dark else "#fbfbfa"
    surface = "#13151a" if is_dark else "#f2f2ee"
    ink = "#f5f6f8" if is_dark else "#141413"
    muted = "#8e929f" if is_dark else "#686763"
    accent = "#3b82f6" if is_dark else "#1d4ed8"

    for name, val, role in hex_items:
        if any(k in role for k in ["background", "canvas", "page"]):
            bg = val
            break
    for name, val, role in hex_items:
        if val != bg and any(k in role for k in ["surface", "card", "panel", "secondary", "stage"]):
            surface = val
            break
    for name, val, role in hex_items:
        if val not in (bg, surface) and any(k in role for k in ["headline", "ink", "primary text", "body", "copy"]):
            ink = val
            break
    for name, val, role in hex_items:
        if val not in (bg, surface, ink) and any(k in role for k in ["accent", "cta", "button", "link", "brand"]):
            accent = val
            break

    return {"bg": bg, "surface": surface, "ink": ink, "muted": muted, "accent": accent, "all": hex_items[:8]}


def synthesize_direction_html(idx: int, bench: dict, product_name: str, headline: str, subhead: str, cta: str) -> str:
    pal = bench["palette"]
    font_main = bench["font_main"]
    font_mono = bench["font_mono"]
    radius = bench["card_radius"]
    btn_radius = bench["btn_radius"]

    def supporting_copy(css_class: str) -> str:
        text = subhead.strip()
        return f'<p class="{css_class}">{html.escape(text)}</p>' if text else ""

    # 3 Distinct Hero Archetypes (Never 3 identical left-text/right-image clones!)
    archetype_idx = idx % 3
    if archetype_idx == 0:
        # Archetype A: Editorial Typographic Monument
        body_markup = f"""
        <div class="shell arch-a">
          <header class="topbar">
            <span class="brand">{html.escape(product_name)}</span>
            <nav class="nav"><span>Architecture</span><span>Benchmarks</span><span>Pricing</span></nav>
            <button class="btn-ghost">Sign In</button>
          </header>
          <main class="stage-a">
            <div class="col-main">
              <h1 class="display-title">{html.escape(headline)}</h1>
              <div class="stagger-row">
                {supporting_copy("lead")}
                <div class="cta-cluster">
                  <button class="btn-primary">{html.escape(cta)}</button>
                </div>
              </div>
            </div>
          </main>
        </div>
        """
    elif archetype_idx == 1:
        # Archetype B: Center Iconic Object / Interactive Stage Slice
        body_markup = f"""
        <div class="shell arch-b">
          <header class="topbar">
            <span class="brand">{html.escape(product_name)}</span>
          </header>
          <main class="stage-b">
            <h1 class="center-title">{html.escape(headline)}</h1>
            {supporting_copy("center-lead")}
            <div class="center-actions">
              <button class="btn-primary">{html.escape(cta)}</button>
            </div>
            <section class="interactive-slice">
              <div class="slice-toolbar">
                <span class="slice-tab active">Pipeline Topology</span>
                <span class="slice-tab">Token Matrix</span>
                <span class="slice-tab">Telemetry</span>
              </div>
              <div class="slice-canvas">
                <div class="node-card">
                  <div class="node-head"><span>Ingest Engine</span><code>READY</code></div>
                  <div class="bar-track"><div class="bar-fill" style="width:84%"></div></div>
                  <div class="node-foot"><span>1,238 ops/s</span><span>0.4ms</span></div>
                </div>
                <div class="node-card">
                  <div class="node-head"><span>Optical Synthesizer</span><code>ACTIVE</code></div>
                  <div class="bar-track"><div class="bar-fill" style="width:92%"></div></div>
                  <div class="node-foot"><span>OKLCH 8-Step</span><span>AA 7.4:1</span></div>
                </div>
                <div class="node-card">
                  <div class="node-head"><span>Cross-Stack AST</span><code>SYNCED</code></div>
                  <div class="bar-track"><div class="bar-fill" style="width:76%"></div></div>
                  <div class="node-foot"><span>React · Vue · RN</span><span>60fps</span></div>
                </div>
              </div>
            </section>
          </main>
        </div>
        """
    else:
        # Archetype C: Swiss Architectural Bento Grid / High-Contrast Precision
        body_markup = f"""
        <div class="shell arch-c">
          <header class="topbar-grid">
            <div class="cell-brand">{html.escape(product_name)}</div>
            <div class="cell-cta"><button class="btn-primary">{html.escape(cta)}</button></div>
          </header>
          <main class="bento-stage">
            <section class="bento-hero">
              <h1 class="bento-title">{html.escape(headline)}</h1>
              {supporting_copy("bento-lead")}
            </section>
            <section class="bento-visual">
              <div class="dial-stage">
                <svg viewBox="0 0 240 240" class="precision-svg">
                  <circle cx="120" cy="120" r="96" fill="none" stroke="currentColor" stroke-opacity="0.14" stroke-width="1.5"/>
                  <circle cx="120" cy="120" r="68" fill="none" stroke="currentColor" stroke-opacity="0.24" stroke-dasharray="4 6" stroke-width="1.5"/>
                  <path d="M 120 24 A 96 96 0 0 1 216 120" fill="none" stroke="{pal['accent']}" stroke-width="3.5" stroke-linecap="round"/>
                  <circle cx="120" cy="120" r="6" fill="{pal['accent']}"/>
                </svg>
              </div>
            </section>
          </main>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>
  :root {{
    --bg: {pal['bg']};
    --surface: {pal['surface']};
    --ink: {pal['ink']};
    --muted: {pal['muted']};
    --accent: {pal['accent']};
    --font-main: '{font_main}', -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Noto Sans CJK SC', sans-serif;
    --font-mono: '{font_mono}', 'JetBrains Mono', ui-monospace, monospace;
    --radius-card: {radius};
    --radius-btn: {btn_radius};
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--ink);
    font-family: var(--font-main);
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
    font-variant-numeric: tabular-nums;
    overflow-x: hidden;
  }}
  .shell {{ max-width: 1320px; margin: 0 auto; padding: 28px 48px 56px; min-height: 100vh; display: flex; flex-direction: column; }}
  .topbar {{ display: flex; align-items: center; justify-content: space-between; padding-bottom: 28px; border-bottom: 1px solid color-mix(in srgb, var(--ink) 12%, transparent); }}
  .brand {{ font-weight: 700; font-size: 18px; letter-spacing: -0.01em; }}
  .nav {{ display: flex; gap: 32px; font-size: 14px; color: var(--muted); }}
  .btn-primary {{
    background: var(--accent);
    color: #ffffff;
    border: none;
    padding: 12px 24px;
    border-radius: var(--radius-btn);
    font-weight: 600;
    font-size: 14px;
    cursor: pointer;
    transition: transform 160ms cubic-bezier(0.23, 1, 0.32, 1);
  }}
  .btn-primary:active {{ transform: scale(0.97); }}
  .btn-ghost {{
    background: transparent;
    color: var(--ink);
    border: 1px solid color-mix(in srgb, var(--ink) 18%, transparent);
    padding: 9px 18px;
    border-radius: var(--radius-btn);
    font-size: 13px;
    cursor: pointer;
  }}
  /* Archetype A */
  .stage-a {{ display: grid; grid-template-columns: minmax(0, 860px); padding-top: 72px; align-items: center; flex: 1; }}
  .display-title {{ font-size: clamp(44px, 5.2vw, 76px); line-height: 1.28; font-weight: 600; text-wrap: balance; margin-bottom: 36px; }}
  .stagger-row {{ max-width: 580px; display: flex; flex-direction: column; gap: 28px; }}
  .lead {{ font-size: 17px; line-height: 1.72; color: var(--muted); text-wrap: pretty; }}
  .cta-cluster {{ display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }}

  /* Archetype B */
  .stage-b {{ display: flex; flex-direction: column; align-items: center; text-align: center; padding-top: 48px; flex: 1; }}
  .center-title {{ font-size: clamp(40px, 4.6vw, 64px); line-height: 1.28; max-width: 820px; margin-bottom: 20px; text-wrap: balance; }}
  .center-lead {{ font-size: 16px; line-height: 1.7; color: var(--muted); max-width: 560px; margin-bottom: 28px; }}
  .center-actions {{ margin-bottom: 44px; }}
  .interactive-slice {{ width: 100%; background: var(--surface); border-radius: var(--radius-card); padding: 20px; box-shadow: 0 0 0 1px color-mix(in srgb, var(--ink) 12%, transparent); text-align: left; }}
  .slice-toolbar {{ display: flex; align-items: center; gap: 12px; padding-bottom: 16px; border-bottom: 1px solid color-mix(in srgb, var(--ink) 10%, transparent); margin-bottom: 20px; font-size: 13px; }}
  .slice-tab {{ padding: 6px 12px; border-radius: 6px; color: var(--muted); }}
  .slice-tab.active {{ background: var(--bg); color: var(--ink); font-weight: 600; }}
  .slice-canvas {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
  .node-card {{ background: var(--bg); border-radius: calc(max(4px, var(--radius-card) - 8px)); padding: 18px; box-shadow: 0 0 0 1px color-mix(in srgb, var(--ink) 8%, transparent); display: flex; flex-direction: column; gap: 14px; }}
  .node-head {{ display: flex; justify-content: space-between; font-size: 14px; font-weight: 600; }}
  .node-head code {{ font-family: var(--font-mono); font-size: 11px; color: var(--accent); }}
  .bar-track {{ height: 6px; background: var(--surface); border-radius: 99px; overflow: hidden; }}
  .bar-fill {{ height: 100%; background: var(--accent); border-radius: 99px; }}
  .node-foot {{ display: flex; justify-content: space-between; font-size: 12px; color: var(--muted); font-family: var(--font-mono); }}

  /* Archetype C */
  .topbar-grid {{ display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 24px; padding-bottom: 20px; border-bottom: 1px solid color-mix(in srgb, var(--ink) 16%, transparent); }}
  .cell-brand {{ font-weight: 700; font-size: 18px; }}
  .bento-stage {{ display: grid; grid-template-columns: 1.35fr 1fr; gap: 20px; padding-top: 32px; flex: 1; }}
  .bento-hero {{ background: var(--surface); border-radius: var(--radius-card); padding: 44px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 0 0 1px color-mix(in srgb, var(--ink) 10%, transparent); }}
  .bento-title {{ font-size: clamp(36px, 4vw, 56px); line-height: 1.28; font-weight: 600; text-wrap: balance; }}
  .bento-lead {{ font-size: 16px; line-height: 1.7; color: var(--muted); max-width: 48ch; }}
  .bento-visual {{ background: var(--surface); border-radius: var(--radius-card); padding: 32px; display: flex; align-items: center; justify-content: center; position: relative; box-shadow: 0 0 0 1px color-mix(in srgb, var(--ink) 10%, transparent); }}
  .dial-stage {{ position: relative; width: 220px; height: 220px; display: flex; align-items: center; justify-content: center; }}
  .precision-svg {{ width: 100%; height: 100%; }}

  @media (max-width: 640px) {{
    .shell {{ padding: 20px; }}
    .stage-a, .slice-canvas, .bento-stage {{ grid-template-columns: 1fr; gap: 20px; }}
    .nav {{ display: none; }}
  }}
</style>
</head>
<body>
{body_markup}
</body>
</html>"""


def load_benchmarks_from_db(ids: list[str], query: str) -> list[dict]:
    conn = sqlite3.connect(DB_PATH.resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = []
    if ids:
        for bid in ids:
            r = cur.execute("SELECT * FROM benchmarks WHERE id = ?", (bid.strip(),)).fetchone()
            if r:
                rows.append(dict(r))
    if len(rows) < 3:
        like_q = f"%{query}%"
        extra = cur.execute(
            "SELECT * FROM benchmarks WHERE name LIKE ? OR tags_zh LIKE ? OR note_zh LIKE ? LIMIT 12",
            (like_q, like_q, like_q),
        ).fetchall()
        for r in extra:
            if len(rows) >= 3:
                break
            if not any(x["id"] == r["id"] for x in rows):
                rows.append(dict(r))
    if len(rows) < 3:
        fallback = cur.execute("SELECT * FROM benchmarks LIMIT 3").fetchall()
        for r in fallback:
            if len(rows) < 3 and not any(x["id"] == r["id"] for x in rows):
                rows.append(dict(r))
    conn.close()

    directions = []
    archetype_labels = [
        "Editorial Typographic Monument",
        "Interactive Workbench Slice",
        "Swiss Architectural Bento",
    ]
    for i, r in enumerate(rows[:3]):
        cols = zjson(r.get("colors_json"), [])
        typo = zjson(r.get("typography_json"), {})
        lay = zjson(r.get("layout_json"), {})
        pal = pick_colors(cols, r.get("theme", "light"))
        fonts = typo.get("fonts", []) if isinstance(typo, dict) else []
        f_main = fonts[0].get("family", "Inter") if fonts and isinstance(fonts[0], dict) else "Inter"
        f_mono = fonts[1].get("family", "JetBrains Mono") if len(fonts) > 1 and isinstance(fonts[1], dict) else "JetBrains Mono"
        radii = lay.get("radii", {}) if isinstance(lay, dict) else {}
        c_rad = radii.get("cards") or radii.get("containers") or ("16px" if i != 2 else "4px")
        b_rad = radii.get("buttons") or radii.get("pills") or "9999px"

        directions.append({
            "id": r["id"],
            "label": f"Direction {chr(65 + i)} — {r['name']}",
            "name": r["name"],
            "archetype": archetype_labels[i % 3],
            "theme": r.get("theme", "light"),
            "tags": r.get("tags_zh", ""),
            "note": r.get("note_zh", "") or f"Inspired by {r['name']} ({r.get('source_url', '')})",
            "palette": pal,
            "font_main": f_main,
            "font_mono": f_mono,
            "card_radius": c_rad,
            "btn_radius": b_rad,
        })
    return directions


def build_explorer_shell(title: str, directions: list[dict]) -> str:
    manifest_json = json.dumps(directions, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(title)} — Light-UI-UX Style Explorer</title>
<style>
  :root {{
    --ui-bg: #0c0d10;
    --ui-panel: #15171c;
    --ui-border: rgba(255,255,255,0.09);
    --ui-ink: #f3f4f6;
    --ui-muted: #9ca3af;
    --ui-accent: #3b82f6;
    --spring: linear(0, 0.45 12%, 0.82 26%, 0.98 42%, 1.01 58%, 1);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--ui-bg);
    color: var(--ui-ink);
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'PingFang SC', sans-serif;
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    font-variant-numeric: tabular-nums;
  }}
  header.explorer-bar {{
    height: 54px;
    background: var(--ui-panel);
    border-bottom: 1px solid var(--ui-border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    gap: 16px;
    flex-shrink: 0;
  }}
  .bar-left {{ display: flex; align-items: center; gap: 14px; }}
  .badge {{ font-size: 11px; font-family: ui-monospace, monospace; padding: 3px 8px; border-radius: 4px; background: rgba(59,130,246,0.16); color: #60a5fa; font-weight: 600; }}
  .bar-title {{ font-size: 14px; font-weight: 600; }}
  .bar-tabs, .bar-controls {{ display: flex; align-items: center; gap: 6px; }}
  .tab-btn {{
    background: transparent;
    color: var(--ui-muted);
    border: 1px solid transparent;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 150ms ease;
  }}
  .tab-btn:hover {{ color: var(--ui-ink); background: rgba(255,255,255,0.04); }}
  .tab-btn.active {{ color: var(--ui-ink); background: rgba(255,255,255,0.09); border-color: var(--ui-border); }}
  .copy-btn {{
    background: var(--ui-accent);
    color: #fff;
    border: none;
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
  }}
  main.workspace {{
    flex: 1;
    display: grid;
    grid-template-columns: 1fr 310px;
    min-height: 0;
  }}
  main.workspace.compare-mode {{
    grid-template-columns: 1fr;
  }}
  main.workspace.compare-mode aside.inspector {{
    display: none;
  }}
  .stage-area {{
    position: relative;
    overflow: auto;
    padding: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 18px;
  }}
  .compare-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
    width: 100%;
    height: 100%;
  }}
  .dir-card {{
    background: var(--ui-panel);
    border: 1px solid var(--ui-border);
    border-radius: 10px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    height: 100%;
  }}
  .dir-card-head {{
    padding: 10px 14px;
    border-bottom: 1px solid var(--ui-border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12px;
  }}
  .dir-card-head strong {{ font-size: 13px; }}
  .dir-frame-wrap {{
    flex: 1;
    position: relative;
    overflow: hidden;
    background: #000;
  }}
  iframe.preview-frame {{
    border: none;
    transform-origin: top left;
    position: absolute;
    top: 0;
    left: 0;
  }}
  aside.inspector {{
    background: var(--ui-panel);
    border-left: 1px solid var(--ui-border);
    padding: 20px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }}
  .insp-section {{ display: flex; flex-direction: column; gap: 8px; }}
  .insp-label {{ font-size: 11px; font-family: ui-monospace, monospace; color: var(--ui-muted); text-transform: uppercase; }}
  .swatch-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }}
  .swatch {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    border-radius: 6px;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--ui-border);
    font-size: 11px;
    font-family: ui-monospace, monospace;
  }}
  .swatch-dot {{ width: 16px; height: 16px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.2); flex-shrink: 0; }}
  .spec-kv {{ font-size: 12px; color: var(--ui-ink); line-height: 1.5; }}
</style>
</head>
<body>
<header class="explorer-bar">
  <div class="bar-left">
    <span class="badge">LIGHT-UI-UX EXPLORER</span>
    <span class="bar-title">{html.escape(title)}</span>
  </div>
  <div class="bar-tabs" id="mode-tabs">
    <button class="tab-btn active" data-view="compare">Side-by-Side (All 3)</button>
  </div>
  <div class="bar-controls">
    <button class="tab-btn active" data-vp="desktop">Desktop 1440×900</button>
    <button class="tab-btn" data-vp="mobile">Mobile 390×844</button>
    <button class="copy-btn" id="copy-lock">Copy Direction Contract</button>
  </div>
</header>
<main class="workspace compare-mode" id="workspace">
  <div class="stage-area" id="stage-area"></div>
  <aside class="inspector" id="inspector"></aside>
</main>
<script id="directions-data" type="application/json">{manifest_json}</script>
<script>
  const directions = JSON.parse(document.getElementById('directions-data').textContent);
  let activeView = 'compare'; // 'compare' or index 0..2
  let viewport = 'desktop';   // 'desktop' or 'mobile'

  const tabsEl = document.getElementById('mode-tabs');
  directions.forEach((d, idx) => {{
    const btn = document.createElement('button');
    btn.className = 'tab-btn';
    btn.dataset.view = String(idx);
    btn.textContent = d.label;
    tabsEl.appendChild(btn);
  }});

  function scaleFrames() {{
    const targetW = viewport === 'desktop' ? 1440 : 390;
    const targetH = viewport === 'desktop' ? 900 : 844;
    document.querySelectorAll('.dir-frame-wrap').forEach(wrap => {{
      const iframe = wrap.querySelector('iframe');
      if (!iframe) return;
      const rect = wrap.getBoundingClientRect();
      const scale = Math.min(rect.width / targetW, rect.height / targetH);
      iframe.style.width = targetW + 'px';
      iframe.style.height = targetH + 'px';
      iframe.style.transform = `scale(${{scale}})`;
      iframe.style.left = Math.max(0, (rect.width - targetW * scale) / 2) + 'px';
      iframe.style.top = Math.max(0, (rect.height - targetH * scale) / 2) + 'px';
    }});
  }}

  function renderInspector(d) {{
    const el = document.getElementById('inspector');
    if (!d) {{ el.innerHTML = ''; return; }}
    const p = d.palette || {{}};
    const swatches = [
      ['bg', p.bg], ['surface', p.surface], ['ink', p.ink], ['muted', p.muted], ['accent', p.accent]
    ].filter(x => x[1]).map(([k, v]) => `
      <div class="swatch"><span class="swatch-dot" style="background:${{v}}"></span><span>${{k}}: ${{v}}</span></div>
    `).join('');
    el.innerHTML = `
      <div class="insp-section">
        <span class="insp-label">Benchmark Origin</span>
        <div class="spec-kv"><strong>${{d.label}}</strong> (${{d.id}})<br/>Archetype: ${{d.archetype || 'Custom'}}</div>
      </div>
      ${{d.note && d.note.trim() ? `<div class="insp-section"><span class="insp-label">Design Rationale</span><div class="spec-kv">${{d.note}}</div></div>` : ''}}
      <div class="insp-section">
        <span class="insp-label">Color Tokens</span>
        <div class="swatch-grid">${{swatches}}</div>
      </div>
      <div class="insp-section">
        <span class="insp-label">Typography & Shape</span>
        <div class="spec-kv">
          • Display/Body: <code>${{d.font_main || 'System'}}</code><br/>
          • Monospace: <code>${{d.font_mono || 'JetBrains Mono'}}</code><br/>
          • Card Radius: <code>${{d.card_radius || '16px'}}</code><br/>
          • Button Radius: <code>${{d.btn_radius || '9999px'}}</code>
        </div>
      </div>
    `;
  }}

  function renderStage() {{
    const ws = document.getElementById('workspace');
    const stage = document.getElementById('stage-area');
    stage.innerHTML = '';

    if (activeView === 'compare') {{
      ws.classList.add('compare-mode');
      const grid = document.createElement('div');
      grid.className = 'compare-grid';
      directions.forEach((d, idx) => {{
        const card = document.createElement('div');
        card.className = 'dir-card';
        card.innerHTML = `
          <div class="dir-card-head">
            <strong>${{d.label}}</strong>
            <button class="tab-btn" onclick="selectDirection(${{idx}})">Expand →</button>
          </div>
          <div class="dir-frame-wrap"></div>
        `;
        const iframe = document.createElement('iframe');
        iframe.className = 'preview-frame';
        iframe.srcdoc = d.html;
        card.querySelector('.dir-frame-wrap').appendChild(iframe);
        grid.appendChild(card);
      }});
      stage.appendChild(grid);
    }} else {{
      ws.classList.remove('compare-mode');
      const idx = Number(activeView);
      const d = directions[idx];
      const card = document.createElement('div');
      card.className = 'dir-card';
      card.style.width = '100%';
      card.style.height = '100%';
      card.innerHTML = `<div class="dir-frame-wrap"></div>`;
      const iframe = document.createElement('iframe');
      iframe.className = 'preview-frame';
      iframe.srcdoc = d.html;
      card.querySelector('.dir-frame-wrap').appendChild(iframe);
      stage.appendChild(card);
      renderInspector(d);
    }}
    requestAnimationFrame(scaleFrames);
  }}

  window.selectDirection = function(idx) {{
    activeView = String(idx);
    document.querySelectorAll('#mode-tabs .tab-btn').forEach(b => {{
      b.classList.toggle('active', b.dataset.view === activeView);
    }});
    renderStage();
  }};

  document.querySelectorAll('#mode-tabs .tab-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      activeView = btn.dataset.view;
      document.querySelectorAll('#mode-tabs .tab-btn').forEach(b => b.classList.toggle('active', b === btn));
      renderStage();
    }});
  }});

  document.querySelectorAll('[data-vp]').forEach(btn => {{
    btn.addEventListener('click', () => {{
      viewport = btn.dataset.vp;
      document.querySelectorAll('[data-vp]').forEach(b => b.classList.toggle('active', b === btn));
      scaleFrames();
    }});
  }});

  document.getElementById('copy-lock').addEventListener('click', () => {{
    const idx = activeView === 'compare' ? 0 : Number(activeView);
    const d = directions[idx];
    const contract = JSON.stringify({{
      selected_direction: d.label,
      benchmark_id: d.id,
      archetype: d.archetype,
      palette: d.palette,
      font_main: d.font_main,
      font_mono: d.font_mono,
      card_radius: d.card_radius,
      btn_radius: d.btn_radius
    }}, null, 2);
    navigator.clipboard.writeText(contract);
    const btn = document.getElementById('copy-lock');
    btn.textContent = 'Copied Contract!';
    setTimeout(() => btn.textContent = 'Copy Direction Contract', 1600);
  }});

  window.addEventListener('resize', scaleFrames);
  renderStage();
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Light-UI-UX 3-Direction Style Explorer HTML Generator")
    parser.add_argument("--benchmarks", default="", help="Comma-separated benchmark IDs (e.g., ref-b36d5c7c-9b2,ref-486c3132-9ff,ref-cc38369a-41e)")
    parser.add_argument("--query", default="科技感 极简", help="Search query to auto-select 3 benchmarks if --benchmarks is omitted")
    parser.add_argument("--product", default="Light Studio", help="Product / Brand Name")
    parser.add_argument("--headline", default="Precision Interfaces Engineered at the Speed of Thought", help="Hero headline")
    parser.add_argument("--subhead", default="", help="Optional supporting copy; omitted by default")
    parser.add_argument("--cta", default="Launch Workbench", help="Primary CTA label")
    parser.add_argument("--manifest", help="Optional path to custom manifest.json with custom HTML files")
    parser.add_argument("--out", required=True, help="Output file path for style-explorer.html")

    args = parser.parse_args()
    out_fp = Path(args.out)

    if args.manifest:
        m_fp = Path(args.manifest)
        m_data = json.loads(m_fp.read_text(encoding="utf-8"))
        directions = []
        for idx, item in enumerate(m_data.get("directions", [])):
            html_fp = (m_fp.parent / item["file"]).resolve()
            raw_html = html_fp.read_text(encoding="utf-8", errors="replace")
            inlined = inline_local_assets(raw_html, html_fp.parent)
            directions.append({
                "id": item.get("id", f"dir-{idx+1}"),
                "label": item.get("label", f"Direction {chr(65+idx)}"),
                "name": item.get("name", f"Direction {chr(65+idx)}"),
                "archetype": item.get("archetype", "Custom Prototype"),
                "note": item.get("note", ""),
                "palette": item.get("palette", {}),
                "font_main": item.get("font_main", "Inter"),
                "font_mono": item.get("font_mono", "JetBrains Mono"),
                "card_radius": item.get("card_radius", "16px"),
                "btn_radius": item.get("btn_radius", "9999px"),
                "html": inlined,
            })
        title = m_data.get("title", args.product)
    else:
        ids = [x.strip() for x in args.benchmarks.split(",") if x.strip()]
        directions = load_benchmarks_from_db(ids, args.query)
        for idx, d in enumerate(directions):
            d["html"] = synthesize_direction_html(idx, d, args.product, args.headline, args.subhead, args.cta)
        title = args.product

    final_html = build_explorer_shell(title, directions)
    out_fp.parent.mkdir(parents=True, exist_ok=True)
    out_fp.write_text(final_html, encoding="utf-8")
    print(f"[OK] Generated 3-direction interactive Style Explorer ({len(final_html):,} bytes) at: {out_fp.resolve()}")


if __name__ == "__main__":
    main()
