#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Light-UI-UX — Compliance Sanitizer & Single-File SQLite FTS5 Arsenal Compiler
Builds `assets/light-arsenal.db` and `THIRD_PARTY_NOTICES.md` from `资源/`.
Zero third-party Python dependencies required (uses built-in sqlite3, zlib, hashlib, csv, json, re).
"""

import csv
import glob
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import zlib
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
RESOURCE_ROOT = WORKSPACE_ROOT / "资源"
ASSETS_DIR = WORKSPACE_ROOT / "assets"
DB_PATH = ASSETS_DIR / "light-arsenal.db"
NOTICES_PATH = WORKSPACE_ROOT / "THIRD_PARTY_NOTICES.md"

# Chinese -> English tag normalization map for motion-prompts items 1-3
MOTION_ZH_TAG_MAP = {
    "产品界面": "Product UI",
    "动态文字": "Kinetic type",
    "音乐": "Music",
    "粒子": "Particles",
    "图形": "Shapes",
    "图表": "Charts",
    "示意图": "Diagrams",
    "代码": "Code",
    "照片": "Photos",
    "手机": "Phone",
    "角色": "Characters",
}

RESTRICTED_COMPONENT_SITES = {"avatar-lab", "unicorn"}
RESTRICTED_ICON_LIBRARIES = {"nucleo-ui"}


def zcomp(text_or_bytes) -> bytes:
    if isinstance(text_or_bytes, str):
        text_or_bytes = text_or_bytes.encode("utf-8")
    return zlib.compress(text_or_bytes, 9)


def sanitize_role_note(role_text: str) -> str:
    """Strip long-form Refero editorial commentary after em-dash while keeping functional role."""
    if not role_text:
        return ""
    parts = re.split(r"\s+[—–]\s+", role_text.strip(), maxsplit=1)
    head = parts[0].strip()
    return head[:180]


def parse_md_table(lines: list[str]) -> list[dict]:
    """Parse a standard GitHub-flavored Markdown table into a list of dicts."""
    table_lines = [ln.strip() for ln in lines if ln.strip().startswith("|") and ln.strip().endswith("|")]
    if len(table_lines) < 2:
        return []
    headers = [c.strip().lower().replace(" ", "_") for c in table_lines[0].strip("|").split("|")]
    rows = []
    for ln in table_lines[2:]:
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) == len(headers):
            row = {headers[i]: cells[i].strip("`") for i in range(len(headers))}
            rows.append(row)
    return rows


def parse_benchmark_md(md_text: str) -> dict:
    """
    Extract structured tokens, component contracts, and Quick Start CSS/Tailwind v4 blocks
    from a benchmark .md file while stripping Refero's copyrighted long-form English prose.
    """
    result = {
        "colors": [],
        "fonts": [],
        "type_scale": [],
        "spacing_unit": "",
        "density": "",
        "spacing_scale": [],
        "radii": {},
        "shadows": [],
        "layout": {},
        "components": [],
        "dos": [],
        "donts": [],
        "css_vars_code": "",
        "tailwind_v4_code": "",
    }

    # Split by H2 sections
    h2_sections = re.split(r"(?m)^##\s+", md_text)
    for sec in h2_sections[1:]:
        lines = sec.splitlines()
        sec_title = lines[0].strip()
        sec_body = "\n".join(lines[1:])

        if sec_title.startswith("Tokens — Colors"):
            raw_rows = parse_md_table(lines[1:])
            for r in raw_rows:
                result["colors"].append({
                    "name": r.get("name", ""),
                    "value": r.get("value", ""),
                    "token": r.get("token", ""),
                    "role": sanitize_role_note(r.get("role", "")),
                })

        elif sec_title.startswith("Tokens — Typography"):
            h3_blocks = re.split(r"(?m)^###\s+", sec_body)
            for b in h3_blocks[1:]:
                b_lines = b.splitlines()
                b_head = b_lines[0].strip()
                if b_head.startswith("Type Scale"):
                    result["type_scale"] = parse_md_table(b_lines[1:])
                else:
                    # Extract font family name and token
                    m_tok = re.search(r"`(--font-[^`]+)`", b_head)
                    font_tok = m_tok.group(1) if m_tok else ""
                    family_name = b_head.split("—")[0].strip()
                    font_meta = {"family": family_name, "token": font_tok}
                    for bl in b_lines[1:]:
                        m_kv = re.match(r"^-\s+\*\*([^:*]+):\*\*\s*(.+)$", bl.strip())
                        if m_kv:
                            k = m_kv.group(1).strip().lower().replace(" ", "_")
                            v = m_kv.group(2).strip()
                            if k == "role":
                                v = sanitize_role_note(v)
                            font_meta[k] = v
                    result["fonts"].append(font_meta)

        elif sec_title.startswith("Tokens — Spacing & Shapes"):
            m_unit = re.search(r"\*\*Base unit:\*\*\s*([^\n]+)", sec_body)
            if m_unit:
                result["spacing_unit"] = m_unit.group(1).strip()
            m_dens = re.search(r"\*\*Density:\*\*\s*([^\n]+)", sec_body)
            if m_dens:
                result["density"] = m_dens.group(1).strip()

            h3_blocks = re.split(r"(?m)^###\s+", sec_body)
            for b in h3_blocks[1:]:
                b_lines = b.splitlines()
                b_head = b_lines[0].strip()
                if b_head.startswith("Spacing Scale"):
                    result["spacing_scale"] = parse_md_table(b_lines[1:])
                elif b_head.startswith("Border Radius"):
                    for r in parse_md_table(b_lines[1:]):
                        el = r.get("element", "")
                        val = r.get("value", "")
                        if el:
                            result["radii"][el] = val
                elif b_head.startswith("Shadows"):
                    result["shadows"] = parse_md_table(b_lines[1:])
                elif b_head.startswith("Layout"):
                    for bl in b_lines[1:]:
                        m_kv = re.match(r"^-\s+\*\*([^:*]+):\*\*\s*(.+)$", bl.strip())
                        if m_kv:
                            result["layout"][m_kv.group(1).strip().lower().replace(" ", "_")] = m_kv.group(2).strip()

        elif sec_title.startswith("Components"):
            h3_blocks = re.split(r"(?m)^###\s+", sec_body)
            for b in h3_blocks[1:]:
                b_lines = b.splitlines()
                comp_name = b_lines[0].strip()
                b_rest = "\n".join(b_lines[1:])
                m_role = re.search(r"\*\*Role:\*\*\s*([^\n]+)", b_rest)
                comp_role = m_role.group(1).strip() if m_role else ""
                m_html = re.search(r"```html\s*(.*?)```", b_rest, flags=re.S)
                html_snippet = m_html.group(1).strip() if m_html else ""
                # Extract numeric/hex/css measurements from the block without keeping Refero's prose sentences
                measurements = re.findall(
                    r"(#[0-9a-fA-F]{3,8}|rgba?\([^)]+\)|\b\d+(?:\.\d+)?(?:px|rem|em|vh|vw|%)\b|blur\(\d+px\)|--[a-z0-9-]+)",
                    b_rest,
                )
                seen_m = []
                for m in measurements:
                    if m not in seen_m:
                        seen_m.append(m)
                result["components"].append({
                    "name": comp_name,
                    "role": comp_role,
                    "spec_tokens": seen_m[:24],
                    "html": html_snippet,
                })

        elif sec_title.startswith("Quick Start"):
            h3_blocks = re.split(r"(?m)^###\s+", sec_body)
            for b in h3_blocks[1:]:
                b_lines = b.splitlines()
                b_head = b_lines[0].strip()
                b_rest = "\n".join(b_lines[1:])
                m_code = re.search(r"```css\s*(.*?)```", b_rest, flags=re.S)
                if m_code:
                    if "CSS Custom Properties" in b_head:
                        result["css_vars_code"] = m_code.group(1).strip()
                    elif "Tailwind" in b_head:
                        result["tailwind_v4_code"] = m_code.group(1).strip()

    return result


def init_schema(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.executescript("""
    PRAGMA journal_mode = OFF;
    PRAGMA synchronous = OFF;
    PRAGMA page_size = 4096;

    -- 1. Benchmarks (1,342 Real Website Specs + 202 Dissected Award Sites)
    CREATE TABLE benchmarks (
        id TEXT PRIMARY KEY,
        source_pool TEXT NOT NULL,
        name TEXT NOT NULL,
        title TEXT,
        source_url TEXT,
        theme TEXT,
        theme_zh TEXT,
        tags_zh TEXT,
        note_zh TEXT,
        colors_json TEXT,
        typography_json TEXT,
        layout_json TEXT,
        components_json TEXT,
        steal_json TEXT,
        css_vars_zlib BLOB,
        tailwind_v4_zlib BLOB
    );
    CREATE VIRTUAL TABLE benchmarks_fts USING fts5(
        id UNINDEXED,
        name,
        title,
        theme,
        tags_zh,
        note_zh,
        component_names,
        tokenize = 'unicode61'
    );

    -- 2. Interactive Components & Content-Addressed Source Blobs
    CREATE TABLE components (
        id TEXT PRIMARY KEY,
        site TEXT NOT NULL,
        name TEXT NOT NULL,
        name_zh TEXT,
        categories TEXT,
        license TEXT NOT NULL,
        redistribution_mode TEXT NOT NULL,
        install_cmd TEXT,
        source_url TEXT,
        preview_url TEXT,
        tags TEXT,
        description TEXT,
        file_count INTEGER DEFAULT 0,
        file_map_json TEXT
    );
    CREATE TABLE component_blobs (
        sha256 TEXT PRIMARY KEY,
        ext TEXT,
        raw_size INTEGER,
        zlib_content BLOB
    );
    CREATE VIRTUAL TABLE components_fts USING fts5(
        id UNINDEXED,
        site,
        name,
        name_zh,
        categories,
        tags,
        description,
        tokenize = 'unicode61'
    );

    -- 3. Motion Prompts, Motion-Lab Cases & Art-Motion Grammars
    CREATE TABLE motion_prompts (
        id TEXT PRIMARY KEY,
        source_pool TEXT NOT NULL,
        title TEXT NOT NULL,
        category TEXT,
        tags_en TEXT,
        tags_zh TEXT,
        aspect_ratio TEXT,
        duration TEXT,
        prompt_en TEXT,
        prompt_zh TEXT,
        meta_json TEXT,
        code_zlib BLOB
    );
    CREATE VIRTUAL TABLE motion_fts USING fts5(
        id UNINDEXED,
        source_pool,
        title,
        category,
        tags_en,
        tags_zh,
        prompt_en,
        prompt_zh,
        tokenize = 'unicode61'
    );

    -- 4. Icons (7 Compliant Libraries: 17,130 Logical Icons & 33,253 Compressed SVGs)
    CREATE TABLE icons (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        library TEXT NOT NULL,
        license TEXT NOT NULL,
        styles_json TEXT,
        categories_json TEXT,
        concepts_json TEXT,
        keywords_zh TEXT
    );
    CREATE TABLE icon_svgs (
        svg_id TEXT PRIMARY KEY,
        icon_id TEXT NOT NULL,
        library TEXT NOT NULL,
        style TEXT NOT NULL,
        name TEXT NOT NULL,
        raw_bytes INTEGER,
        zlib_svg BLOB NOT NULL
    );
    CREATE INDEX idx_icon_svgs_icon_id ON icon_svgs(icon_id);
    CREATE INDEX idx_icon_svgs_lib_name ON icon_svgs(library, name);
    CREATE VIRTUAL TABLE icons_fts USING fts5(
        id UNINDEXED,
        library,
        name,
        categories,
        concepts,
        keywords_zh,
        tokenize = 'unicode61'
    );

    -- 5. WebGL2 / Three.js Single-File Shader Stages & High-Craft Prototypes
    CREATE TABLE webgl_shaders (
        id TEXT PRIMARY KEY,
        slug TEXT NOT NULL,
        title TEXT NOT NULL,
        engine TEXT NOT NULL,
        category TEXT,
        visual_mood TEXT,
        description TEXT,
        raw_lines INTEGER,
        zlib_html BLOB NOT NULL
    );

    -- 6. Brand Design Systems (152 Brand DESIGN.md Systems + 8 Shadcn Presets)
    CREATE TABLE brand_systems (
        id TEXT PRIMARY KEY,
        brand_name TEXT NOT NULL,
        category TEXT,
        summary TEXT,
        colors_preview TEXT,
        fonts_preview TEXT,
        zlib_design_md BLOB NOT NULL
    );
    CREATE VIRTUAL TABLE brand_systems_fts USING fts5(
        id UNINDEXED,
        brand_name,
        category,
        summary,
        colors_preview,
        fonts_preview,
        tokenize = 'unicode61'
    );

    -- 7. Blueprints, Palettes, Font Pairings & Mobile Shells
    CREATE TABLE blueprints_and_palettes (
        id TEXT PRIMARY KEY,
        asset_type TEXT NOT NULL,
        name TEXT NOT NULL,
        tags TEXT,
        summary TEXT,
        spec_json TEXT NOT NULL,
        zlib_template BLOB
    );

    -- 8. Industry Reasoning (192 Industries x 16 WCAG Tokens + 88 UI Styles + 195 UX/Perf Rules + Charts)
    CREATE TABLE industry_reasoning (
        id TEXT PRIMARY KEY,
        record_type TEXT NOT NULL,
        name TEXT NOT NULL,
        keywords TEXT,
        recommended_pattern TEXT,
        style_priority TEXT,
        colors_json TEXT,
        decision_rules_json TEXT,
        anti_patterns TEXT,
        details_json TEXT
    );
    CREATE VIRTUAL TABLE industry_fts USING fts5(
        id UNINDEXED,
        record_type,
        name,
        keywords,
        recommended_pattern,
        style_priority,
        anti_patterns,
        tokenize = 'unicode61'
    );

    -- 9. Cross-Stack Guidelines (22 Tech Stacks x 1,271 Versioned Rules + RN/Shadcn Contracts)
    CREATE TABLE stack_guidelines (
        id TEXT PRIMARY KEY,
        stack TEXT NOT NULL,
        category TEXT,
        guideline TEXT NOT NULL,
        description TEXT,
        do_text TEXT,
        dont_text TEXT,
        code_good TEXT,
        code_bad TEXT,
        severity TEXT,
        applies_to TEXT,
        status TEXT
    );
    CREATE VIRTUAL TABLE stack_fts USING fts5(
        id UNINDEXED,
        stack,
        category,
        guideline,
        description,
        do_text,
        dont_text,
        tokenize = 'unicode61'
    );
    """)
    conn.commit()


def build_benchmarks(conn: sqlite3.Connection) -> dict:
    cur = conn.cursor()
    md_dir = RESOURCE_ROOT / "网站灵感" / "优设美地_设计说明"
    meta_path = md_dir / "metadata.json"
    with open(meta_path, "r", encoding="utf-8") as f:
        meta_list = json.load(f)

    spec_count = 0
    comp_total = 0
    for item in meta_list:
        fn = item["filename"]
        fp = md_dir / fn
        if not fp.exists():
            continue
        md_text = fp.read_text(encoding="utf-8", errors="replace")
        parsed = parse_benchmark_md(md_text)
        comp_total += len(parsed["components"])

        bid = f"ref-{item.get('allan_id', fn.replace('.md', ''))[:12]}"
        name = item.get("name") or fn.replace(".md", "")
        title = item.get("design_md_title") or name
        theme = item.get("theme", "light")
        theme_zh = item.get("theme_zh", "")
        tags_zh = " / ".join(item.get("tags", []))
        note_zh = item.get("note", "")
        comp_names = " ".join(c["name"] for c in parsed["components"])

        cur.execute(
            """INSERT OR REPLACE INTO benchmarks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                bid,
                "youshemeidi-1342",
                name,
                title,
                item.get("source_url", ""),
                theme,
                theme_zh,
                tags_zh,
                note_zh,
                zcomp(json.dumps(parsed["colors"], ensure_ascii=False)),
                zcomp(json.dumps({"fonts": parsed["fonts"], "scale": parsed["type_scale"]}, ensure_ascii=False)),
                zcomp(
                    json.dumps(
                        {
                            "spacing_unit": parsed["spacing_unit"],
                            "density": parsed["density"],
                            "spacing_scale": parsed["spacing_scale"],
                            "radii": parsed["radii"],
                            "shadows": parsed["shadows"],
                            "layout": parsed["layout"],
                        },
                        ensure_ascii=False,
                    )
                ),
                zcomp(json.dumps(parsed["components"], ensure_ascii=False)),
                zcomp("[]"),
                zcomp(parsed["css_vars_code"]) if parsed["css_vars_code"] else None,
                zcomp(parsed["tailwind_v4_code"]) if parsed["tailwind_v4_code"] else None,
            ),
        )
        cur.execute(
            """INSERT INTO benchmarks_fts VALUES (?,?,?,?,?,?,?)""",
            (bid, name, title, f"{theme} {theme_zh}", tags_zh, note_zh, comp_names),
        )
        spec_count += 1

    # Also ingest 202 Award Sites from taste-skill/library/sites.json
    sites_path = (
        RESOURCE_ROOT
        / "精选skill"
        / "taste-skill-main"
        / "taste-skill-main"
        / "skills"
        / "taste-skill"
        / "library"
        / "sites.json"
    )
    award_count = 0
    if sites_path.exists():
        sites_data = json.loads(sites_path.read_text(encoding="utf-8"))
        for s in sites_data:
            sid = f"taste-{s['id']}"
            name = s.get("name", s["id"])
            title = f"{name} ({s.get('archetype', '')})"
            tags = " / ".join(s.get("mood", []) + [s.get("kind", ""), s.get("archetype", "")])
            note = s.get("idea", "")
            steal_str = " ".join(s.get("steal", []))
            cur.execute(
                """INSERT OR REPLACE INTO benchmarks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    sid,
                    "taste-awards-202",
                    name,
                    title,
                    s.get("url", ""),
                    "mixed",
                    "获奖站拆解",
                    tags,
                    note,
                    json.dumps(s.get("colour", {}), ensure_ascii=False),
                    json.dumps(s.get("type", {}), ensure_ascii=False),
                    json.dumps({"hero": s.get("hero", {}), "layout": s.get("layout", {})}, ensure_ascii=False),
                    json.dumps(s.get("sections", []), ensure_ascii=False),
                    json.dumps(s.get("steal", []), ensure_ascii=False),
                    None,
                    None,
                ),
            )
            cur.execute(
                """INSERT INTO benchmarks_fts VALUES (?,?,?,?,?,?,?)""",
                (sid, name, title, "award mixed", tags, note, steal_str),
            )
            award_count += 1

    conn.commit()
    return {"specs": spec_count, "awards": award_count, "extracted_components": comp_total}


def build_components(conn: sqlite3.Connection) -> dict:
    cur = conn.cursor()
    comp_root = RESOURCE_ROOT / "交互组件"
    idx_csv = comp_root / "catalog" / "components-index.csv"
    lic_csv = comp_root / "source" / "_licenses.csv"

    with open(idx_csv, "r", encoding="utf-8-sig") as f:
        idx_map = {r["id"]: r for r in csv.DictReader(f)}

    with open(lic_csv, "r", encoding="utf-8-sig") as f:
        lic_rows = list(csv.DictReader(f))

    stats = {
        "full_source_components": 0,
        "metadata_only_components": 0,
        "excluded_restricted": 0,
        "total_files_scanned": 0,
        "unique_blobs": 0,
        "raw_bytes": 0,
        "compressed_bytes": 0,
    }
    seen_blobs = set()

    for lrow in lic_rows:
        cid = lrow["id"]
        site = lrow["site"]
        lic = lrow["license"]
        flags = lrow.get("flags", "")

        # Compliance Filter: Exclude AGPL-3.0, GPL-3.0, GSAP Standard, Unicorn Proprietary
        if (
            site in RESTRICTED_COMPONENT_SITES
            or "AGPL" in lic
            or "GPL" in lic
            or "Standard License" in lic
            or "proprietary" in flags
            or "non-open" in flags
        ):
            stats["excluded_restricted"] += 1
            continue

        meta = idx_map.get(cid, {})
        name = meta.get("name") or lrow.get("name") or cid
        name_zh = meta.get("name_zh") or lrow.get("name") or ""
        categories = meta.get("categories", "")
        install_cmd = meta.get("install", "")
        source_url = meta.get("source_url") or lrow.get("source_url", "")
        preview_url = meta.get("preview_url", "")
        tags = meta.get("tags", "")
        description = meta.get("description", "")

        # Restricted or unspecified redistribution terms: index the upstream link only.
        # StringTune's package license does not license its separately downloaded tutorials.
        if site in {"rareui", "reactbits", "stringtune"} or "no redistribution" in lic.lower() or "commons clause" in lic.lower():
            cur.execute(
                """INSERT OR REPLACE INTO components VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    cid,
                    site,
                    name,
                    name_zh,
                    categories,
                    lic,
                    "metadata_only",
                    install_cmd,
                    source_url,
                    preview_url,
                    tags,
                    description,
                    0,
                    "{}",
                ),
            )
            cur.execute(
                """INSERT INTO components_fts VALUES (?,?,?,?,?,?,?)""",
                (cid, site, name, name_zh, categories, tags, description),
            )
            stats["metadata_only_components"] += 1
            continue

        # Permissive / Free-Redistributable component -> walk source/<site>/<id>
        comp_dir = comp_root / "source" / site / cid
        file_map = {}
        if comp_dir.is_dir():
            for root_d, _, files in os.walk(comp_dir):
                for fn in sorted(files):
                    if fn == "METADATA.json":
                        continue
                    fp = Path(root_d) / fn
                    rel_path = fp.relative_to(comp_dir).as_posix()
                    raw_data = fp.read_bytes()
                    sha = hashlib.sha256(raw_data).hexdigest()
                    file_map[rel_path] = sha
                    stats["total_files_scanned"] += 1
                    stats["raw_bytes"] += len(raw_data)

                    if sha not in seen_blobs:
                        comp_data = zlib.compress(raw_data, 9)
                        ext = fp.suffix.lower()
                        cur.execute(
                            """INSERT OR IGNORE INTO component_blobs VALUES (?,?,?,?)""",
                            (sha, ext, len(raw_data), comp_data),
                        )
                        seen_blobs.add(sha)
                        stats["unique_blobs"] += 1
                        stats["compressed_bytes"] += len(comp_data)

        cur.execute(
            """INSERT OR REPLACE INTO components VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                cid,
                site,
                name,
                name_zh,
                categories,
                lic,
                "full_source",
                install_cmd,
                source_url,
                preview_url,
                tags,
                description,
                len(file_map),
                json.dumps(file_map, ensure_ascii=False),
            ),
        )
        cur.execute(
            """INSERT INTO components_fts VALUES (?,?,?,?,?,?,?)""",
            (cid, site, name, name_zh, categories, tags, description),
        )
        stats["full_source_components"] += 1

    conn.commit()
    return stats


def build_motions(conn: sqlite3.Connection) -> dict:
    cur = conn.cursor()
    mp_path = RESOURCE_ROOT / "精美动画" / "allan-motion-prompts" / "motion-prompts.json"
    raw_mp = json.loads(mp_path.read_text(encoding="utf-8"))
    items = raw_mp.get("items", []) if isinstance(raw_mp, dict) else raw_mp

    allan_count = 0
    for it in items:
        mid = f"allan-{it.get('num') or it.get('id')}"
        title = it.get("title") or f"Motion #{it.get('num')}"
        raw_tags = it.get("tags", [])
        norm_en = []
        norm_zh = []
        for t in raw_tags:
            if t in MOTION_ZH_TAG_MAP:
                norm_zh.append(t)
                norm_en.append(MOTION_ZH_TAG_MAP[t])
            else:
                norm_en.append(t)
        tags_en_str = " / ".join(dict.fromkeys(norm_en))
        tags_zh_str = " / ".join(dict.fromkeys(norm_zh))
        prompt_main = it.get("prompt") or ""
        prompt_alt = it.get("promptAlt") or ""
        # Determine language of prompt vs promptAlt
        if re.search(r"[\u4e00-\u9fff]", prompt_main) and not re.search(r"[\u4e00-\u9fff]", prompt_alt):
            prompt_zh, prompt_en = prompt_main, prompt_alt
        else:
            prompt_en, prompt_zh = prompt_main, prompt_alt

        meta = {
            "author": it.get("author", ""),
            "model": it.get("model", ""),
            "sourceUrl": it.get("sourceUrl", ""),
            "videoUrl": it.get("videoUrl", ""),
        }
        cur.execute(
            """INSERT OR REPLACE INTO motion_prompts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                mid,
                "allan-motion-233",
                title,
                norm_en[0] if norm_en else "General",
                tags_en_str,
                tags_zh_str,
                it.get("aspectRatio", "16:9"),
                it.get("duration", ""),
                prompt_en,
                prompt_zh,
                json.dumps(meta, ensure_ascii=False),
                None,
            ),
        )
        cur.execute(
            """INSERT INTO motion_fts VALUES (?,?,?,?,?,?,?,?)""",
            (mid, "allan-motion-233", title, norm_en[0] if norm_en else "General", tags_en_str, tags_zh_str, prompt_en, prompt_zh),
        )
        allan_count += 1

    # Ingest Taste motions.json (18) + Pro-Max motion.csv (17)
    taste_mp = (
        RESOURCE_ROOT
        / "精选skill"
        / "taste-skill-main"
        / "taste-skill-main"
        / "skills"
        / "taste-skill"
        / "library"
        / "motions.json"
    )
    recipe_count = 0
    if taste_mp.exists():
        for m in json.loads(taste_mp.read_text(encoding="utf-8")):
            mid = f"taste-motion-{m['id']}"
            cur.execute(
                """INSERT OR REPLACE INTO motion_prompts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    mid,
                    "taste-recipes",
                    m.get("name", m["id"]),
                    "UI Motion Recipe",
                    m["id"],
                    "",
                    "",
                    "",
                    m.get("description", ""),
                    "",
                    "{}",
                    None,
                ),
            )
            cur.execute(
                """INSERT INTO motion_fts VALUES (?,?,?,?,?,?,?,?)""",
                (mid, "taste-recipes", m.get("name", m["id"]), "UI Motion Recipe", m["id"], "", m.get("description", ""), ""),
            )
            recipe_count += 1

    promax_mp = RESOURCE_ROOT / "精选skill" / "ui-ux-pro-max-skill" / "data" / "motion.csv"
    if promax_mp.exists():
        with open(promax_mp, "r", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                mid = f"promax-motion-{r['No']}"
                title = f"{r['Category']} ({r['Intensity Tier']})"
                dont_val = r.get("Don't", "")
                desc = f"Trigger: {r['Trigger']} | Duration: {r['Duration']} | Easing: {r['Easing']} | Do: {r['Do']} | Don't: {dont_val}"
                cur.execute(
                    """INSERT OR REPLACE INTO motion_prompts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        mid,
                        "promax-gsap-17",
                        title,
                        r["Category"],
                        r["Keywords"],
                        "",
                        "",
                        r["Duration"],
                        desc,
                        "",
                        json.dumps({"easing": r["Easing"], "perf": r["Performance Notes"]}, ensure_ascii=False),
                        zcomp(r.get("GSAP Snippet", "")) if r.get("GSAP Snippet") else None,
                    ),
                )
                cur.execute(
                    """INSERT INTO motion_fts VALUES (?,?,?,?,?,?,?,?)""",
                    (mid, "promax-gsap-17", title, r["Category"], r["Keywords"], "", desc, r.get("GSAP Snippet", "")),
                )
                recipe_count += 1

    # Ingest Open-Design motion-lab reference files & huashu-art-motion reference files
    od_skills = RESOURCE_ROOT / "精选skill" / "open-design-main" / "open-design-main" / "skills"
    for sub_skill, pool_tag in [("motion-lab", "open-design-motion-lab"), ("huashu-art-motion", "huashu-art-motion")]:
        ref_dir = od_skills / sub_skill / "references"
        if ref_dir.is_dir():
            for md_fp in sorted(ref_dir.glob("*.md")):
                content = md_fp.read_text(encoding="utf-8", errors="replace")
                # Split by H2 or H3 sections so each pattern is individually searchable
                chunks = re.split(r"(?m)^##\s+", content)
                for idx, ch in enumerate(chunks[1:], 1):
                    lines = ch.splitlines()
                    h_title = lines[0].strip()
                    body = "\n".join(lines[1:]).strip()
                    mid = f"{sub_skill}-{md_fp.stem}-{idx:02d}"
                    cur.execute(
                        """INSERT OR REPLACE INTO motion_prompts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            mid,
                            pool_tag,
                            f"{md_fp.stem}: {h_title}",
                            md_fp.stem,
                            h_title,
                            "",
                            "",
                            "",
                            body[:600],
                            "",
                            json.dumps({"file": md_fp.name}, ensure_ascii=False),
                            zcomp(body),
                        ),
                    )
                    cur.execute(
                        """INSERT INTO motion_fts VALUES (?,?,?,?,?,?,?,?)""",
                        (mid, pool_tag, h_title, md_fp.stem, h_title, "", body[:1000], ""),
                    )
                    recipe_count += 1

    conn.commit()
    return {"allan_prompts": allan_count, "motion_recipes_and_cases": recipe_count}


def build_icons(conn: sqlite3.Connection) -> dict:
    cur = conn.cursor()
    icon_root = RESOURCE_ROOT / "图标资源"
    cat_data = json.loads((icon_root / "catalog.json").read_text(encoding="utf-8"))
    man_data = json.loads((icon_root / "manifest.json").read_text(encoding="utf-8"))

    lib_licenses = {
        "hugeicons": "MIT",
        "tabler": "MIT",
        "phosphor": "MIT",
        "bootstrap": "MIT",
        "iconoir": "MIT",
        "heroicons": "MIT",
        "solar": "CC BY 4.0 (480 Design)",
    }

    logical_count = 0
    for entry in cat_data.get("entries", []):
        fam = entry.get("family", "")
        if fam in RESTRICTED_ICON_LIBRARIES or fam not in lib_licenses:
            continue
        iid = entry["id"]
        name = entry["name"]
        lic = lib_licenses[fam]
        styles = entry.get("styles", [])
        cats = entry.get("categories", [])
        concepts = list((entry.get("concepts") or {}).keys())
        kw_zh = entry.get("keywords", "")

        cur.execute(
            """INSERT OR REPLACE INTO icons VALUES (?,?,?,?,?,?,?,?)""",
            (
                iid,
                name,
                fam,
                lic,
                json.dumps(styles, ensure_ascii=False),
                json.dumps(cats, ensure_ascii=False),
                json.dumps(concepts, ensure_ascii=False),
                kw_zh,
            ),
        )
        cur.execute(
            """INSERT INTO icons_fts VALUES (?,?,?,?,?,?)""",
            (iid, fam, name.replace("-", " "), " ".join(cats), " ".join(concepts), kw_zh),
        )
        logical_count += 1

    svg_count = 0
    svg_raw_bytes = 0
    svg_comp_bytes = 0
    icons_dir = icon_root / "icons"

    for s_item in man_data.get("icons", []):
        fam = s_item.get("family", "")
        if fam in RESTRICTED_ICON_LIBRARIES or fam not in lib_licenses:
            continue
        rel_file = s_item["file"]
        svg_fp = icons_dir / rel_file
        if not svg_fp.exists():
            continue
        raw_svg = svg_fp.read_bytes()
        comp_svg = zlib.compress(raw_svg, 9)
        style = s_item.get("style", "default")
        name = s_item.get("name", "")
        icon_id = f"{fam}:{name}"
        svg_id = f"{fam}:{style}:{name}"

        cur.execute(
            """INSERT OR REPLACE INTO icon_svgs VALUES (?,?,?,?,?,?,?)""",
            (svg_id, icon_id, fam, style, name, len(raw_svg), comp_svg),
        )
        svg_count += 1
        svg_raw_bytes += len(raw_svg)
        svg_comp_bytes += len(comp_svg)

    conn.commit()
    return {
        "logical_icons": logical_count,
        "svg_files": svg_count,
        "svg_raw_mb": round(svg_raw_bytes / (1024 * 1024), 2),
        "svg_comp_mb": round(svg_comp_bytes / (1024 * 1024), 2),
    }


def build_shaders_and_systems(conn: sqlite3.Connection) -> dict:
    cur = conn.cursor()
    od_root = RESOURCE_ROOT / "精选skill" / "open-design-main" / "open-design-main"

    # 1. WebGL2 / Three.js single-file shader stages
    shader_count = 0
    for html_fp in sorted((od_root / "plugins" / "_official" / "examples").glob("webgl-*/example.html")):
        slug = html_fp.parent.name
        skill_fp = html_fp.parent / "SKILL.md"
        desc = ""
        title = slug.replace("webgl-", "").replace("-", " ").title()
        if skill_fp.exists():
            stxt = skill_fp.read_text(encoding="utf-8", errors="replace")
            m_desc = re.search(r"description:\s*([^\n]+)", stxt)
            if m_desc:
                desc = m_desc.group(1).strip().strip('"\'')
        html_txt = html_fp.read_text(encoding="utf-8", errors="replace")
        engine = "threejs-webgl" if "three" in html_txt.lower() else "webgl2-glsl-fullscreen"
        cur.execute(
            """INSERT OR REPLACE INTO webgl_shaders VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                slug,
                slug,
                title,
                engine,
                "Hero / Stage Shader",
                desc[:160],
                desc,
                len(html_txt.splitlines()),
                zcomp(html_txt),
            ),
        )
        shader_count += 1

    # Also add VFX Text Cursor & 3 Taste Trilogy full HTML templates into webgl_shaders / prototypes
    vfx_fp = od_root / "plugins" / "_official" / "video-templates" / "vfx-text-cursor" / "source" / "index.html"
    if vfx_fp.exists():
        html_txt = vfx_fp.read_text(encoding="utf-8", errors="replace")
        cur.execute(
            """INSERT OR REPLACE INTO webgl_shaders VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                "webgl-vfx-text-cursor",
                "webgl-vfx-text-cursor",
                "VFX Chromatic Aberration Glow Text Cursor",
                "webgl-canvas",
                "Interactive Cursor / Typography VFX",
                "Chromatic aberration + glow trail cursor interaction",
                "Single-file interactive VFX text cursor template",
                len(html_txt.splitlines()),
                zcomp(html_txt),
            ),
        )
        shader_count += 1

    # 2. Brand Design Systems (152 DESIGN.md files)
    brand_count = 0
    seen_brands = set()
    for sys_dir in [od_root / "design-systems", od_root / "plugins" / "_official" / "design-systems"]:
        if not sys_dir.is_dir():
            continue
        for dmd_fp in sorted(sys_dir.glob("*/DESIGN.md")):
            slug = dmd_fp.parent.name
            if slug in seen_brands:
                continue
            seen_brands.add(slug)
            txt = dmd_fp.read_text(encoding="utf-8", errors="replace")
            m_h1 = re.search(r"(?m)^#\s+(.+)$", txt)
            bname = m_h1.group(1).strip() if m_h1 else slug.replace("-", " ").title()
            hexes = list(dict.fromkeys(re.findall(r"#[0-9a-fA-F]{6}\b", txt)))[:10]
            fonts = list(dict.fromkeys(re.findall(r"(?:Font|Family|Typeface)[^:\n]*:\s*([^\n|]+)", txt, flags=re.I)))[:5]
            summary = " ".join(line.strip() for line in txt.splitlines()[1:10] if line.strip() and not line.startswith("#"))[:300]

            cur.execute(
                """INSERT OR REPLACE INTO brand_systems VALUES (?,?,?,?,?,?,?)""",
                (
                    f"brand-{slug}",
                    bname,
                    "Brand Design System",
                    summary,
                    " ".join(hexes),
                    " | ".join(f.strip() for f in fonts),
                    zcomp(txt),
                ),
            )
            cur.execute(
                """INSERT INTO brand_systems_fts VALUES (?,?,?,?,?,?)""",
                (f"brand-{slug}", bname, "Brand Design System", summary, " ".join(hexes), " ".join(fonts)),
            )
            brand_count += 1

    conn.commit()
    return {"webgl_shaders": shader_count, "brand_systems": brand_count}


def build_blueprints_and_reasoning(conn: sqlite3.Connection) -> dict:
    cur = conn.cursor()
    taste_lib = (
        RESOURCE_ROOT
        / "精选skill"
        / "taste-skill-main"
        / "taste-skill-main"
        / "skills"
        / "taste-skill"
        / "library"
    )
    bp_count = 0

    for fn, atype in [
        ("directions.json", "direction"),
        ("heroes.json", "hero_blueprint"),
        ("sections.json", "section_blueprint"),
        ("palettes.json", "color_palette"),
        ("type.json", "font_pairing"),
    ]:
        fp = taste_lib / fn
        if fp.exists():
            for item in json.loads(fp.read_text(encoding="utf-8")):
                bid = f"taste-{atype}-{item['id']}"
                name = item.get("name", item["id"])
                tags = " ".join(
                    str(x)
                    for x in (
                        item.get("sectors", [])
                        + item.get("tones", [])
                        + item.get("tags", [])
                        + item.get("directions", [])
                        + [item.get("role", ""), item.get("shape", ""), item.get("archetype", ""), item.get("class", "")]
                    )
                    if x
                )
                summary = item.get("idea") or item.get("blueprint") or item.get("note") or ""
                cur.execute(
                    """INSERT OR REPLACE INTO blueprints_and_palettes VALUES (?,?,?,?,?,?,?)""",
                    (bid, atype, name, tags, str(summary)[:300], json.dumps(item, ensure_ascii=False), None),
                )
                bp_count += 1

    app_fp = taste_lib / "app.json"
    if app_fp.exists():
        app_data = json.loads(app_fp.read_text(encoding="utf-8"))
        for sub_key in ["styles", "shells", "patterns", "kinds"]:
            sub_val = app_data.get(sub_key, {})
            items_iter = (
                [{"id": k, **(v if isinstance(v, dict) else {"value": v})} for k, v in sub_val.items()]
                if isinstance(sub_val, dict)
                else sub_val
            )
            for item in items_iter:
                if not isinstance(item, dict):
                    continue
                bid = f"taste-app-{sub_key}-{item.get('id', item.get('name', ''))}"
                cur.execute(
                    """INSERT OR REPLACE INTO blueprints_and_palettes VALUES (?,?,?,?,?,?,?)""",
                    (
                        bid,
                        f"app_{sub_key[:-1]}",
                        item.get("name", item.get("id", bid)),
                        sub_key,
                        str(item.get("trait") or item.get("layout") or item.get("use") or item.get("description") or "")[:300],
                        json.dumps(item, ensure_ascii=False),
                        None,
                    ),
                )
                bp_count += 1

    # Also store Open-Design iPhone 15 Pro CSS/SVG shell & 3 Taste Trilogy HTML prototypes
    od_tpl = RESOURCE_ROOT / "精选skill" / "open-design-main" / "open-design-main" / "design-templates"
    for slug in ["web-prototype-taste-editorial", "web-prototype-taste-brutalist", "web-prototype-taste-soft"]:
        efp = od_tpl / slug / "example.html"
        if efp.exists():
            cur.execute(
                """INSERT OR REPLACE INTO blueprints_and_palettes VALUES (?,?,?,?,?,?,?)""",
                (
                    f"od-{slug}",
                    "html_prototype",
                    slug.replace("-", " ").title(),
                    "taste trilogy prototype html",
                    f"Complete single-file HTML reference prototype for {slug}",
                    json.dumps({"slug": slug}, ensure_ascii=False),
                    zcomp(efp.read_text(encoding="utf-8", errors="replace")),
                ),
            )
            bp_count += 1

    mob_shell = od_tpl / "mobile-app" / "assets" / "template.html"
    if mob_shell.exists():
        cur.execute(
            """INSERT OR REPLACE INTO blueprints_and_palettes VALUES (?,?,?,?,?,?,?)""",
            (
                "od-iphone15pro-shell",
                "mobile_shell",
                "iPhone 15 Pro Pure CSS/SVG Mockup Shell (390x844)",
                "mobile ios iphone mockup dynamic-island",
                "Zero-external-image pure HTML/CSS/SVG iPhone 15 Pro frame with Dynamic Island and status bar",
                json.dumps({"viewport": "390x844"}, ensure_ascii=False),
                zcomp(mob_shell.read_text(encoding="utf-8", errors="replace")),
            ),
        )
        bp_count += 1

    # Ingest UI-UX-Pro-Max 192 Industries + 88 Styles + 34 Landing + 25 Charts + 195 UX/Perf Guidelines + 22 Tech Stacks
    p_dir = RESOURCE_ROOT / "精选skill" / "ui-ux-pro-max-skill" / "data"
    with open(p_dir / "products.csv", "r", encoding="utf-8-sig") as f:
        prod_map = {r["No"]: r for r in csv.DictReader(f)}
    with open(p_dir / "colors.csv", "r", encoding="utf-8-sig") as f:
        col_map = {r["No"]: r for r in csv.DictReader(f)}
    with open(p_dir / "ui-reasoning.csv", "r", encoding="utf-8-sig") as f:
        reas_map = {r["No"]: r for r in csv.DictReader(f)}

    ind_count = 0
    for no, prod in prod_map.items():
        col = col_map.get(no, {})
        reas = reas_map.get(no, {})
        iid = f"industry-{no}"
        name = prod.get("Product Type") or reas.get("UI_Category") or iid
        kw = prod.get("Keywords", "")
        rec_pat = reas.get("Recommended_Pattern") or prod.get("Landing Page Pattern", "")
        style_prio = reas.get("Style_Priority") or prod.get("Primary Style Recommendation", "")
        anti = reas.get("Anti_Patterns", "")

        cur.execute(
            """INSERT OR REPLACE INTO industry_reasoning VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                iid,
                "industry_archetype",
                name,
                kw,
                rec_pat,
                style_prio,
                json.dumps(col, ensure_ascii=False),
                reas.get("Decision_Rules", "{}"),
                anti,
                json.dumps({"product": prod, "reasoning": reas}, ensure_ascii=False),
            ),
        )
        cur.execute(
            """INSERT INTO industry_fts VALUES (?,?,?,?,?,?,?)""",
            (iid, "industry_archetype", name, kw, rec_pat, style_prio, anti),
        )
        ind_count += 1

    # Add 88 UI styles, 34 Landing patterns, 25 Chart rules, 74 Font pairings
    for csv_fn, rtype, name_col, kw_col in [
        ("styles.csv", "ui_style", "Style Category", "Keywords"),
        ("landing.csv", "landing_pattern", "Pattern Name", "Keywords"),
        ("charts.csv", "chart_guideline", "Data Type", "Keywords"),
        ("typography.csv", "font_pairing_pro", "Font Pairing Name", "Mood/Style Keywords"),
    ]:
        with open(p_dir / csv_fn, "r", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                rid = f"{rtype}-{r['No']}"
                rname = r.get(name_col, rid)
                rkw = r.get(kw_col, "")
                cur.execute(
                    """INSERT OR REPLACE INTO industry_reasoning VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (
                        rid,
                        rtype,
                        rname,
                        rkw,
                        r.get("Best Chart Type") or r.get("Section Order") or r.get("Heading Font", ""),
                        r.get("Type") or r.get("Category", ""),
                        json.dumps({"primary": r.get("Primary Colors", ""), "secondary": r.get("Secondary Colors", "")}, ensure_ascii=False),
                        "{}",
                        r.get("Do Not Use For") or r.get("When NOT to Use", ""),
                        json.dumps(r, ensure_ascii=False),
                    ),
                )
                cur.execute(
                    """INSERT INTO industry_fts VALUES (?,?,?,?,?,?,?)""",
                    (rid, rtype, rname, rkw, "", "", ""),
                )
                ind_count += 1

    # Ingest 22 Tech Stack CSVs + UX/App/React-Performance CSVs into stack_guidelines
    stack_count = 0
    for extra_csv, stack_label in [
        ("ux-guidelines.csv", "general-ux"),
        ("app-interface.csv", "mobile-app-interface"),
        ("react-performance.csv", "react-performance"),
    ]:
        with open(p_dir / extra_csv, "r", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                sid = f"{stack_label}-{r['No']}"
                cur.execute(
                    """INSERT OR REPLACE INTO stack_guidelines VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        sid,
                        stack_label,
                        r.get("Category", ""),
                        r.get("Issue", ""),
                        r.get("Description", ""),
                        r.get("Do", ""),
                        r.get("Don't", ""),
                        r.get("Code Example Good", ""),
                        r.get("Code Example Bad", ""),
                        r.get("Severity", "Medium"),
                        r.get("Platform", "all"),
                        "current",
                    ),
                )
                cur.execute(
                    """INSERT INTO stack_fts VALUES (?,?,?,?,?,?,?)""",
                    (sid, stack_label, r.get("Category", ""), r.get("Issue", ""), r.get("Description", ""), r.get("Do", ""), r.get("Don't", "")),
                )
                stack_count += 1

    for stack_fp in sorted((p_dir / "stacks").glob("*.csv")):
        stack_name = stack_fp.stem
        with open(stack_fp, "r", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r.get("Status", "current").lower() == "deprecated":
                    continue
                sid = f"stack-{stack_name}-{r['No']}"
                cur.execute(
                    """INSERT OR REPLACE INTO stack_guidelines VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        sid,
                        stack_name,
                        r.get("Category", ""),
                        r.get("Guideline", ""),
                        r.get("Description", ""),
                        r.get("Do", ""),
                        r.get("Don't", ""),
                        r.get("Code Good", ""),
                        r.get("Code Bad", ""),
                        r.get("Severity", "Medium"),
                        r.get("Applies To", ""),
                        r.get("Status", "current"),
                    ),
                )
                cur.execute(
                    """INSERT INTO stack_fts VALUES (?,?,?,?,?,?,?)""",
                    (sid, stack_name, r.get("Category", ""), r.get("Guideline", ""), r.get("Description", ""), r.get("Do", ""), r.get("Don't", "")),
                )
                stack_count += 1

    conn.commit()
    return {"blueprints_and_palettes": bp_count, "industry_records": ind_count, "stack_guidelines": stack_count}


def write_third_party_notices(stats: dict):
    content = """# Third-party notices

Original Light-UI-UX code and documentation are licensed under MIT. Third-party resources retain their own copyright and license terms; inclusion in the local database does not relicense them.

## Components

The component index contains 1,140 entries: 876 with bundled source and 264 with metadata and an upstream link only. Bundled components retain license files inside their source maps where available. Additional full license texts are in [licenses/components](licenses/components).

| Source | Bundled entries | License text |
| --- | ---: | --- |
| BundUI | 213 | [MIT](licenses/components/bundui.txt) |
| Animation Micro-Interactions | 176 | [MIT](licenses/components/amicro.txt) |
| Animata | 154 | [MIT](licenses/components/animata.txt) |
| Cult UI | 137 | [MIT](licenses/components/cult-ui.txt) |
| GSAP CodePen examples | 61 | [Example license](licenses/components/gsap.txt) |
| Bencho | 49 | [MIT](licenses/components/bencho.txt) |
| Open UI libraries | 49 | [MIT and dependency notices](licenses/components/libraries.txt) |
| Beautiful UI | 21 | [MIT](licenses/components/beautifului.txt) |
| Orb / shader components | 13 | [MIT](licenses/components/orb.txt) |
| Public CodePen examples | 2 | [Example license](licenses/components/codepen.txt) |
| Liquid Glass | 1 | [MIT](licenses/components/liquid-glass.txt) |

Reference-only entries do not bundle component source:

- **React Bits (216):** [upstream terms](https://github.com/DavidHDev/react-bits/blob/main/LICENSE.md) restrict redistribution of the components themselves. The index retains names, search metadata, and official source URLs.
- **RareUI (25):** indexed by metadata and upstream URL; component redistribution is not included.
- **StringTune tutorials (23):** the package's MIT license does not establish a separate license for downloaded tutorial pages, so those pages are linked rather than bundled.

The database excludes AGPL/GPL components, GSAP Standard License example bundles, proprietary Unicorn Studio embeds, and Nucleo UI SVGs. Code examples can still require separately installed libraries, fonts, or media under their own terms. A CodePen example's license does not relicense GSAP itself.

## Icons

The database contains 17,130 logical icon entries and 33,253 SVG variants. Full license texts:

| Library | License |
| --- | --- |
| Tabler Icons — Paweł Kuna | [MIT](licenses/icons/tabler.txt) |
| Hugeicons Free | [MIT](licenses/icons/hugeicons.txt) |
| Phosphor Icons | [MIT](licenses/icons/phosphor.txt) |
| Bootstrap Icons — The Bootstrap Authors | [MIT](licenses/icons/bootstrap.txt) |
| Iconoir — Luca Burgio | [MIT](licenses/icons/iconoir.txt) |
| Heroicons — Tailwind Labs | [MIT](licenses/icons/heroicons.txt) |
| Solar — 480 Design | [CC BY 4.0](licenses/icons/solar.txt) |

Solar attribution: [480 Design](https://www.figma.com/@480design), [original collection](https://www.figma.com/community/file/1166831539721848736), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The archived SVGs normalize IDs and make ink colors configurable; vector geometry is retained. Preserve this attribution when redistributing Solar icons.

## Design datasets and references

| Source | Included material | License |
| --- | --- | --- |
| Impeccable | Design guidance | [Apache-2.0](licenses/methods/impeccable-LICENSE), [notice](licenses/methods/impeccable-NOTICE.md) |
| Open-Design | Shader templates, brand systems, motion and layout references | [Apache-2.0](licenses/methods/open-design-LICENSE) |
| Taste-Skill | Blueprints, palettes, font pairings, motion recipes | [MIT](licenses/methods/taste-skill-LICENSE) |
| UI/UX Pro Max | Industry mappings and stack guidance | [MIT](licenses/methods/ui-ux-pro-max-LICENSE) |
| GSAP Skills | Motion guidance | [MIT](licenses/methods/gsap-skills-LICENSE) |
| AI Design Skills | Design workflow references | [MIT](licenses/methods/ai-design-skills-LICENSE) |
| IP-as-Logo | Brand design methodology | [MIT](licenses/methods/ip-as-logo-LICENSE) |

Additional methodology references include Interface Details, Emil Kowalski's design engineering guidance, Apple fluid interfaces, mobile app design guidance, and shadcn/ui. Website benchmark records retain source URLs and structured measurements such as colors, type scales, spacing, and radii; these references do not imply affiliation or endorsement.

## Showcase

RIFT, NOCT, Meltday, and Veylo are fictional demonstration projects built with Light-UI-UX. Screenshots and original briefs are in [docs](docs); screenshots are examples of output rather than part of the reusable component library. The QR code assets in the README are supplied by the project author and reused from [Light-skills](https://github.com/Light0305/Light-skills).
"""
    NOTICES_PATH.write_text(content, encoding="utf-8")


def main():
    t0 = time.time()
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    resume = "--resume" in sys.argv and DB_PATH.exists()
    if not resume and DB_PATH.exists():
        DB_PATH.unlink()

    print(f"[build_arsenal] Compiling single-file SQLite FTS5 database at: {DB_PATH} (resume={resume})")
    conn = sqlite3.connect(str(DB_PATH))
    if not resume:
        init_schema(conn)

        print("[1/5] Building `benchmarks` (1,342 sanitized website specs + 202 dissected award sites)...")
        s_bench = build_benchmarks(conn)
        print(f"      -> {s_bench}")

        print("[2/5] Building `components` & `component_blobs` (SHA-256 deduplicated + zlib level-9)...")
        s_comp = build_components(conn)
        print(f"      -> {s_comp}")

        print("[3/5] Building `motion_prompts` (233 Allan prompts + Taste/ProMax/Motion-Lab/Huashu cases)...")
        s_mot = build_motions(conn)
        print(f"      -> {s_mot}")

        print("[4/5] Building `icons` & `icon_svgs` (7 compliant libraries, excluding nucleo-ui)...")
        s_icon = build_icons(conn)
        print(f"      -> {s_icon}")
    else:
        cur = conn.cursor()
        s_bench = {"specs": 1342, "awards": 202, "extracted_components": 15045}
        s_comp = {
            "full_source_components": cur.execute("SELECT COUNT(*) FROM components WHERE redistribution_mode='full_source'").fetchone()[0],
            "metadata_only_components": cur.execute("SELECT COUNT(*) FROM components WHERE redistribution_mode='metadata_only'").fetchone()[0],
            "excluded_restricted": 51,
            "unique_blobs": cur.execute("SELECT COUNT(*) FROM component_blobs").fetchone()[0],
        }
        s_mot = {"total_motions": cur.execute("SELECT COUNT(*) FROM motion_prompts").fetchone()[0]}
        s_icon = {"logical_icons": cur.execute("SELECT COUNT(*) FROM icons").fetchone()[0], "svg_files": cur.execute("SELECT COUNT(*) FROM icon_svgs").fetchone()[0]}
        for tbl in ["webgl_shaders", "brand_systems", "brand_systems_fts", "blueprints_and_palettes", "industry_reasoning", "industry_fts", "stack_guidelines", "stack_fts"]:
            cur.execute(f"DELETE FROM {tbl}")
        conn.commit()

    print("[5/5] Building `webgl_shaders`, `brand_systems`, `blueprints_and_palettes`, `industry_reasoning`, `stack_guidelines`...")
    s_shd = build_shaders_and_systems(conn)
    s_bp = build_blueprints_and_reasoning(conn)
    print(f"      -> Shaders & Brands: {s_shd}")
    print(f"      -> Blueprints, Industry & Stacks: {s_bp}")

    print("[VACUUM] Optimizing FTS5 indexes and compacting SQLite database pages...")
    cur = conn.cursor()
    for col in ["colors_json", "typography_json", "layout_json", "components_json", "steal_json"]:
        rows = cur.execute(f"SELECT id, {col} FROM benchmarks").fetchall()
        for bid, val in rows:
            if isinstance(val, str):
                cur.execute(f"UPDATE benchmarks SET {col} = ? WHERE id = ?", (zcomp(val), bid))
    for fts in [
        "benchmarks_fts",
        "components_fts",
        "motion_fts",
        "icons_fts",
        "brand_systems_fts",
        "industry_fts",
        "stack_fts",
    ]:
        cur.execute(f"INSERT INTO {fts}({fts}) VALUES('optimize')")
    conn.commit()
    conn.execute("PRAGMA page_size = 1024;")
    conn.execute("VACUUM;")
    conn.close()

    db_size_mb = round(DB_PATH.stat().st_size / (1024 * 1024), 2)
    all_stats = {
        "db_size_mb": db_size_mb,
        "elapsed_sec": round(time.time() - t0, 2),
        "benchmarks": s_bench,
        "components": s_comp,
        "motions": s_mot,
        "icons": s_icon,
        "shaders_and_brands": s_shd,
        "blueprints_and_stacks": s_bp,
    }
    write_third_party_notices(all_stats)
    print(f"\n[SUCCESS] Built {DB_PATH} ({db_size_mb} MB) and {NOTICES_PATH} in {all_stats['elapsed_sec']}s!")
    print(json.dumps(all_stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
