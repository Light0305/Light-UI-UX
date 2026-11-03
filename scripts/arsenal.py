#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Light-UI-UX — Zero-Dependency Millisecond Local Arsenal CLI (`scripts/arsenal.py`)
Queries `assets/light-arsenal.db` across 9 domain tables:
  stats | benchmark | component | motion | icon | shader | brand | blueprint | industry | stack
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import zlib
from pathlib import Path

# Ensure UTF-8 stdout on Windows PowerShell/CMD
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = WORKSPACE_ROOT / "assets" / "light-arsenal.db"


def get_conn() -> sqlite3.Connection:
    if not DB_PATH.exists():
        sys.stderr.write(f"[ERROR] Database not found at {DB_PATH}. Reinstall the complete skill, including assets/light-arsenal.db.\n")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH.resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


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


def build_fts_query(raw_query: str) -> str:
    """Convert user search phrase into a safe FTS5 OR query."""
    tokens = [re.sub(r'["\'()*^:—\-/\\]+', " ", t).strip() for t in raw_query.split()]
    clean = []
    for t in tokens:
        for sub in t.split():
            if sub:
                clean.append(f'"{sub}"*')
    return " OR ".join(clean) if clean else '""'


def cmd_stats(args):
    conn = get_conn()
    cur = conn.cursor()
    tables = [
        "benchmarks",
        "components",
        "component_blobs",
        "motion_prompts",
        "icons",
        "icon_svgs",
        "webgl_shaders",
        "brand_systems",
        "blueprints_and_palettes",
        "industry_reasoning",
        "stack_guidelines",
    ]
    counts = {}
    for t in tables:
        counts[t] = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    size_mb = round(DB_PATH.stat().st_size / (1024 * 1024), 2)
    conn.close()

    if args.json:
        print(json.dumps({"db_path": str(DB_PATH), "db_size_mb": size_mb, "table_counts": counts}, indent=2, ensure_ascii=False))
        return

    print(f"=== Light-UI-UX Local Arsenal (`{DB_PATH.name}` — {size_mb} MB) ===")
    for k, v in counts.items():
        print(f"  • {k:<25}: {v:,} records")


def cmd_benchmark(args):
    conn = get_conn()
    cur = conn.cursor()

    if args.id:
        row = cur.execute("SELECT * FROM benchmarks WHERE id = ?", (args.id,)).fetchone()
        if not row:
            print(f"[WARN] Benchmark ID '{args.id}' not found.")
            return
        data = dict(row)
        data["colors"] = zjson(data.pop("colors_json"), [])
        data["typography"] = zjson(data.pop("typography_json"), {})
        data["layout"] = zjson(data.pop("layout_json"), {})
        data["components"] = zjson(data.pop("components_json"), [])
        data["steal"] = zjson(data.pop("steal_json"), [])
        css_code = zdecomp(data.pop("css_vars_zlib"))
        tw_code = zdecomp(data.pop("tailwind_v4_zlib"))

        if args.export_css:
            Path(args.export_css).write_text(css_code, encoding="utf-8")
            print(f"[OK] Exported CSS Custom Properties to {args.export_css}")
        if args.export_tailwind:
            Path(args.export_tailwind).write_text(tw_code, encoding="utf-8")
            print(f"[OK] Exported Tailwind v4 @theme to {args.export_tailwind}")

        if args.json:
            data["css_vars_code"] = css_code
            data["tailwind_v4_code"] = tw_code
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return

        print(f"=== [{data['id']}] {data['name']} — {data['title']} ===")
        print(f"URL: {data['source_url']} | Theme: {data['theme']} ({data['theme_zh']}) | Tags: {data['tags_zh']}")
        if data["note_zh"]:
            print(f"Summary: {data['note_zh']}")
        print("\n[Colors (Top 10)]:")
        if isinstance(data["colors"], list):
            for c in data["colors"][:10]:
                print(f"  - {c.get('name')}: {c.get('value')} ({c.get('token')}) -> {c.get('role')}")
        else:
            print(f"  {json.dumps(data['colors'], ensure_ascii=False)}")
        print("\n[Typography]:")
        print(f"  {json.dumps(data['typography'], ensure_ascii=False)[:600]}")
        print("\n[Layout & Radii]:")
        print(f"  {json.dumps(data['layout'], ensure_ascii=False)[:600]}")
        print(f"\n[Components ({len(data['components'])})]:")
        for c in data["components"][:8]:
            if isinstance(c, dict):
                print(f"  - {c.get('name')} [{c.get('role')}]: {', '.join(c.get('spec_tokens', [])[:8])}")
            else:
                print(f"  - {c}")
        if css_code:
            print(f"\n[Quick Start — CSS Custom Properties (first 25 lines)]:\n" + "\n".join(css_code.splitlines()[:25]))
        return

    q = (args.query or "").strip()
    params = []
    where_clauses = []
    if args.theme:
        where_clauses.append("b.theme = ?")
        params.append(args.theme)

    rows = []
    if q:
        fts_q = build_fts_query(q)
        sql = f"""
            SELECT b.id, b.source_pool, b.name, b.title, b.source_url, b.theme, b.theme_zh,
                   b.tags_zh, b.note_zh, b.colors_json, b.typography_json, b.layout_json, b.steal_json
            FROM benchmarks_fts f
            JOIN benchmarks b ON f.id = b.id
            WHERE benchmarks_fts MATCH ?
            {('AND ' + ' AND '.join(where_clauses)) if where_clauses else ''}
            ORDER BY rank
            LIMIT ?
        """
        try:
            rows = cur.execute(sql, [fts_q] + params + [args.limit]).fetchall()
        except Exception:
            rows = []

        if not rows:
            like_p = f"%{q}%"
            sql_like = f"""
                SELECT b.id, b.source_pool, b.name, b.title, b.source_url, b.theme, b.theme_zh,
                       b.tags_zh, b.note_zh, b.colors_json, b.typography_json, b.layout_json, b.steal_json
                FROM benchmarks b
                WHERE (b.name LIKE ? OR b.title LIKE ? OR b.tags_zh LIKE ? OR b.note_zh LIKE ?)
                {('AND ' + ' AND '.join(where_clauses)) if where_clauses else ''}
                LIMIT ?
            """
            rows = cur.execute(sql_like, [like_p, like_p, like_p, like_p] + params + [args.limit]).fetchall()
    else:
        sql = f"""
            SELECT b.id, b.source_pool, b.name, b.title, b.source_url, b.theme, b.theme_zh,
                   b.tags_zh, b.note_zh, b.colors_json, b.typography_json, b.layout_json, b.steal_json
            FROM benchmarks b
            {('WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''}
            LIMIT ?
        """
        rows = cur.execute(sql, params + [args.limit]).fetchall()

    results = []
    for r in rows:
        d = dict(r)
        cols = zjson(d.pop("colors_json"), [])
        typo = zjson(d.pop("typography_json"), {})
        lay = zjson(d.pop("layout_json"), {})
        steal = zjson(d.pop("steal_json"), [])
        d["color_preview"] = [f"{c.get('name')}:{c.get('value')}" for c in cols[:5]] if isinstance(cols, list) else cols
        d["font_preview"] = [f.get("family") for f in typo.get("fonts", [])[:3]] if isinstance(typo, dict) and "fonts" in typo else typo
        d["radii_preview"] = lay.get("radii", {}) if isinstance(lay, dict) else {}
        if steal:
            d["steal"] = steal
        results.append(d)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    print(f"=== Found {len(results)} Real-World Benchmark Specs (query='{q}') ===")
    for idx, item in enumerate(results, 1):
        print(f"\n[{idx}] {item['id']} | {item['name']} ({item['theme']} / {item['tags_zh']})")
        if item["note_zh"]:
            print(f"    • Brief    : {item['note_zh']}")
        print(f"    • Palette  : {item['color_preview']}")
        print(f"    • Fonts    : {item['font_preview']}")
        if item.get("radii_preview"):
            print(f"    • Radii    : {item['radii_preview']}")
        if item.get("steal"):
            print(f"    • Steal    : {item['steal']}")


def cmd_component(args):
    conn = get_conn()
    cur = conn.cursor()

    if args.id:
        row = cur.execute("SELECT * FROM components WHERE id = ?", (args.id,)).fetchone()
        if not row:
            print(f"[WARN] Component '{args.id}' not found.")
            return
        d = dict(row)
        fmap = json.loads(d.pop("file_map_json") or "{}")
        files_content = {}
        for rel_path, sha in fmap.items():
            blob_row = cur.execute("SELECT zlib_content FROM component_blobs WHERE sha256 = ?", (sha,)).fetchone()
            if blob_row:
                files_content[rel_path] = zdecomp(blob_row["zlib_content"])

        library_license = WORKSPACE_ROOT / "licenses" / "components" / f"{d['site']}.txt"
        has_license = any(re.match(r"(?:licen[sc]e|notice|copying)", Path(name).name, re.I) for name in files_content)
        if files_content and not has_license and library_license.is_file():
            files_content["LICENSE.upstream.txt"] = library_license.read_text(encoding="utf-8")

        if args.extract:
            out_dir = Path(args.extract) / d["id"]
            for rel_path, code in files_content.items():
                dest = out_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(code, encoding="utf-8")
            if not args.json:
                if files_content:
                    print(f"[OK] Extracted {len(files_content)} files for '{d['id']}' to {out_dir}")
                else:
                    print("[INFO] Reference-only entry; source is available from the upstream URL under its own terms.")

        if args.json:
            d["files"] = files_content
            print(json.dumps(d, indent=2, ensure_ascii=False))
            return

        print(f"=== [{d['id']}] {d['name']} ({d['name_zh']}) ===")
        print(f"Site: {d['site']} | License: {d['license']} | Mode: {d['redistribution_mode']}")
        print(f"Categories: {d['categories']} | Tags: {d['tags']}")
        print(f"Description: {d['description']}")
        if d["source_url"]:
            print(f"Upstream URL: {d['source_url']}")
        for rel_path, code in files_content.items():
            print(f"\n--- File: {rel_path} ({len(code.splitlines())} lines) ---")
            print("\n".join(code.splitlines()[:60]))
            if len(code.splitlines()) > 60:
                print(f"... ({len(code.splitlines()) - 60} more lines; use --extract <dir> to dump full source)")
        return

    q = (args.query or "").strip()
    params = []
    where_sql = ""
    if args.site:
        where_sql = "AND c.site = ?"
        params.append(args.site)

    rows = []
    if q:
        fts_q = build_fts_query(q)
        try:
            rows = cur.execute(
                f"""
                SELECT c.id, c.site, c.name, c.name_zh, c.categories, c.license,
                       c.redistribution_mode, c.tags, c.description, c.file_count
                FROM components_fts f
                JOIN components c ON f.id = c.id
                WHERE components_fts MATCH ? {where_sql}
                ORDER BY rank
                LIMIT ?
                """,
                [fts_q] + params + [args.limit],
            ).fetchall()
        except Exception:
            rows = []
        if not rows:
            lp = f"%{q}%"
            rows = cur.execute(
                f"""
                SELECT c.id, c.site, c.name, c.name_zh, c.categories, c.license,
                       c.redistribution_mode, c.tags, c.description, c.file_count
                FROM components c
                WHERE (c.name LIKE ? OR c.name_zh LIKE ? OR c.categories LIKE ? OR c.tags LIKE ? OR c.description LIKE ?)
                {where_sql}
                LIMIT ?
                """,
                [lp, lp, lp, lp, lp] + params + [args.limit],
            ).fetchall()
    else:
        rows = cur.execute(
            f"""
            SELECT c.id, c.site, c.name, c.name_zh, c.categories, c.license,
                   c.redistribution_mode, c.tags, c.description, c.file_count
            FROM components c
            WHERE 1=1 {where_sql}
            LIMIT ?
            """,
            params + [args.limit],
        ).fetchall()

    res = [dict(r) for r in rows]
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    print(f"=== Found {len(res)} Compliant Interactive Components (query='{q}') ===")
    for r in res:
        print(
            f"  • [{r['id']}] {r['name']} ({r['name_zh']}) | {r['site']} | {r['categories']} | {r['tags']} | files={r['file_count']}"
        )
        if r["description"]:
            print(f"    {r['description'][:140]}")


def cmd_motion(args):
    conn = get_conn()
    cur = conn.cursor()

    if args.id:
        row = cur.execute("SELECT * FROM motion_prompts WHERE id = ?", (args.id,)).fetchone()
        if not row:
            print(f"[WARN] Motion ID '{args.id}' not found.")
            return
        d = dict(row)
        d["code_snippet"] = zdecomp(d.pop("code_zlib"))
        d["meta"] = json.loads(d.pop("meta_json") or "{}")
        if args.json:
            print(json.dumps(d, indent=2, ensure_ascii=False))
            return
        print(f"=== [{d['id']}] {d['title']} ({d['source_pool']}) ===")
        print(f"Category: {d['category']} | Tags: {d['tags_en']} {d['tags_zh']} | Ratio: {d['aspect_ratio']} | Duration: {d['duration']}")
        if d["prompt_en"]:
            print(f"\n[Prompt EN / Description]:\n{d['prompt_en']}")
        if d["prompt_zh"]:
            print(f"\n[Prompt ZH]:\n{d['prompt_zh']}")
        if d["code_snippet"]:
            print(f"\n[Code / Reference Detail]:\n{d['code_snippet']}")
        return

    q = (args.query or "").strip()
    rows = []
    if q:
        fts_q = build_fts_query(q)
        try:
            rows = cur.execute(
                """
                SELECT m.id, m.source_pool, m.title, m.category, m.tags_en, m.tags_zh, m.duration, m.prompt_en, m.prompt_zh
                FROM motion_fts f
                JOIN motion_prompts m ON f.id = m.id
                WHERE motion_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (fts_q, args.limit),
            ).fetchall()
        except Exception:
            rows = []
        if not rows:
            lp = f"%{q}%"
            rows = cur.execute(
                """
                SELECT id, source_pool, title, category, tags_en, tags_zh, duration, prompt_en, prompt_zh
                FROM motion_prompts
                WHERE title LIKE ? OR category LIKE ? OR tags_en LIKE ? OR tags_zh LIKE ? OR prompt_en LIKE ? OR prompt_zh LIKE ?
                LIMIT ?
                """,
                (lp, lp, lp, lp, lp, lp, args.limit),
            ).fetchall()
    else:
        rows = cur.execute(
            "SELECT id, source_pool, title, category, tags_en, tags_zh, duration, prompt_en, prompt_zh FROM motion_prompts LIMIT ?",
            (args.limit,),
        ).fetchall()

    res = [dict(r) for r in rows]
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    print(f"=== Found {len(res)} Motion Prompts & Recipes (query='{q}') ===")
    for r in res:
        preview = (r["prompt_zh"] or r["prompt_en"] or "").replace("\n", " ")[:140]
        print(f"  • [{r['id']}] ({r['source_pool']}) {r['title']} | {r['category']} | {r['tags_en']}")
        print(f"    {preview}...")


def cmd_icon(args):
    conn = get_conn()
    cur = conn.cursor()

    if args.svg:
        target = args.svg
        row = cur.execute(
            "SELECT * FROM icon_svgs WHERE svg_id = ? OR icon_id = ? LIMIT 1",
            (target, target),
        ).fetchone()
        if not row and ":" in target:
            lib, name = target.split(":", 1)
            row = cur.execute(
                "SELECT * FROM icon_svgs WHERE library = ? AND name = ? LIMIT 1",
                (lib, name),
            ).fetchone()
        if not row:
            row = cur.execute("SELECT * FROM icon_svgs WHERE name = ? LIMIT 1", (target,)).fetchone()
        if not row:
            print(f"[WARN] SVG '{target}' not found.")
            return
        svg_text = zdecomp(row["zlib_svg"])
        if args.out:
            Path(args.out).write_text(svg_text, encoding="utf-8")
            print(f"[OK] Wrote SVG '{row['svg_id']}' ({row['raw_bytes']} bytes) to {args.out}")
        else:
            print(svg_text)
        return

    q = (args.query or "").strip()
    lib_clause = "AND i.library = ?" if args.lib else ""
    params = [args.lib] if args.lib else []

    rows = []
    if q:
        fts_q = build_fts_query(q)
        try:
            rows = cur.execute(
                f"""
                SELECT i.id, i.name, i.library, i.license, i.styles_json, i.categories_json, i.keywords_zh
                FROM icons_fts f
                JOIN icons i ON f.id = i.id
                WHERE icons_fts MATCH ? {lib_clause}
                ORDER BY rank
                LIMIT ?
                """,
                [fts_q] + params + [args.limit],
            ).fetchall()
        except Exception:
            rows = []
        if not rows:
            lp = f"%{q}%"
            rows = cur.execute(
                f"""
                SELECT i.id, i.name, i.library, i.license, i.styles_json, i.categories_json, i.keywords_zh
                FROM icons i
                WHERE (i.name LIKE ? OR i.keywords_zh LIKE ? OR i.concepts_json LIKE ?) {lib_clause}
                LIMIT ?
                """,
                [lp, lp, lp] + params + [args.limit],
            ).fetchall()
    else:
        rows = cur.execute(
            f"SELECT id, name, library, license, styles_json, categories_json, keywords_zh FROM icons i WHERE 1=1 {lib_clause} LIMIT ?",
            params + [args.limit],
        ).fetchall()

    res = [dict(r) for r in rows]
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    print(f"=== Found {len(res)} Compliant Vector Icons (query='{q}') ===")
    for r in res:
        print(
            f"  • {r['id']:<28} | lib={r['library']:<10} | styles={r['styles_json']} | zh={r['keywords_zh'][:40]}"
        )


def cmd_shader(args):
    conn = get_conn()
    cur = conn.cursor()

    q = (args.query or "").strip()
    if q and (args.extract or cur.execute("SELECT 1 FROM webgl_shaders WHERE id = ? OR slug = ?", (q, q)).fetchone()):
        row = cur.execute("SELECT * FROM webgl_shaders WHERE id = ? OR slug = ?", (q, q)).fetchone()
        if row:
            html_code = zdecomp(row["zlib_html"])
            if args.extract:
                Path(args.extract).write_text(html_code, encoding="utf-8")
                print(f"[OK] Extracted standalone WebGL shader '{row['slug']}' ({row['raw_lines']} lines) to {args.extract}")
                return
            if args.json:
                d = dict(row)
                d.pop("zlib_html")
                d["html_source"] = html_code
                print(json.dumps(d, indent=2, ensure_ascii=False))
                return
            print(f"=== [{row['slug']}] {row['title']} ({row['engine']}, {row['raw_lines']} lines) ===")
            print(f"Description: {row['description']}\n")
            print(html_code[:2000] + ("\n... (use --extract <out.html> for full file)" if len(html_code) > 2000 else ""))
            return

    rows = cur.execute(
        "SELECT id, slug, title, engine, category, visual_mood, raw_lines FROM webgl_shaders WHERE slug LIKE ? OR title LIKE ? OR description LIKE ? LIMIT ?",
        (f"%{q}%", f"%{q}%", f"%{q}%", args.limit),
    ).fetchall()
    res = [dict(r) for r in rows]
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return
    print(f"=== Available Single-File WebGL2 / Three.js Shader Stages ({len(res)}) ===")
    for r in res:
        print(f"  • {r['slug']:<32} | {r['engine']:<22} | {r['raw_lines']:>3} lines | {r['visual_mood'][:70]}")


def cmd_brand(args):
    conn = get_conn()
    cur = conn.cursor()

    if args.id:
        bid = args.id if args.id.startswith("brand-") else f"brand-{args.id}"
        row = cur.execute("SELECT * FROM brand_systems WHERE id = ? OR brand_name LIKE ?", (bid, f"%{args.id}%")).fetchone()
        if not row:
            print(f"[WARN] Brand system '{args.id}' not found.")
            return
        md_txt = zdecomp(row["zlib_design_md"])
        if args.extract:
            Path(args.extract).write_text(md_txt, encoding="utf-8")
            print(f"[OK] Extracted DESIGN.md for '{row['brand_name']}' to {args.extract}")
            return
        print(md_txt)
        return

    q = (args.query or "").strip()
    if q:
        lp = f"%{q}%"
        rows = cur.execute(
            "SELECT id, brand_name, category, colors_preview, fonts_preview, summary FROM brand_systems WHERE id LIKE ? OR brand_name LIKE ? OR summary LIKE ? LIMIT ?",
            (lp, lp, lp, args.limit),
        ).fetchall()
    else:
        rows = cur.execute(
            "SELECT id, brand_name, category, colors_preview, fonts_preview, summary FROM brand_systems LIMIT ?",
            (args.limit,),
        ).fetchall()

    res = [dict(r) for r in rows]
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return
    print(f"=== Found {len(res)} Brand Design Systems (query='{q}') ===")
    for r in res:
        print(f"  • [{r['id']}] {r['brand_name']} | Colors: {r['colors_preview'][:50]} | Fonts: {r['fonts_preview'][:50]}")


def cmd_blueprint(args):
    conn = get_conn()
    cur = conn.cursor()

    if args.id:
        row = cur.execute("SELECT * FROM blueprints_and_palettes WHERE id = ?", (args.id,)).fetchone()
        if not row:
            print(f"[WARN] Blueprint '{args.id}' not found.")
            return
        tpl = zdecomp(row["zlib_template"])
        if args.extract and tpl:
            Path(args.extract).write_text(tpl, encoding="utf-8")
            print(f"[OK] Extracted template '{row['id']}' to {args.extract}")
            return
        print(f"=== [{row['id']}] {row['name']} ({row['asset_type']}) ===")
        print(row["spec_json"])
        if tpl:
            print("\n--- Template HTML (first 40 lines) ---")
            print("\n".join(tpl.splitlines()[:40]))
        return

    q = (args.query or "").strip()
    t_clause = "AND asset_type = ?" if args.type else ""
    params = [f"%{q}%", f"%{q}%", f"%{q}%"] + ([args.type] if args.type else []) + [args.limit]
    rows = cur.execute(
        f"SELECT id, asset_type, name, tags, summary FROM blueprints_and_palettes WHERE (name LIKE ? OR tags LIKE ? OR summary LIKE ?) {t_clause} LIMIT ?",
        params,
    ).fetchall()
    res = [dict(r) for r in rows]
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return
    print(f"=== Found {len(res)} Blueprints, Palettes & Shells (query='{q}') ===")
    for r in res:
        print(f"  • [{r['id']}] ({r['asset_type']}) {r['name']} | {r['summary'][:100]}")


def cmd_industry(args):
    conn = get_conn()
    cur = conn.cursor()
    q = (args.query or "").strip()
    t_clause = "AND r.record_type = ?" if args.type else ""
    params = [args.type] if args.type else []

    rows = []
    if q:
        fts_q = build_fts_query(q)
        try:
            rows = cur.execute(
                f"""
                SELECT r.* FROM industry_fts f
                JOIN industry_reasoning r ON f.id = r.id
                WHERE industry_fts MATCH ? {t_clause}
                ORDER BY rank
                LIMIT ?
                """,
                [fts_q] + params + [args.limit],
            ).fetchall()
        except Exception:
            rows = []
        if not rows:
            lp = f"%{q}%"
            rows = cur.execute(
                f"""
                SELECT * FROM industry_reasoning r
                WHERE (r.name LIKE ? OR r.keywords LIKE ? OR r.recommended_pattern LIKE ? OR r.style_priority LIKE ?) {t_clause}
                LIMIT ?
                """,
                [lp, lp, lp, lp] + params + [args.limit],
            ).fetchall()
    else:
        rows = cur.execute(
            f"SELECT * FROM industry_reasoning r WHERE 1=1 {t_clause} LIMIT ?",
            params + [args.limit],
        ).fetchall()

    res = [dict(r) for r in rows]
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return
    print(f"=== Found {len(res)} Industry Reasoning & UI Style Rules (query='{q}') ===")
    for r in res:
        print(f"\n• [{r['id']}] ({r['record_type']}) {r['name']}")
        print(f"  Keywords  : {r['keywords']}")
        print(f"  Pattern   : {r['recommended_pattern']}")
        print(f"  Style     : {r['style_priority']}")
        if r["anti_patterns"]:
            print(f"  Avoid     : {r['anti_patterns']}")
        print(f"  Tokens    : {r['colors_json'][:220]}...")


def cmd_stack(args):
    conn = get_conn()
    cur = conn.cursor()
    st = (args.stack or "").strip()
    q = (args.query or "").strip()
    lp = f"%{q}%"
    rows = cur.execute(
        """
        SELECT id, stack, category, guideline, description, do_text, dont_text, severity, applies_to
        FROM stack_guidelines
        WHERE stack LIKE ? AND (guideline LIKE ? OR description LIKE ? OR category LIKE ? OR do_text LIKE ?)
        LIMIT ?
        """,
        (f"%{st}%", lp, lp, lp, lp, args.limit),
    ).fetchall()
    res = [dict(r) for r in rows]
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return
    print(f"=== Found {len(res)} Stack Guidelines (stack='{st}', query='{q}') ===")
    for r in res:
        print(f"  • [{r['id']}] ({r['stack']} / {r['severity']}) {r['guideline']}")
        print(f"    DO   : {r['do_text'][:140]}")
        print(f"    DONT : {r['dont_text'][:140]}")


def main():
    parser = argparse.ArgumentParser(description="Light-UI-UX Local Arsenal Search & Extraction Engine")
    parser.add_argument("--json", action="store_true", help="Output structured JSON")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("stats", help="Show arsenal database statistics")

    p_bench = sub.add_parser("benchmark", help="Search 1,544 website & award specs")
    p_bench.add_argument("query", nargs="?", default="", help="Keywords (e.g., 'AI 科技感 极简', 'fintech', 'Apple')")
    p_bench.add_argument("--theme", choices=["light", "dark", "mixed"], help="Filter by theme")
    p_bench.add_argument("--limit", type=int, default=3, help="Max results (default 3 for Benchmark Briefs)")
    p_bench.add_argument("--id", help="Inspect specific benchmark ID and view CSS/Tailwind tokens")
    p_bench.add_argument("--export-css", help="Export CSS Custom Properties to file")
    p_bench.add_argument("--export-tailwind", help="Export Tailwind v4 @theme block to file")

    p_comp = sub.add_parser("component", help="Search 1,140 compliant interactive components")
    p_comp.add_argument("query", nargs="?", default="", help="Component search query")
    p_comp.add_argument("--site", help="Filter by upstream library (e.g., reactbits, bundui, animata, cult-ui)")
    p_comp.add_argument("--limit", type=int, default=8)
    p_comp.add_argument("--id", help="View component details & source files")
    p_comp.add_argument("--extract", help="Extract full component source tree into directory")

    p_mot = sub.add_parser("motion", help="Search motion prompts, motion-lab cases & GSAP recipes")
    p_mot.add_argument("query", nargs="?", default="")
    p_mot.add_argument("--limit", type=int, default=8)
    p_mot.add_argument("--id", help="View full motion prompt & code snippet")

    p_ico = sub.add_parser("icon", help="Search 17,130 logical icons / 33,253 SVGs across 7 compliant libraries")
    p_ico.add_argument("query", nargs="?", default="", help="Chinese or English icon keyword")
    p_ico.add_argument("--lib", help="Filter by library (hugeicons, tabler, phosphor, solar, iconoir, bootstrap, heroicons)")
    p_ico.add_argument("--limit", type=int, default=12)
    p_ico.add_argument("--svg", help="Decompress and print SVG by svg_id or icon_id (e.g., 'tabler:outline:home' or 'hugeicons:home-01')")
    p_ico.add_argument("--out", help="Write extracted SVG to file path")

    p_shd = sub.add_parser("shader", help="List or extract 16 standalone single-file WebGL2 / Three.js shader stages")
    p_shd.add_argument("query", nargs="?", default="", help="Shader slug or keyword (e.g., 'webgl-liquid-metal')")
    p_shd.add_argument("--limit", type=int, default=20)
    p_shd.add_argument("--extract", help="Write standalone single-file HTML shader stage to path")

    p_brd = sub.add_parser("brand", help="Search 152 brand DESIGN.md systems (Linear, Stripe, Apple, Claude, etc.)")
    p_brd.add_argument("query", nargs="?", default="")
    p_brd.add_argument("--limit", type=int, default=10)
    p_brd.add_argument("--id", help="Print full DESIGN.md for brand slug")
    p_brd.add_argument("--extract", help="Write DESIGN.md to file path")

    p_bp = sub.add_parser("blueprint", help="Search Taste directions, hero/section blueprints, palettes, font pairings & mobile shells")
    p_bp.add_argument("query", nargs="?", default="")
    p_bp.add_argument("--type", help="Filter by asset_type (direction, hero_blueprint, section_blueprint, color_palette, font_pairing, mobile_shell, html_prototype)")
    p_bp.add_argument("--limit", type=int, default=10)
    p_bp.add_argument("--id", help="Inspect full blueprint JSON or HTML template")
    p_bp.add_argument("--extract", help="Extract HTML prototype/shell to file")

    p_ind = sub.add_parser("industry", help="Search 192 industry reasoning profiles, 88 UI styles, 34 landing patterns & 25 chart rules")
    p_ind.add_argument("query", nargs="?", default="")
    p_ind.add_argument("--type", help="Filter by record_type (industry_archetype, ui_style, landing_pattern, chart_guideline, font_pairing_pro)")
    p_ind.add_argument("--limit", type=int, default=5)

    p_stk = sub.add_parser("stack", help="Search 1,271 versioned rules across 22 tech stacks")
    p_stk.add_argument("stack", help="Stack name (e.g., nextjs, react, vue, react-native, flutter, swiftui, shadcn, html-tailwind)")
    p_stk.add_argument("query", nargs="?", default="")
    p_stk.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()
    dispatch = {
        "stats": cmd_stats,
        "benchmark": cmd_benchmark,
        "component": cmd_component,
        "motion": cmd_motion,
        "icon": cmd_icon,
        "shader": cmd_shader,
        "brand": cmd_brand,
        "blueprint": cmd_blueprint,
        "industry": cmd_industry,
        "stack": cmd_stack,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
