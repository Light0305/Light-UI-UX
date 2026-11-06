#!/usr/bin/env python3
"""Import inspected BoardUI and LeiBox snapshots into the existing arsenal.

No network access, dependency installation, or upstream code execution occurs.
BoardUI entries include their local import closure and shared theme files.
LeiBox entries without an explicit component license remain reference-only.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sqlite3
import zlib

ROOT = Path(__file__).resolve().parent.parent
BOARD_REVISION = "ec5c5eb3e29c2441be63b9422cd54f411ef23466"
LEIBOX_REVISION = "42a55345cc9f53e6ab926a62527e0bc0ad9db7bc"
FRAMEWORKS = ("react", "vue", "svelte", "solid", "preact", "vanilla")
IMPORT_RE = re.compile(
    r'''\bfrom\s*["']([^"']+)["']|\bimport\s*(?:\(\s*)?["']([^"']+)["']'''
)
ALIASES = {
    "sidebar": "components/application/dashboard/dashboard-sidebar.tsx",
    "direction": "components/foundations/direction/direction.tsx",
    "chevrons": "components/foundations/icons/chevrons.tsx",
    "logo": "components/foundations/brand/logo.tsx",
    "template-copy": "components/foundations/template-copy/template-copy.tsx",
    "agent-runtime": "app/api/chat/route.ts",
}
ZH = {
    "agent-chat": "AI 对话聊天与历史记录", "agent-log": "智能体任务日志",
    "agent-thinking": "AI 思考状态指示器", "app-shell": "应用外壳与移动抽屉",
    "auth-card": "登录注册表单", "composer-loader": "对话输入框加载动效",
    "data-grid": "可编辑电子表格与数据网格", "data-table": "排序筛选分页数据表",
    "important-alerts-card": "重要提醒信息卡", "notification-center": "通知消息中心",
    "orders-chart-card": "订单对比柱状图", "patient-info-card": "用户患者资料卡",
    "revenue-chart-card": "收入对比面积图", "settings-modal": "多页设置弹窗",
    "sidebar": "侧边导航栏", "stat-cards": "指标统计卡", "theme-toggle": "明暗主题切换",
    "announcement": "可关闭公告", "avatar": "头像", "badge": "徽章计数",
    "breadcrumb": "面包屑导航", "button": "按钮", "button-group": "按钮组",
    "carousel": "轮播画廊", "checkbox": "复选框", "checkbox-card": "复选卡片",
    "chip": "状态标签", "close-button": "关闭按钮", "date-picker": "日期选择器",
    "date-range-picker": "日期范围选择器", "divider": "分隔线", "dropdown": "下拉菜单",
    "file-upload": "文件上传拖放进度", "icon-button": "图标按钮", "input": "输入框",
    "input-otp": "验证码输入框", "kbd": "键盘快捷键提示", "link-button": "链接按钮",
    "meeting-scheduler": "会议时间预约", "notification": "通知提示",
    "pagination": "分页导航", "radio": "单选框", "radio-card": "单选卡片",
    "segmented-control": "分段选择控件", "select": "选择下拉框", "slider": "范围滑块",
    "social-button": "社交登录按钮", "status-dot": "状态圆点", "switch": "开关",
    "switch-card": "设置开关卡片", "table": "表格", "tabs": "标签页",
    "textarea": "多行输入框", "tooltip": "悬浮提示", "tree-view": "树形目录文件导航",
    "cx": "语义排版样式合并", "direction": "多语言双向布局 RTL",
    "directional-icon": "方向图标镜像", "scroll-direction": "双向滚动工具",
    "globals": "全局样式与动画", "logo": "品牌标志占位组件",
    "template-copy": "模板多语言文案", "theme": "语义颜色明暗主题变量",
    "typography": "复合字体排版变量", "use-count-up": "数字递增动画",
    "use-dismiss-on-outside-press": "浮层外部点击关闭", "agent-runtime": "流式聊天接口运行时",
    "chevrons": "箭头图标",
}


def dumps(value):
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def safe_name(value):
    path = PurePosixPath(value)
    if not value or "\\" in value or ":" in value or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe source path: {value!r}")
    return path.as_posix()


def local_file(root, relative):
    path = root / safe_name(relative)
    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"Missing or out-of-tree source: {relative}")
    return path


def imports(text):
    return sorted({a or b for a, b in IMPORT_RE.findall(text)})


def resolve_import(root, current, specifier):
    relative = root / specifier[2:] if specifier.startswith("@/") else current.parent / specifier
    candidates = [relative] + [Path(str(relative) + ext) for ext in (".ts", ".tsx", ".js", ".mjs", ".json", ".css")]
    candidates += [relative / ("index" + ext) for ext in (".ts", ".tsx", ".js")]
    for candidate in candidates:
        if candidate.is_file() and candidate.resolve().is_relative_to(root.resolve()):
            return candidate.resolve()
    raise ValueError(f"Unresolved local import {specifier!r} in {current.relative_to(root)}")


def dependency_closure(root, entry):
    pending = [entry, root / "styles/globals.css", root / "styles/theme.css", root / "styles/typography.css"]
    files, external = {}, set()
    while pending:
        path = pending.pop().resolve()
        relative = path.relative_to(root.resolve()).as_posix()
        if relative in files:
            continue
        content = local_file(root, relative).read_text(encoding="utf-8")
        files[relative] = content
        specs = imports(content)
        if path.suffix == ".css":
            specs += re.findall(r'''@import\s+["']([^"']+)["']''', content)
        for specifier in specs:
            if specifier.startswith(("@/", ".")):
                pending.append(resolve_import(root, path, specifier))
            elif not specifier.startswith(("node:", "http:", "https:")):
                parts = specifier.split("/")
                external.add("/".join(parts[:2]) if specifier.startswith("@") else parts[0])
    if any(name.endswith(".tsx") for name in files):
        external.update(("react", "react-dom"))
    return files, external


def board_entries(root):
    root = root.resolve()
    license_text = local_file(root, "LICENSE").read_text(encoding="utf-8")
    if "MIT License" not in license_text or "BoardUI" not in license_text:
        raise ValueError("BoardUI's expected MIT license is missing; inspect the snapshot before importing.")
    package = json.loads(local_file(root, "package.json").read_text(encoding="utf-8"))
    versions = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    readme = local_file(root, "README.md").read_text(encoding="utf-8").split("## BoardUI Pro", 1)[0]
    for line in readme.splitlines():
        match = re.match(r"\| \[([^]]+)\]\(([^)]+)\) \| (.*?) \| `npx boardui@latest add ([\w-]+)` \|", line)
        if not match:
            continue
        name, href, description, slug = match.groups()
        if slug == "rules":
            continue  # Design conventions are routed in the skill, never installed as global agent instructions.
        if slug in ALIASES:
            entry = local_file(root, ALIASES[slug])
        else:
            candidates = [p for folder in ("components", "utils", "hooks", "styles")
                          for p in (root / folder).rglob(slug + ".*") if p.suffix in {".tsx", ".ts", ".css"}]
            if len(candidates) != 1:
                raise ValueError(f"Expected one source entry for BoardUI {slug}, got {candidates}")
            entry = candidates[0]
        files, external = dependency_closure(root, entry)
        missing = external - versions.keys()
        if missing:
            raise ValueError(f"Dependencies without upstream versions in {slug}: {sorted(missing)}")
        entry_path = entry.relative_to(root).as_posix()
        meta = {
            "repository": "https://github.com/BoardUI/boardui", "revision": BOARD_REVISION,
            "entry_files": {"react": [entry_path]}, "local_frameworks": ["react"],
            "documentation_url": href if href.startswith("https://") else f"https://github.com/BoardUI/boardui/blob/{BOARD_REVISION}/{href}",
            "styles": ["styles/globals.css", "styles/theme.css", "styles/typography.css"],
            "integration": "Preserve @/ paths or adapt them together. Merge required dependencies and semantic tokens; do not replace the target package.json or global CSS. Public demo media is not bundled; supply your own assets. The chat runtime needs its own provider configuration.",
        }
        dependencies = {name: versions[name] for name in sorted(external)}
        files["LICENSE.upstream.txt"] = license_text
        files["_LIGHT_UI_SOURCE.json"] = dumps({**meta, "dependencies": dependencies,
            "tooling": {name: versions[name] for name in ("@tailwindcss/postcss", "typescript") if name in versions},
            "runtime": "React 19 / Tailwind CSS 4; Next.js only where imported."}) + "\n"
        yield {
            "id": "boardui-" + slug, "site": "boardui", "name": name,
            "name_zh": ZH.get(slug, name), "categories": entry_path.split("/")[1] if entry_path.startswith("components/") else "foundations",
            "license": "MIT", "redistribution_mode": "full_source",
            "install_cmd": f"npx boardui@latest add {slug}",
            "source_url": f"https://github.com/BoardUI/boardui/blob/{BOARD_REVISION}/{entry_path}",
            "preview_url": meta["documentation_url"], "tags": "react nextjs tailwind v4 react-aria boardui " + slug.replace("-", " ") + " " + ZH.get(slug, ""),
            "description": description, "frameworks": "react", "dependencies": dependencies,
            "source_meta": meta, "files": files,
        }


def leibox_entries(root):
    catalog = json.loads(local_file(root, "public/ai/catalog.json").read_text(encoding="utf-8-sig"))
    for item in catalog["items"]:
        slug, discovery = item["slug"], item.get("discovery", {})
        source = item.get("source", {})
        frameworks = [name for name in item.get("frameworks", []) if name in FRAMEWORKS]
        meta = {
            "repository": "https://github.com/leishifu666/LeiBox", "catalog_revision": LEIBOX_REVISION,
            "catalog_url": f"https://github.com/leishifu666/LeiBox/blob/{LEIBOX_REVISION}/public/ai/catalog.json",
            "upstream_source": source, "distribution": item.get("distribution", {}),
            "caveat": discovery.get("caveat", ""), "local_frameworks": [],
            "detail_url": "https://leibox.pantoria.cn" + item["detailPath"],
            "packages": {name: "https://leibox.pantoria.cn/ai/packages/" + slug + "/" + name + ".json" for name in frameworks},
        }
        files, dependencies = {}, {}
        # The inspected ASCII Sharks component has an explicit MIT attribution.
        # The site's canRedistributeSource flag alone is not a blanket license.
        licensed = slug == "ascii-sharks" and source.get("license", "").startswith("MIT License, Copyright (c) 2026 drewdi;")
        if licensed:
            entries, package_hashes = {}, {}
            for framework in frameworks:
                package_file = local_file(root, f"public/ai/packages/{slug}/{framework}.json")
                raw = package_file.read_bytes()
                package = json.loads(raw)
                if package["slug"] != slug or package["framework"] != framework:
                    raise ValueError(f"Wrong LeiBox package: {slug}/{framework}")
                package_hashes[framework] = hashlib.sha256(raw).hexdigest()
                dependencies[framework] = package.get("dependencies", [])
                entries[framework] = []
                for file in package["files"]:
                    relative, content = safe_name(file["path"]), file["content"]
                    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
                    if not file.get("sha256") or digest != file["sha256"]:
                        raise ValueError(f"LeiBox file hash mismatch: {framework}/{relative}")
                    files[framework + "/" + relative] = content
                    if "Engine" not in relative and "motion-runtime" not in relative:
                        entries[framework].append(framework + "/" + relative)
                files[framework + "/_PACKAGE.json"] = dumps({k: v for k, v in package.items() if k != "files"}) + "\n"
                engine = next((f["content"] for f in package["files"] if f["path"].endswith("Engine.js")), "")
                if "Copyright (c) 2026 drewdi" not in engine or "MIT License" not in engine:
                    raise ValueError("ASCII Sharks engine is missing its promised MIT notice.")
            meta.update(local_frameworks=frameworks, entry_files=entries, package_sha256=package_hashes,
                        package_revision="Live site packages verified by embedded SHA-256; catalog revision does not pin package generation.")
            files["_LIGHT_UI_SOURCE.json"] = dumps({**meta, "dependencies": dependencies}) + "\n"
        tags = [item.get("keywords", ""), *frameworks, *discovery.get("searchTerms", []),
                *discovery.get("visualTags", []), *discovery.get("interactions", []), *item.get("renderers", [])]
        yield {
            "id": "leibox-" + slug, "site": "leibox", "name": item["name"]["en"],
            "name_zh": item["name"].get("zh", ""), "categories": discovery.get("category", "interaction"),
            "license": "MIT; embedded font/icon notices" if licensed else "Source-specific; redistribution unverified",
            "redistribution_mode": "full_source" if files else "metadata_only", "install_cmd": "",
            "source_url": "https://leibox.pantoria.cn" + item["docsPath"],
            "preview_url": "https://leibox.pantoria.cn" + item["docsPath"],
            "tags": " ".join(tags), "description": item["description"].get("zh", "") + " " + item["description"]["en"] + " " + discovery.get("caveat", ""),
            "frameworks": ",".join(frameworks), "dependencies": dependencies, "source_meta": meta, "files": files,
        }


def import_entries(db, entries):
    entries = list(entries)  # Validate all sources before opening the write transaction.
    if not entries or len({entry["id"] for entry in entries}) != len(entries):
        raise ValueError("Empty import or duplicate component IDs.")
    conn = sqlite3.connect(db)
    try:
        conn.execute("BEGIN IMMEDIATE")
        columns = {row[1] for row in conn.execute("PRAGMA table_info(components)")}
        if "id" not in columns:
            raise ValueError("The destination must be an existing Light-UI-UX arsenal.")
        for name in ("frameworks", "dependencies_json", "source_meta_json"):
            if name not in columns:
                conn.execute(f"ALTER TABLE components ADD COLUMN {name} TEXT NOT NULL DEFAULT ''")
        for site in sorted({entry["site"] for entry in entries}):
            conn.execute("DELETE FROM components_fts WHERE site = ?", (site,))
            conn.execute("DELETE FROM components WHERE site = ?", (site,))
        for entry in entries:
            file_map = {}
            for relative, content in sorted(entry["files"].items()):
                relative = safe_name(relative)
                raw = content.encode("utf-8")
                digest = hashlib.sha256(raw).hexdigest()
                conn.execute("INSERT OR IGNORE INTO component_blobs VALUES (?,?,?,?)",
                             (digest, Path(relative).suffix, len(raw), zlib.compress(raw, 9)))
                file_map[relative] = digest
            fields = ("id", "site", "name", "name_zh", "categories", "license", "redistribution_mode",
                      "install_cmd", "source_url", "preview_url", "tags", "description")
            conn.execute("INSERT INTO components (" + ",".join(fields) +
                         ",file_count,file_map_json,frameworks,dependencies_json,source_meta_json) VALUES (" + ",".join("?" for _ in range(17)) + ")",
                         [entry[key] for key in fields] + [len(file_map), dumps(file_map), entry["frameworks"], dumps(entry["dependencies"]), dumps(entry["source_meta"])])
            conn.execute("INSERT INTO components_fts VALUES (?,?,?,?,?,?,?)",
                         [entry[key] for key in ("id", "site", "name", "name_zh", "categories", "tags", "description")])
        conn.execute("INSERT INTO components_fts(components_fts) VALUES('optimize')")
        conn.commit()
        summary = {site: {"entries": sum(e["site"] == site for e in entries),
                          "full_source": sum(e["site"] == site and bool(e["files"]) for e in entries)}
                   for site in sorted({e["site"] for e in entries})}
        summary["total_components"] = conn.execute("SELECT count(*) FROM components").fetchone()[0]
        summary["total_full_source"] = conn.execute("SELECT count(*) FROM components WHERE redistribution_mode='full_source'").fetchone()[0]
        return summary
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boardui", type=Path, help="BoardUI checkout at the inspected revision")
    parser.add_argument("--leibox", type=Path, help="LeiBox catalog plus six inspected ASCII Sharks packages")
    parser.add_argument("--db", type=Path, default=ROOT / "assets/light-arsenal.db")
    args = parser.parse_args()
    if not args.boardui and not args.leibox:
        parser.error("Provide --boardui and/or --leibox; paths are local, already-inspected snapshots.")
    if not args.db.is_file():
        parser.error("The arsenal database must already exist.")
    entries = []
    if args.boardui:
        entries.extend(board_entries(args.boardui))
    if args.leibox:
        entries.extend(leibox_entries(args.leibox))
    result = import_entries(args.db, entries)
    if args.db.resolve() == (ROOT / "assets/light-arsenal.db").resolve():
        from build_arsenal import write_third_party_notices
        conn = sqlite3.connect(args.db)
        try:
            sources = [dict(zip(("site", "entries", "full_source"), row)) for row in conn.execute(
                "SELECT site, count(*), sum(redistribution_mode='full_source') FROM components GROUP BY site ORDER BY site"
            )]
        finally:
            conn.close()
        licenses = ROOT / "licenses/components"
        if args.boardui:
            (licenses / "boardui.txt").write_bytes(local_file(args.boardui, "LICENSE").read_bytes())
        if args.leibox:
            for name in ("LICENSE", "COPYRIGHT"):
                (licenses / f"leibox-{name}.md").write_bytes(local_file(args.leibox, name + ".md").read_bytes())
        write_third_party_notices({"component_sources": sources})
    print(dumps(result))


if __name__ == "__main__":
    main()
