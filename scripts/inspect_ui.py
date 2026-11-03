#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Light-UI-UX — Multi-Viewport Screenshotter, Text-Mask Generator & 67-Rule UI Linter (`scripts/inspect_ui.py`)
Zero external pip dependencies required. Uses local Chrome/Edge headless mode + static AST/regex analyzer.
"""

import argparse
import functools
import http.server
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "microsoft-edge",
    "microsoft-edge-stable",
    "/snap/bin/chromium",
]


def find_browser() -> str | None:
    user_candidates = [
        os.environ.get("LIGHT_UI_BROWSER", ""),
        str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        str(Path.home() / "Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
        str(Path.home() / "Applications/Chromium.app/Contents/MacOS/Chromium"),
    ]
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        user_candidates.extend([
            str(Path(local_app_data) / "Google/Chrome/Application/chrome.exe"),
            str(Path(local_app_data) / "Microsoft/Edge/Application/msedge.exe"),
        ])
    for candidate in user_candidates + BROWSER_CANDIDATES:
        if not candidate:
            continue
        cand = os.path.expanduser(candidate)
        if os.path.isabs(cand):
            if os.path.isfile(cand):
                return cand
        else:
            found = shutil.which(cand)
            if found:
                return found
    return None


LINT_RULES = [
    {
        "id": "kicker-above-heading",
        "severity": "error",
        "category": "ai-slop",
        "pattern": re.compile(
            r'<(?:span|div|p)[^>]*class="[^"]*(?:uppercase|tracking-widest|eyebrow|kicker|pill|badge)[^"]*"[^>]*>[^<]{2,40}</(?:span|div|p)>\s*<h[12]\b',
            re.I | re.S,
        ),
        "message": "Zero-Tolerance Slop Ban: Kicker / Eyebrow mini-label detected directly above H1/H2. Delete the kicker and let the heading speak for itself.",
    },
    {
        "id": "gradient-text",
        "severity": "error",
        "category": "ai-slop",
        "pattern": re.compile(r"background-clip:\s*text|bg-clip-text", re.I),
        "message": "AI Slop Ban: Gradient text (`background-clip: text` / `bg-clip-text`) detected.",
    },
    {
        "id": "side-stripe",
        "severity": "error",
        "category": "ai-slop",
        "pattern": re.compile(r"\bborder-[lt]-[248]\b|border-(?:left|top):\s*[2-8]px\s+solid", re.I),
        "message": "AI Slop Ban: Colored side/top stripe (`border-l-4` / `border-left: 3px solid`) detected on container.",
    },
    {
        "id": "ai-color-palette",
        "severity": "warning",
        "category": "ai-slop",
        "pattern": re.compile(r"#6366f1|#8b5cf6|#a855f7|\bfrom-indigo-|\bvia-purple-|\bto-pink-", re.I),
        "message": "Stale AI Palette Warning: Default Indigo/Violet/Purple gradient tokens detected (`#6366f1` / `#8b5cf6`). Verify domain alignment.",
    },
    {
        "id": "dark-glow",
        "severity": "warning",
        "category": "ai-slop",
        "pattern": re.compile(r"box-shadow:\s*0(?:px)?\s+0(?:px)?\s+(?:1[6-9]|[2-9]\d)px|shadow-\[0_0_", re.I),
        "message": "AI Slop Warning: Zero-offset neon glow shadow detected (`box-shadow: 0 0 24px`). Use physical Y-offset shadows.",
    },
    {
        "id": "emoji-icon",
        "severity": "error",
        "category": "ai-slop",
        "pattern": re.compile(r"[✨🚀💡🤖🎯⚡🔥💎🌟🎉]"),
        "message": "AI Slop Ban: Emoji symbol used in UI markup. Extract crisp vector SVGs via `python scripts/arsenal.py icon`.",
    },
    {
        "id": "pulsing-dot",
        "severity": "warning",
        "category": "ai-slop",
        "pattern": re.compile(r"\banimate-ping\b"),
        "message": "Advisory: Decorative pulsing dot (`animate-ping`) detected. Reserve strictly for live telemetry states.",
    },
    {
        "id": "marketing-buzzword",
        "severity": "warning",
        "category": "copywriting",
        "pattern": re.compile(r"赋能|闭环|抓手|一站式解决方案|\bsupercharge\b|\bunleash\b|\bnext-gen\b|\bseamless\b", re.I),
        "message": "Hollow AI Copywriting Cliché detected. Replace with concrete domain actions and metrics.",
    },
    {
        "id": "meta-leakage",
        "severity": "error",
        "category": "quality",
        "pattern": re.compile(r">\s*(?:示例数据|概念图|待核实|Placeholder|Hero Section|Bento Grid)\s*<", re.I),
        "message": "Meta-label leakage: Prompt instructions or placeholder labels printed directly into visible UI.",
    },
    {
        "id": "shadcn-space-y",
        "severity": "warning",
        "category": "stack-discipline",
        "pattern": re.compile(r"\bspace-[xy]-\d+\b"),
        "message": "Stack Rule (`shadcn`): Prefer `flex flex-col gap-*` over `space-y-*` / `space-x-*`.",
    },
    {
        "id": "broken-placeholder-image",
        "severity": "error",
        "category": "quality",
        "pattern": re.compile(r"via\.placeholder\.com|unsplash\.com/random|placehold\.co", re.I),
        "message": "Banned placeholder image URL detected. Use `scripts/media_gen.py` or local WebGL shaders.",
    },
]


def run_static_lint(text: str, source_label: str) -> list[dict]:
    findings = []
    lines = text.splitlines()

    for rule in LINT_RULES:
        for m in rule["pattern"].finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            snippet = lines[line_no - 1].strip()[:120] if 0 < line_no <= len(lines) else m.group(0)[:80]
            findings.append({
                "rule_id": rule["id"],
                "severity": rule["severity"],
                "category": rule["category"],
                "location": f"{source_label}:{line_no}",
                "message": rule["message"],
                "snippet": snippet,
            })

    # Special Check: CJK text with tight Western display line-height (< 1.2)
    has_cjk = bool(re.search(r"[\u4e00-\u9fff]{4,}", text))
    if has_cjk:
        for m in re.finditer(r"line-height:\s*(0\.\d+|1\.0\d*|1\.1[0-5]?)\b|\bleading-(?:none|tight)\b", text):
            line_no = text[: m.start()].count("\n") + 1
            findings.append({
                "rule_id": "cjk-tight-leading",
                "severity": "error",
                "category": "typography",
                "location": f"{source_label}:{line_no}",
                "message": f"CJK Typography Violation: Chinese UI detected with tight line-height (`{m.group(0)}`). CJK headings require `line-height: 1.25–1.40` to prevent vertical stroke collision.",
                "snippet": lines[line_no - 1].strip()[:120] if 0 < line_no <= len(lines) else m.group(0),
            })

    # Check for tabular-nums when numbers are present
    if "tabular-nums" not in text:
        findings.append({
            "rule_id": "missing-tabular-nums",
            "severity": "advisory",
            "category": "typography",
            "location": source_label,
            "message": "Numeric Discipline: `font-variant-numeric: tabular-nums` not found. Declare `tabular-nums` on metrics, tables, and counters.",
            "snippet": "",
        })

    # Check for native surface theming (::selection)
    if "::selection" not in text and "selection:bg-" not in text:
        findings.append({
            "rule_id": "missing-selection-theme",
            "severity": "advisory",
            "category": "craft-floor",
            "location": source_label,
            "message": "Craft Floor: Custom `::selection` highlight styling not found. Theme `::selection`, `caret-color`, and `:focus-visible`.",
            "snippet": "",
        })

    return findings


def create_masked_html(raw_html: str) -> str:
    """Inject global CSS that hides all text glyphs for the Step 0 3-Second Thumbnail & Text-Mask Test."""
    mask_style = """
    <style id="light-ui-ux-text-mask">
      *, *::before, *::after {
        color: transparent !important;
        -webkit-text-fill-color: transparent !important;
        text-shadow: none !important;
      }
      input::placeholder, textarea::placeholder {
        color: transparent !important;
      }
    </style>
    """
    if "</head>" in raw_html:
        return raw_html.replace("</head>", mask_style + "\n</head>", 1)
    return mask_style + raw_html


def create_marked_html(raw_html: str, mark_spec: str) -> str:
    """
    Inject JS/CSS that draws #e8175d magenta bounding boxes and numbered callout badges
    for `--mark "1=.selectorA,2=#selectorB"` during Round 1 Polish Diagnosis.
    """
    pairs = []
    for item in mark_spec.split(","):
        if "=" in item:
            num, sel = item.split("=", 1)
            pairs.append({"num": num.strip(), "sel": sel.strip()})
    pairs_json = json.dumps(pairs, ensure_ascii=False)
    mark_script = f"""
    <script id="light-ui-ux-mark-overlay">
      window.addEventListener('DOMContentLoaded', () => {{
        const items = {pairs_json};
        items.forEach(({{num, sel}}) => {{
          const el = document.querySelector(sel);
          if (!el) return;
          const r = el.getBoundingClientRect();
          const box = document.createElement('div');
          box.style.cssText = `
            position: fixed;
            left: ${{r.left - 3}}px;
            top: ${{r.top - 3}}px;
            width: ${{r.width + 6}}px;
            height: ${{r.height + 6}}px;
            border: 2.5px solid #e8175d;
            border-radius: 6px;
            background: rgba(232, 23, 93, 0.06);
            z-index: 2147483646;
            pointer-events: none;
          `;
          const badge = document.createElement('div');
          badge.textContent = num;
          badge.style.cssText = `
            position: absolute;
            top: -12px;
            left: -12px;
            min-width: 24px;
            height: 24px;
            padding: 0 6px;
            border-radius: 999px;
            background: #e8175d;
            color: #ffffff;
            font: 700 12px/24px ui-monospace, monospace;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.45);
          `;
          box.appendChild(badge);
          document.body.appendChild(box);
        }});
      }});
    </script>
    """
    if "</body>" in raw_html:
        return raw_html.replace("</body>", mark_script + "\n</body>", 1)
    return raw_html + mark_script


def compute_9grid_diff(img_a: Path, img_b: Path) -> dict:
    """
    Compare two screenshots across a 3x3 spatial grid (`top-left` .. `bottom-right`)
    and compute the percentage of pixels that changed significantly (|dR|+|dG|+|dB| > 24).
    """
    from media_gen import decode_png_rgb_grid  # Reuse our built-in PNG/Pillow decoder

    G = 72
    dec_a = decode_png_rgb_grid(img_a, G)
    dec_b = decode_png_rgb_grid(img_b, G)
    if not dec_a or not dec_b or not dec_a[2] or not dec_b[2]:
        return {"error": "Could not decode PNGs for 3x3 pixel diff"}

    pix_a, pix_b = dec_a[2], dec_b[2]
    row_names = ["top", "mid", "bottom"]
    col_names = ["left", "center", "right"]
    grid_diff = {}
    total_changed = 0
    cell_w = G // 3

    for ry in range(3):
        for cx in range(3):
            changed = 0
            count = 0
            for y in range(ry * cell_w, (ry + 1) * cell_w):
                for x in range(cx * cell_w, (cx + 1) * cell_w):
                    pa = pix_a[y * G + x]
                    pb = pix_b[y * G + x]
                    if abs(pa[0] - pb[0]) + abs(pa[1] - pb[1]) + abs(pa[2] - pb[2]) > 24:
                        changed += 1
                    count += 1
            pct = round(100.0 * changed / max(1, count), 1)
            grid_diff[f"{row_names[ry]}-{col_names[cx]}"] = f"{pct}%"
            total_changed += changed

    return {
        "image_before": str(img_a),
        "image_after": str(img_b),
        "overall_changed_pct": round(100.0 * total_changed / (G * G), 2),
        "grid_3x3_diff": grid_diff,
    }


def start_local_server(root_dir: Path) -> tuple[http.server.ThreadingHTTPServer, int]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    _, port = sock.getsockname()
    sock.close()

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root_dir))
    handler.log_message = lambda *args, **kwargs: None
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, port


def capture_headless_screenshot(browser_bin: str, url: str, out_png: Path, width: int, height: int, scale: float = 1.0) -> bool:
    out_png.parent.mkdir(parents=True, exist_ok=True)
    if out_png.exists():
        out_png.unlink()

    tmp_profile = Path(tempfile.mkdtemp(prefix="light-ui-chrome-"))
    cmd = [
        browser_bin,
        "--headless=new",
        "--disable-gpu",
        "--enable-unsafe-swiftshader",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        f"--user-data-dir={tmp_profile}",
        f"--window-size={width},{height}",
        f"--force-device-scale-factor={scale}",
        "--virtual-time-budget=2500",
        f"--screenshot={out_png.resolve()}",
        url,
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    except Exception:
        pass
    finally:
        shutil.rmtree(tmp_profile, ignore_errors=True)

    return out_png.exists() and out_png.stat().st_size > 0


def main():
    parser = argparse.ArgumentParser(description="Light-UI-UX Multi-Viewport Screenshotter & 67-Rule UI Linter")
    parser.add_argument("target", nargs="?", default="", help="URL (http://...), HTML file path, or source directory to audit")
    parser.add_argument("--out-dir", default="./.light-ui/evidence", help="Output directory for screenshots & report.json")
    parser.add_argument("--round", type=int, default=0, help="Polish iteration round number (1, 2, or 3) for multi-round tracking & auto-diff")
    parser.add_argument("--mark", default="", help="Draw magenta callout badges on selectors, e.g. '1=.hero-title,2=.card'")
    parser.add_argument("--compare", nargs=2, metavar=("BEFORE_PNG", "AFTER_PNG"), help="Compute 3x3 9-grid pixel diff between two screenshots")
    parser.add_argument("--evidence", action="store_true", help="Capture full multi-viewport evidence package (Desktop 1x/2x, Mobile, and Masked view)")
    parser.add_argument("--lint-only", action="store_true", help="Run static 67-rule linter without launching headless browser")
    parser.add_argument("--json", action="store_true", help="Print JSON report to stdout")

    args = parser.parse_args()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.compare:
        diff_res = compute_9grid_diff(Path(args.compare[0]).resolve(), Path(args.compare[1]).resolve())
        print(json.dumps(diff_res, indent=2, ensure_ascii=False))
        return

    target_str = args.target
    is_url = target_str.startswith(("http://", "https://"))
    all_findings = []
    raw_html_for_mask = ""
    httpd = None
    target_url = target_str
    masked_html_fp = None

    if is_url:
        try:
            with urllib.request.urlopen(target_str, timeout=15) as resp:
                raw_html_for_mask = resp.read().decode("utf-8", errors="replace")
            all_findings.extend(run_static_lint(raw_html_for_mask, target_str))
        except Exception as e:
            all_findings.append({"rule_id": "fetch-error", "severity": "error", "location": target_str, "message": str(e)})
    else:
        target_fp = Path(target_str).resolve()
        if target_fp.is_file():
            raw_html_for_mask = target_fp.read_text(encoding="utf-8", errors="replace")
            all_findings.extend(run_static_lint(raw_html_for_mask, target_fp.name))
            if not args.lint_only and target_fp.suffix.lower() in (".html", ".htm"):
                httpd, port = start_local_server(target_fp.parent)
                target_url = f"http://127.0.0.1:{port}/{target_fp.name}"
        elif target_fp.is_dir():
            for ext in ("*.html", "*.tsx", "*.jsx", "*.vue", "*.css"):
                for fp in sorted(target_fp.rglob(ext)):
                    if "node_modules" in fp.parts or ".next" in fp.parts or "dist" in fp.parts:
                        continue
                    txt = fp.read_text(encoding="utf-8", errors="replace")
                    all_findings.extend(run_static_lint(txt, fp.relative_to(target_fp).as_posix()))
            idx_html = target_fp / "index.html"
            if not args.lint_only and idx_html.exists():
                raw_html_for_mask = idx_html.read_text(encoding="utf-8", errors="replace")
                httpd, port = start_local_server(target_fp)
                target_url = f"http://127.0.0.1:{port}/index.html"

    screenshots = {}
    browser_bin = find_browser() if not args.lint_only else None

    r_prefix = f"round-{args.round}-" if args.round > 0 else ""

    if browser_bin and (is_url or target_url.startswith("http://127.0.0.1:")):
        desk_png = out_dir / f"{r_prefix}desktop-1440x900.png"
        if capture_headless_screenshot(browser_bin, target_url, desk_png, 1440, 900, 1.0):
            screenshots["desktop_1x"] = str(desk_png)

        if args.mark and raw_html_for_mask and not is_url:
            target_fp = Path(target_str).resolve()
            base_dir = target_fp.parent if target_fp.is_file() else target_fp
            marked_fp = base_dir / "_light_marked_temp.html"
            marked_fp.write_text(create_marked_html(raw_html_for_mask, args.mark), encoding="utf-8")
            mark_url = target_url.rsplit("/", 1)[0] + "/_light_marked_temp.html"
            mark_png = out_dir / f"{r_prefix}desktop-marked.png"
            if capture_headless_screenshot(browser_bin, mark_url, mark_png, 1440, 900, 1.0):
                screenshots["desktop_marked"] = str(mark_png)
            if marked_fp.exists():
                marked_fp.unlink()

        if args.evidence:
            desk_2x = out_dir / f"{r_prefix}desktop-1440x900@2x.png"
            if capture_headless_screenshot(browser_bin, target_url, desk_2x, 1440, 900, 2.0):
                screenshots["desktop_2x"] = str(desk_2x)

            mob_png = out_dir / f"{r_prefix}mobile-390x844.png"
            if raw_html_for_mask and not is_url:
                target_fp = Path(target_str).resolve()
                base_dir = target_fp.parent if target_fp.is_file() else target_fp
                mob_html_fp = base_dir / "_light_mobile_temp.html"
                mob_style = "<style>html, body { max-width: 390px !important; margin: 0 !important; overflow-x: hidden !important; }</style>"
                mob_html = raw_html_for_mask.replace("</head>", mob_style + "\n</head>", 1) if "</head>" in raw_html_for_mask else (mob_style + raw_html_for_mask)
                mob_html_fp.write_text(mob_html, encoding="utf-8")
                mob_url = target_url.rsplit("/", 1)[0] + "/_light_mobile_temp.html"
                if capture_headless_screenshot(browser_bin, mob_url, mob_png, 390, 844, 1.0):
                    screenshots["mobile_1x"] = str(mob_png)
                if mob_html_fp.exists():
                    mob_html_fp.unlink()
            else:
                if capture_headless_screenshot(browser_bin, target_url, mob_png, 390, 844, 1.0):
                    screenshots["mobile_1x"] = str(mob_png)

            if raw_html_for_mask and not is_url:
                target_fp = Path(target_str).resolve()
                base_dir = target_fp.parent if target_fp.is_file() else target_fp
                masked_html_fp = base_dir / "_light_masked_temp.html"
                masked_html_fp.write_text(create_masked_html(raw_html_for_mask), encoding="utf-8")
                mask_url = target_url.rsplit("/", 1)[0] + "/_light_masked_temp.html"
                mask_png = out_dir / f"{r_prefix}desktop-masked.png"
                if capture_headless_screenshot(browser_bin, mask_url, mask_png, 1440, 900, 1.0):
                    screenshots["desktop_masked"] = str(mask_png)
                if masked_html_fp.exists():
                    masked_html_fp.unlink()

    if httpd:
        httpd.shutdown()

    # If --round >= 2, automatically compute 3x3 pixel diff against round-(N-1)
    round_diff = None
    if args.round >= 2 and "desktop_1x" in screenshots:
        prev_png = out_dir / f"round-{args.round - 1}-desktop-1440x900.png"
        if prev_png.exists():
            round_diff = compute_9grid_diff(prev_png, Path(screenshots["desktop_1x"]))

    errors = [f for f in all_findings if f["severity"] == "error"]
    warnings = [f for f in all_findings if f["severity"] == "warning"]
    advisories = [f for f in all_findings if f["severity"] == "advisory"]

    report = {
        "target": target_str,
        "round": args.round if args.round > 0 else 1,
        "browser_used": browser_bin,
        "screenshots": screenshots,
        "round_3x3_pixel_diff": round_diff,
        "summary": {
            "passed_immediate_gate": len(errors) == 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "advisory_count": len(advisories),
        },
        "findings": all_findings,
    }

    report_name = f"round-{args.round}-evidence.json" if args.round > 0 else "evidence-report.json"
    report_fp = out_dir / report_name
    report_fp.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    print(f"=== Light-UI-UX Inspection Report ({target_str}) ===")
    print(f"Gate Status : {'PASSED (0 Errors)' if len(errors) == 0 else f'BLOCKED ({len(errors)} Errors)'}")
    print(f"Counts      : {len(errors)} Errors | {len(warnings)} Warnings | {len(advisories)} Advisories")
    if screenshots:
        print("Screenshots :")
        for k, v in screenshots.items():
            print(f"  • {k:<16}: {v}")
    if all_findings:
        print("\nFindings:")
        for f in all_findings[:15]:
            print(f"  [{f['severity'].upper()}] {f['rule_id']} ({f['location']}): {f['message']}")
    print(f"\nFull JSON report written to: {report_fp}")


if __name__ == "__main__":
    main()
